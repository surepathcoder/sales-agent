"""Inbound webhooks from external services."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.integrations.groq_client import GroqClient
from app.services.interaction_service import InteractionService
from app.services.lead_service import LeadService
from app.utils.phone import normalize_tz_phone

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
    """Receive inbound WhatsApp messages from the sidecar service."""
    try:
        phone = normalize_tz_phone(data.from_number)
    except ValueError:
        phone = data.from_number

    interaction_svc = InteractionService(db, data.tenant_id)
    contact = await interaction_svc.find_contact_by_whatsapp(phone)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found for this number")

    groq = GroqClient()
    classification = await groq.classify(data.message, tenant_id=str(data.tenant_id))

    interaction = await interaction_svc.create_inbound_whatsapp(
        lead_id=contact.lead_id,
        contact_id=contact.id,
        content=data.message,
        metadata={
            "message_id": data.message_id,
            "classification": classification,
        },
    )

    lead_svc = LeadService(db, data.tenant_id)
    lead = await lead_svc.get_lead(contact.lead_id)
    if lead:
        from app.models.enums import LeadStatus

        if lead.status in (LeadStatus.NEW, LeadStatus.CONTACTED):
            lead.status = LeadStatus.ENGAGED

    return {
        "status": "received",
        "interaction_id": str(interaction.id),
        "classification": classification,
    }
