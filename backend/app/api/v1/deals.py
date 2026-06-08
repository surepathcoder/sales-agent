"""Deal pipeline endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_current_user_id, get_db, require_roles
from app.models.enums import UserRole
from app.schemas.deal import DealCreate, DealResponse, DealUpdate
from app.services.deal_service import DealService

router = APIRouter()


@router.get("", response_model=list[DealResponse])
async def list_deals(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[DealResponse]:
    svc = DealService(db, tenant_id)
    return [DealResponse.model_validate(d) for d in await svc.list_deals()]


@router.post(
    "",
    response_model=DealResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER, UserRole.AGENT))],
)
async def create_deal(
    data: DealCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    svc = DealService(db, tenant_id)
    deal = await svc.create_deal(data, created_by=user_id)
    return DealResponse.model_validate(deal)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    svc = DealService(db, tenant_id)
    deal = await svc.get_deal(deal_id)
    if not deal:
        raise HTTPException(status_code=404)
    return DealResponse.model_validate(deal)


@router.patch(
    "/{deal_id}",
    response_model=DealResponse,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER, UserRole.AGENT))],
)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    svc = DealService(db, tenant_id)
    deal = await svc.update_deal(deal_id, data)
    if not deal:
        raise HTTPException(status_code=404)
    return DealResponse.model_validate(deal)
