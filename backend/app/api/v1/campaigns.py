"""Campaign endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_current_user_id, get_db, require_roles
from app.models.enums import UserRole
from app.schemas.campaign import CampaignAnalytics, CampaignCreate, CampaignResponse
from app.services.campaign_service import CampaignService

router = APIRouter()


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    svc = CampaignService(db, tenant_id)
    campaigns = await svc.list_campaigns()
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER))],
)
async def create_campaign(
    data: CampaignCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    svc = CampaignService(db, tenant_id)
    try:
        campaign = await svc.create_campaign(data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return CampaignResponse.model_validate(campaign)


@router.post(
    "/{campaign_id}/start",
    response_model=CampaignResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER))],
)
async def start_campaign(
    campaign_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    from app.services.campaign_executor import execute_campaign

    svc = CampaignService(db, tenant_id)
    campaign = await svc.start_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404)

    job_id = str(uuid.uuid4())
    background_tasks.add_task(execute_campaign, job_id, tenant_id, campaign_id)

    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def campaign_analytics(
    campaign_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> CampaignAnalytics:
    svc = CampaignService(db, tenant_id)
    analytics = await svc.get_analytics(campaign_id)
    if not analytics:
        raise HTTPException(status_code=404)
    return analytics
