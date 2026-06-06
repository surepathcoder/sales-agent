"""User schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import LanguagePreference, PlanType, UserRole
from app.schemas.common import ORMBase
from app.schemas.tenant import TenantResponse


class UserResponse(ORMBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    phone: str
    role: UserRole
    nida_verified: bool
    language_preference: LanguagePreference
    last_active: datetime | None
    created_at: datetime


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: str
    password: str = Field(min_length=8, max_length=128)
    industry_vertical: str = "general"
    plan_type: PlanType = PlanType.FREE


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class NIDAVerifyRequest(BaseModel):
    nida_number: str = Field(min_length=20, max_length=20)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    tenant: TenantResponse
