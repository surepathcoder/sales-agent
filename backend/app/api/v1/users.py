"""Team user management — tenant-scoped."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.user import User

router = APIRouter()


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str
    role: str
    nida_verified: bool

    class Config:
        from_attributes = True


@router.get("", response_model=list[TeamMemberResponse])
async def list_team_members(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
    )
    return [TeamMemberResponse.model_validate(u) for u in result.scalars().all()]
