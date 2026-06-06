"""Lead model — B2B prospect accounts discovered or imported per tenant."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin, TimestampMixin, default_jsonb
from app.models.enums import (
    pg_enum,
    CompanySize,
    LeadPriority,
    LeadSource,
    LeadStatus,
    NextActionType,
)

if TYPE_CHECKING:
    from app.models.agent_memory import AgentMemory
    from app.models.deal import Deal
    from app.models.interaction import Interaction
    from app.models.lead_contact import LeadContact
    from app.models.tenant import Tenant
    from app.models.user import User


class Lead(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[LeadSource] = mapped_column(
        pg_enum(LeadSource, "lead_source"),
        default=LeadSource.MANUAL,
        nullable=False,
    )
    brela_reg_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    trading_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry_code: Mapped[str] = mapped_column(String(20), default="0000", nullable=False)
    company_size: Mapped[CompanySize] = mapped_column(
        pg_enum(CompanySize, "company_size"),
        default=CompanySize.SMALL,
        nullable=False,
    )
    annual_revenue_estimate: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        pg_enum(LeadStatus, "lead_status"),
        default=LeadStatus.NEW,
        nullable=False,
        index=True,
    )
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[LeadPriority] = mapped_column(
        pg_enum(LeadPriority, "lead_priority"),
        default=LeadPriority.COLD,
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    custom_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, default=default_jsonb, nullable=False)
    ai_insights: Mapped[dict[str, Any]] = mapped_column(JSONB, default=default_jsonb, nullable=False)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_action_type: Mapped[NextActionType | None] = mapped_column(
        pg_enum(NextActionType, "next_action_type"),
        nullable=True,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="leads")
    assigned_user: Mapped["User | None"] = relationship(
        "User", back_populates="assigned_leads", foreign_keys=[assigned_to]
    )
    contacts: Mapped[list["LeadContact"]] = relationship(
        "LeadContact", back_populates="lead", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="lead", cascade="all, delete-orphan"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="lead", cascade="all, delete-orphan"
    )
    agent_memories: Mapped[list["AgentMemory"]] = relationship(
        "AgentMemory", back_populates="lead", cascade="all, delete-orphan"
    )
