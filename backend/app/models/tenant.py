"""Tenant model — top-level multi-tenant business customer."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, default_jsonb
from app.models.enums import PlanType, TenantStatus, pg_enum

if TYPE_CHECKING:
    from app.models.billing import BillingTransaction
    from app.models.campaign import Campaign
    from app.models.lead import Lead
    from app.models.user import User


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan_type: Mapped[PlanType] = mapped_column(
        pg_enum(PlanType, "plan_type"),
        default=PlanType.FREE,
        nullable=False,
    )
    industry_vertical: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    billing_currency: Mapped[str] = mapped_column(String(3), default="TZS", nullable=False)
    m_pesa_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tigo_pesa_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[TenantStatus] = mapped_column(
        pg_enum(TenantStatus, "tenant_status"),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )
    # locale, timezone, swahili_preference, auto_reply_enabled, wallet_balance
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=default_jsonb, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    campaigns: Mapped[list["Campaign"]] = relationship(
        "Campaign", back_populates="tenant", cascade="all, delete-orphan"
    )
    billing_transactions: Mapped[list["BillingTransaction"]] = relationship(
        "BillingTransaction", back_populates="tenant", cascade="all, delete-orphan"
    )
