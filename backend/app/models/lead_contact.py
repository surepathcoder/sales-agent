"""Lead contact — decision makers and gatekeepers at prospect companies."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin, TimestampMixin
from app.models.enums import (
    pg_enum,
    ContactType,
    Gender,
    InfluenceLevel,
    LanguagePreference,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.lead import Lead


class LeadContact(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "lead_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_type: Mapped[ContactType] = mapped_column(
        pg_enum(ContactType, "contact_type"),
        default=ContactType.MANAGER,
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    gender: Mapped[Gender] = mapped_column(
        pg_enum(Gender, "gender"),
        default=Gender.UNKNOWN,
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(String(512), nullable=True)  # encrypted
    phone: Mapped[str | None] = mapped_column(String(512), nullable=True)  # encrypted
    whatsapp_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    influence_level: Mapped[InfluenceLevel] = mapped_column(
        pg_enum(InfluenceLevel, "influence_level"),
        default=InfluenceLevel.SECONDARY,
        nullable=False,
    )
    language_preference: Mapped[LanguagePreference] = mapped_column(
        pg_enum(LanguagePreference, "contact_language_preference"),
        default=LanguagePreference.BOTH,
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(String(50), default="Africa/Dar_es_Salaam", nullable=False)
    best_contact_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        pg_enum(VerificationStatus, "verification_status"),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="contacts")
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="contact", cascade="all, delete-orphan"
    )
