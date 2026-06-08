"""Inbound webhooks from external services."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.integrations.groq_client import GroqClient
from app.services.interaction_service import InteractionService
from app.services.lead_service import LeadService
from app.services.tenant_service import TenantService
from app.utils.phone import normalize_tz_phone
from app.models.enums import LeadStatus, InteractionDirection
from app.agents.tools.whatsapp_tool import send_whatsapp_message

router = APIRouter()


class WhatsAppInboundPayload(BaseModel):
    tenant_id: uuid.UUID
    from_number: str
    message: str
    message_id: str | None = None


@router.post("/whatsapp")
async def whatsapp_inbound(
    data: WhatsAppInboundPayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Receive inbound WhatsApp messages from the sidecar service, analyze with Conversational AI, and auto-reply if enabled."""
    try:
        phone = normalize_tz_phone(data.from_number)
    except ValueError:
        phone = data.from_number

    interaction_svc = InteractionService(db, data.tenant_id)
    contact = await interaction_svc.find_contact_by_whatsapp(phone)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found for this number")

    tenant_svc = TenantService(db, data.tenant_id)
    tenant = await tenant_svc.get_tenant()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    lead_svc = LeadService(db, data.tenant_id)
    lead = await lead_svc.get_lead(contact.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # 1. Fetch conversation history for context
    history_interactions = await interaction_svc.list_by_lead(contact.lead_id)
    history_interactions.reverse()
    history = []
    for i in history_interactions:
        role = "user" if i.direction == InteractionDirection.INBOUND else "assistant"
        history.append({"role": role, "content": i.content})

    # Append current inbound message to the history for analysis
    history.append({"role": "user", "content": data.message})

    # 2. Invoke conversational AI assistant
    groq = GroqClient()
    ai_res = await groq.generate_conversational_reply(
        conversation_history=history,
        tenant_name=tenant.name,
        tenant_industry=tenant.industry_vertical,
        lead_name=contact.first_name,
        lead_research=lead.ai_insights.get("research_report") if lead.ai_insights else None,
        tenant_id=str(data.tenant_id),
    )

    # 3. Save incoming message with intent classification metadata
    interaction = await interaction_svc.create_inbound_whatsapp(
        lead_id=contact.lead_id,
        contact_id=contact.id,
        content=data.message,
        metadata={
            "message_id": data.message_id,
            "classification": {
                "intent": ai_res["intent"],
                "is_qualified": ai_res["is_qualified"],
                "requires_takeover": ai_res["requires_takeover"],
                "reasoning": ai_res["reasoning"],
            },
        },
    )

    # 4. Handle qualification & takeover status updates
    if ai_res["is_qualified"]:
        lead.status = LeadStatus.QUALIFIED
    elif lead.status in (LeadStatus.NEW, LeadStatus.CONTACTED):
        lead.status = LeadStatus.ENGAGED

    if ai_res["requires_takeover"]:
        lead.custom_fields = {
            **(lead.custom_fields or {}),
            "human_takeover": True,
            "takeover_reason": ai_res["reasoning"]
        }

    # 5. Handle automated reply if enabled
    reply_sent = False
    reply_id = None
    auto_reply_enabled = tenant.settings.get("auto_reply_enabled", False)

    if auto_reply_enabled and ai_res["reply"]:
        # Dispatch WhatsApp message via WhatsApp sidecar client
        dispatch_res = await send_whatsapp_message(
            str(data.tenant_id),
            data.from_number,
            ai_res["reply"]
        )
        # Log outbound interaction in database
        outbound = await interaction_svc.create_outreach_interaction(
            lead_id=contact.lead_id,
            contact_id=contact.id,
            content=ai_res["reply"],
            pending_approval=False,
            metadata={
                "auto_reply": True,
                "agent_type": "conversation_agent",
                "delivery_id": dispatch_res.get("delivery_id"),
            }
        )
        reply_sent = True
        reply_id = str(outbound.id)

    return {
        "status": "received",
        "interaction_id": str(interaction.id),
        "classification": {
            "intent": ai_res["intent"],
            "is_qualified": ai_res["is_qualified"],
            "requires_takeover": ai_res["requires_takeover"],
            "reasoning": ai_res["reasoning"],
        },
        "auto_reply": {
            "sent": reply_sent,
            "interaction_id": reply_id,
            "reply_text": ai_res["reply"] if reply_sent else None,
        }
    }
