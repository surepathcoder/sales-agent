"""Interaction endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.schemas.interaction import ApproveOutreachRequest, InteractionResponse, ReplyRequest
from app.services.interaction_service import InteractionService

router = APIRouter()


@router.get("", response_model=list[InteractionResponse])
async def list_all_interactions(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[InteractionResponse]:
    svc = InteractionService(db, tenant_id)
    return [InteractionResponse.model_validate(i) for i in await svc.list_all()]


@router.get("/lead/{lead_id}", response_model=list[InteractionResponse])
async def list_lead_interactions(
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[InteractionResponse]:
    svc = InteractionService(db, tenant_id)
    return [InteractionResponse.model_validate(i) for i in await svc.list_by_lead(lead_id)]


@router.get("/pending", response_model=list[InteractionResponse])
async def list_pending_outreach(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[InteractionResponse]:
    svc = InteractionService(db, tenant_id)
    return [InteractionResponse.model_validate(i) for i in await svc.list_pending_approval()]


@router.post("/{interaction_id}/reply", response_model=InteractionResponse)
async def reply_to_interaction(
    interaction_id: uuid.UUID,
    data: ReplyRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    from datetime import datetime, timezone

    from app.integrations.groq_client import GroqClient
    from app.models.enums import InteractionChannel, InteractionDirection, InteractionInitiator
    from app.models.interaction import Interaction

    svc = InteractionService(db, tenant_id)
    original = await svc.get_interaction(interaction_id)
    if not original:
        raise HTTPException(status_code=404)

    content = data.content
    if data.use_ai_draft:
        groq = GroqClient()
        content = await groq.generate_reply_draft(
            context=original.content,
            tenant_id=str(tenant_id),
        )

    reply = Interaction(
        tenant_id=tenant_id,
        lead_id=original.lead_id,
        contact_id=original.contact_id,
        campaign_id=original.campaign_id,
        channel=InteractionChannel.WHATSAPP,
        direction=InteractionDirection.OUTBOUND,
        initiated_by=InteractionInitiator.HUMAN_USER,
        content=content,
        ai_generated=data.use_ai_draft,
        human_approved=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(reply)
    await db.flush()
    return InteractionResponse.model_validate(reply)


@router.post("/{interaction_id}/approve", response_model=InteractionResponse)
async def approve_outreach(
    interaction_id: uuid.UUID,
    data: ApproveOutreachRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    svc = InteractionService(db, tenant_id)
    if data.send_now:
        interaction = await svc.approve_and_send(interaction_id)
    else:
        interaction = await svc.get_interaction(interaction_id)
        if interaction:
            interaction.human_approved = True
    if not interaction:
        raise HTTPException(status_code=404)
    return InteractionResponse.model_validate(interaction)
