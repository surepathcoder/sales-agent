"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agents,
    analytics,
    auth,
    billing,
    campaigns,
    deals,
    integrations,
    interactions,
    leads,
    tenants,
    usage,
    users,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
