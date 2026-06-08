"""Team user management — tenant-scoped."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.user import User
from app.models.enums import UserRole

router = APIRouter()


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str
    role: str
    nida_verified: bool

    class Config:
        from_attributes = True


class TeamMemberCreate(BaseModel):
    email: str
    phone: str
    password: str
    role: UserRole


@router.get("", response_model=list[TeamMemberResponse])
async def list_team_members(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
    )
    return [TeamMemberResponse.model_validate(u) for u in result.scalars().all()]


@router.post(
    "",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER))],
)
async def create_team_member(
    data: TeamMemberCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    from app.services.auth_service import AuthService
    auth_svc = AuthService(db)

    # Check if email is already registered in the tenant
    existing = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == data.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Mwanachama tayari yupo / User already exists in this tenant")

    user = User(
        tenant_id=tenant_id,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=auth_svc.hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)
    return TeamMemberResponse.model_validate(user)
