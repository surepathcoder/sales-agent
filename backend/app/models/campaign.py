"""Campaign model — outbound sequences and agent-driven outreach programs."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin, TimestampMixin, default_jsonb
from app.models.enums import pg_enum, CampaignStatus, CampaignType

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Campaign(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[CampaignType] = mapped_column(
        pg_enum(CampaignType, "campaign_type"),
        nullable=False,
    )
    status: Mapped[CampaignStatus] = mapped_column(
        pg_enum(CampaignStatus, "campaign_status"),
        default=CampaignStatus.DRAFT,
        nullable=False,
        index=True,
    )
    target_criteria: Mapped[dict[str, Any]] = mapped_column(JSONB, default=default_jsonb, nullable=False)
    lead_pool: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    agent_configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=default_jsonb, nullable=False)
    sequence_steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engaged_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    converted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    budget_allocated: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    spend_to_date: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    roi_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="campaigns")
