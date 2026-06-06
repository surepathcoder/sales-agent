"""Deal CRUD — tenant-scoped."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealUpdate


class DealService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def list_deals(self) -> list[Deal]:
        result = await self.db.execute(
            select(Deal)
            .where(Deal.tenant_id == self.tenant_id)
            .order_by(Deal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_deal(self, deal_id: uuid.UUID) -> Deal | None:
        result = await self.db.execute(
            select(Deal).where(Deal.id == deal_id, Deal.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_deal(self, data: DealCreate, created_by: uuid.UUID | None = None) -> Deal:
        close_date = data.expected_close_date or (
            datetime.now(timezone.utc) + timedelta(days=30)
        )
        deal = Deal(
            tenant_id=self.tenant_id,
            lead_id=data.lead_id,
            contact_id=data.contact_id,
            campaign_id=data.campaign_id,
            deal_name=data.deal_name,
            value=data.value,
            currency=data.currency,
            probability=data.probability,
            stage=data.stage,
            expected_close_date=close_date,
            payment_terms=data.payment_terms,
            created_by=created_by,
            owner=created_by,
        )
        self.db.add(deal)
        await self.db.flush()
        await self.db.refresh(deal)
        return deal

    async def update_deal(self, deal_id: uuid.UUID, data: DealUpdate) -> Deal | None:
        deal = await self.get_deal(deal_id)
        if not deal:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(deal, field, value)
        return deal
