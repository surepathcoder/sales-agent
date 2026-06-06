"""Tenant management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.schemas.tenant import TenantResponse, TenantUpdate
from app.services.tenant_service import TenantService

router = APIRouter()


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    svc = TenantService(db, tenant_id)
    tenant = await svc.get_tenant()
    if not tenant:
        raise HTTPException(status_code=404)
    return TenantResponse.model_validate(tenant)


@router.patch("/me", response_model=TenantResponse)
async def update_current_tenant(
    data: TenantUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    svc = TenantService(db, tenant_id)
    tenant = await svc.update_tenant(data)
    if not tenant:
        raise HTTPException(status_code=404)
    return TenantResponse.model_validate(tenant)
