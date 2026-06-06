"""Interaction logging and outreach approval."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.whatsapp_tool import send_whatsapp_message
from app.models.enums import (
    InteractionChannel,
    InteractionDirection,
    InteractionInitiator,
)
from app.models.interaction import Interaction
from app.models.lead_contact import LeadContact


class InteractionService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def list_all(self, limit: int = 100) -> list[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .where(Interaction.tenant_id == self.tenant_id)
            .order_by(Interaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_lead(self, lead_id: uuid.UUID) -> list[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .where(Interaction.tenant_id == self.tenant_id, Interaction.lead_id == lead_id)
            .order_by(Interaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_pending_approval(self) -> list[Interaction]:
        result = await self.db.execute(
            select(Interaction).where(
                Interaction.tenant_id == self.tenant_id,
                Interaction.direction == InteractionDirection.OUTBOUND,
                Interaction.human_approved.is_(None),
                Interaction.ai_generated.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_interaction(self, interaction_id: uuid.UUID) -> Interaction | None:
        result = await self.db.execute(
            select(Interaction).where(
                Interaction.id == interaction_id,
                Interaction.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_outreach_interaction(
        self,
        lead_id: uuid.UUID,
        contact_id: uuid.UUID,
        content: str,
        *,
        campaign_id: uuid.UUID | None = None,
        pending_approval: bool = True,
        channel: InteractionChannel = InteractionChannel.WHATSAPP,
        metadata: dict[str, Any] | None = None,
    ) -> Interaction:
        interaction = Interaction(
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            contact_id=contact_id,
            campaign_id=campaign_id,
            channel=channel,
            direction=InteractionDirection.OUTBOUND,
            initiated_by=InteractionInitiator.AI_AGENT,
            content=content,
            ai_generated=True,
            human_approved=None if pending_approval else True,
            extra_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(interaction)
        await self.db.flush()
        await self.db.refresh(interaction)
        return interaction

    async def create_inbound_whatsapp(
        self,
        lead_id: uuid.UUID,
        contact_id: uuid.UUID,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Interaction:
        interaction = Interaction(
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            contact_id=contact_id,
            channel=InteractionChannel.WHATSAPP,
            direction=InteractionDirection.INBOUND,
            initiated_by=InteractionInitiator.HUMAN_CONTACT,
            content=content,
            ai_generated=False,
            extra_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(interaction)
        await self.db.flush()
        await self.db.refresh(interaction)
        return interaction

    async def approve_and_send(self, interaction_id: uuid.UUID) -> Interaction | None:
        interaction = await self.get_interaction(interaction_id)
        if not interaction:
            return None

        contact_result = await self.db.execute(
            select(LeadContact).where(
                LeadContact.id == interaction.contact_id,
                LeadContact.tenant_id == self.tenant_id,
            )
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            return None

        if interaction.channel == InteractionChannel.WHATSAPP:
            await send_whatsapp_message(
                str(self.tenant_id),
                contact.whatsapp_number,
                interaction.content,
            )

        interaction.human_approved = True
        interaction.extra_metadata = {
            **interaction.extra_metadata,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        return interaction

    async def find_contact_by_whatsapp(self, phone: str) -> LeadContact | None:
        result = await self.db.execute(
            select(LeadContact).where(
                LeadContact.tenant_id == self.tenant_id,
                LeadContact.whatsapp_number == phone,
            )
        )
        return result.scalar_one_or_none()
