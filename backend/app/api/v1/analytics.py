"""Analytics dashboard endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.campaign import Campaign
from app.models.deal import Deal
from app.models.enums import CampaignStatus, DealStage, LeadStatus
from app.models.lead import Lead

router = APIRouter()


class DashboardAnalytics(BaseModel):
    total_leads: int
    conversion_rate: float
    avg_deal_value: Decimal
    active_campaigns: int
    lead_sources: dict[str, int]
    pipeline_value: Decimal


@router.get("/dashboard", response_model=DashboardAnalytics)
async def get_dashboard_analytics(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> DashboardAnalytics:
    total_leads = (
        await db.execute(
            select(func.count()).select_from(Lead).where(Lead.tenant_id == tenant_id)
        )
    ).scalar_one()

    won = (
        await db.execute(
            select(func.count())
            .select_from(Lead)
            .where(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.CLOSED_WON)
        )
    ).scalar_one()

    active_campaigns = (
        await db.execute(
            select(func.count())
            .select_from(Campaign)
            .where(Campaign.tenant_id == tenant_id, Campaign.status == CampaignStatus.RUNNING)
        )
    ).scalar_one()

    avg_deal = (
        await db.execute(
            select(func.avg(Deal.value)).where(
                Deal.tenant_id == tenant_id, Deal.stage != DealStage.CLOSED_LOST
            )
        )
    ).scalar_one() or Decimal("0")

    pipeline = (
        await db.execute(
            select(func.sum(Deal.value)).where(
                Deal.tenant_id == tenant_id,
                Deal.stage.notin_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]),
            )
        )
    ).scalar_one() or Decimal("0")

    source_rows = (
        await db.execute(
            select(Lead.source, func.count())
            .where(Lead.tenant_id == tenant_id)
            .group_by(Lead.source)
        )
    ).all()
    lead_sources = {row[0].value if hasattr(row[0], "value") else str(row[0]): row[1] for row in source_rows}

    return DashboardAnalytics(
        total_leads=total_leads,
        conversion_rate=round(won / total_leads * 100, 2) if total_leads else 0.0,
        avg_deal_value=Decimal(str(avg_deal)),
        active_campaigns=active_campaigns,
        lead_sources=lead_sources,
        pipeline_value=Decimal(str(pipeline)),
    )
