"""Interaction model — omnichannel communication log with AI metadata."""

import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin
from app.models.enums import (
    pg_enum,
    IntentDetected,
    InteractionChannel,
    InteractionDirection,
    InteractionInitiator,
    LanguagePreference,
    Sentiment,
)

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.lead_contact import LeadContact


class Interaction(Base, TenantScopedMixin):
    __tablename__ = "interactions"

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
        ForeignKey("lead_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[InteractionChannel] = mapped_column(
        pg_enum(InteractionChannel, "interaction_channel"),
        nullable=False,
    )
    direction: Mapped[InteractionDirection] = mapped_column(
        pg_enum(InteractionDirection, "interaction_direction"),
        nullable=False,
    )
    initiated_by: Mapped[InteractionInitiator] = mapped_column(
        pg_enum(InteractionInitiator, "interaction_initiator"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)  # encrypted for WhatsApp/email
    content_vector: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    human_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sentiment: Mapped[Sentiment | None] = mapped_column(
        pg_enum(Sentiment, "sentiment"),
        nullable=True,
    )
    intent_detected: Mapped[IntentDetected | None] = mapped_column(
        pg_enum(IntentDetected, "intent_detected"),
        nullable=True,
    )
    language_used: Mapped[LanguagePreference | None] = mapped_column(
        pg_enum(LanguagePreference, "interaction_language"),
        nullable=True,
    )
    response_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="interactions")
    contact: Mapped["LeadContact"] = relationship("LeadContact", back_populates="interactions")
