"""Tenant schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import PlanType, TenantStatus
from app.schemas.common import ORMBase


class TenantSettings(BaseModel):
    locale: str = "sw_TZ"
    timezone: str = "Africa/Dar_es_Salaam"
    swahili_preference: float = Field(default=0.5, ge=0, le=1)
    auto_reply_enabled: bool = True
    wallet_balance: float = 0.0


class TenantResponse(ORMBase):
    id: uuid.UUID
    name: str
    slug: str
    plan_type: PlanType
    industry_vertical: str
    billing_currency: str
    status: TenantStatus
    settings: dict[str, Any]
    created_at: datetime


class TenantUpdate(BaseModel):
    name: str | None = None
    industry_vertical: str | None = None
    settings: dict[str, Any] | None = None
