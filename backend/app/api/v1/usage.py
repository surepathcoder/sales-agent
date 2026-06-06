"""Tenant usage and plan limits."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.services.tenant_service import PLAN_LIMITS, TenantService

router = APIRouter()


class UsageResponse(BaseModel):
    plan_type: str
    leads_used: int
    leads_limit: int
    campaigns_used: int
    campaigns_limit: int
    leads_remaining: int
    campaigns_remaining: int
    onboarding_complete: bool
    whatsapp_connected: bool


@router.get("", response_model=UsageResponse)
async def get_usage(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    tenant_svc = TenantService(db, tenant_id)
    tenant = await tenant_svc.get_tenant()
    plan = tenant.plan_type.value if tenant else "free"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    leads_used = (
        await db.execute(
            select(func.count()).select_from(Lead).where(Lead.tenant_id == tenant_id)
        )
    ).scalar_one()
    campaigns_used = (
        await db.execute(
            select(func.count()).select_from(Campaign).where(Campaign.tenant_id == tenant_id)
        )
    ).scalar_one()

    settings = tenant.settings if tenant else {}
    return UsageResponse(
        plan_type=plan,
        leads_used=leads_used,
        leads_limit=limits["max_leads"],
        campaigns_used=campaigns_used,
        campaigns_limit=limits["max_campaigns"],
        leads_remaining=max(0, limits["max_leads"] - leads_used),
        campaigns_remaining=max(0, limits["max_campaigns"] - campaigns_used),
        onboarding_complete=bool(settings.get("onboarding_complete")),
        whatsapp_connected=settings.get("whatsapp_status") == "connected",
    )
