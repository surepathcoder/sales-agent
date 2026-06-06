"""Tenant management service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.tenant import TenantUpdate

PLAN_LIMITS = {
    "free": {"max_leads": 50, "max_campaigns": 2},
    "starter": {"max_leads": 500, "max_campaigns": 10},
    "growth": {"max_leads": 5000, "max_campaigns": 50},
    "enterprise": {"max_leads": 100000, "max_campaigns": 1000},
}


class TenantService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def get_tenant(self) -> Tenant | None:
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def update_tenant(self, data: TenantUpdate) -> Tenant | None:
        tenant = await self.get_tenant()
        if not tenant:
            return None
        if data.name is not None:
            tenant.name = data.name
        if data.industry_vertical is not None:
            tenant.industry_vertical = data.industry_vertical
        if data.settings is not None:
            tenant.settings = {**tenant.settings, **data.settings}
        return tenant

    def get_plan_limits(self, plan_type: str) -> dict[str, int]:
        return PLAN_LIMITS.get(plan_type, PLAN_LIMITS["free"])
