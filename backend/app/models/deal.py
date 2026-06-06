"""Deal model — pipeline opportunities linked to leads and campaigns."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin, TimestampMixin
from app.models.enums import pg_enum, DealStage, ForecastCategory, PaymentTerms

if TYPE_CHECKING:
    from app.models.lead import Lead


class Deal(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    deal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TZS", nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    stage: Mapped[DealStage] = mapped_column(
        pg_enum(DealStage, "deal_stage"),
        default=DealStage.PROSPECTING,
        nullable=False,
        index=True,
    )
    expected_close_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loss_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    competitor_mentioned: Mapped[str | None] = mapped_column(String(255), nullable=True)
    products_services: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    payment_terms: Mapped[PaymentTerms] = mapped_column(
        pg_enum(PaymentTerms, "payment_terms"),
        default=PaymentTerms.DAYS_30,
        nullable=False,
    )
    commission_earned: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    ai_forecast_category: Mapped[ForecastCategory | None] = mapped_column(
        pg_enum(ForecastCategory, "forecast_category"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    owner: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="deals")
