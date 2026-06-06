"""Campaign management — tenant-scoped."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.schemas.campaign import CampaignAnalytics, CampaignCreate
from app.services.tenant_service import TenantService


class CampaignService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def count_campaigns(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Campaign).where(Campaign.tenant_id == self.tenant_id)
        )
        return result.scalar_one()

    async def check_campaign_limit(self) -> bool:
        tenant_svc = TenantService(self.db, self.tenant_id)
        tenant = await tenant_svc.get_tenant()
        if not tenant:
            return False
        limits = tenant_svc.get_plan_limits(tenant.plan_type.value)
        return await self.count_campaigns() < limits["max_campaigns"]

    async def create_campaign(self, data: CampaignCreate, created_by: uuid.UUID) -> Campaign:
        if not await self.check_campaign_limit():
            raise ValueError("Campaign limit reached / Kikomo cha kampeni kimefikiwa")

        campaign = Campaign(
            tenant_id=self.tenant_id,
            name=data.name,
            campaign_type=data.campaign_type,
            target_criteria=data.target_criteria,
            lead_pool=data.lead_pool,
            agent_configuration=data.agent_configuration,
            sequence_steps=data.sequence_steps,
            total_leads=len(data.lead_pool),
            created_by=created_by,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def list_campaigns(self) -> list[Campaign]:
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.tenant_id == self.tenant_id)
            .order_by(Campaign.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_campaign(self, campaign_id: uuid.UUID) -> Campaign | None:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id, Campaign.tenant_id == self.tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def start_campaign(self, campaign_id: uuid.UUID) -> Campaign | None:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        campaign.status = CampaignStatus.RUNNING
        campaign.start_date = datetime.now(timezone.utc)
        return campaign

    async def get_analytics(self, campaign_id: uuid.UUID) -> CampaignAnalytics | None:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None

        funnel = {
            "total": campaign.total_leads,
            "contacted": campaign.contacted_count,
            "engaged": campaign.engaged_count,
            "qualified": campaign.qualified_count,
            "converted": campaign.converted_count,
        }
        cost_per_lead = (
            campaign.spend_to_date / campaign.contacted_count
            if campaign.contacted_count > 0
            else Decimal("0")
        )
        return CampaignAnalytics(
            funnel=funnel,
            channel_performance={"whatsapp": 0, "email": 0, "sms": 0},
            sentiment_trends=[],
            cost_per_lead=cost_per_lead,
            roi=campaign.roi_estimate,
        )
