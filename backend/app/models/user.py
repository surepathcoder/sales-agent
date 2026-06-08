"""User model — tenant-scoped team members with RBAC."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import LanguagePreference, UserRole, pg_enum

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.tenant import Tenant


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"),
        default=UserRole.AGENT,
        nullable=False,
    )
    nida_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nida_number: Mapped[str | None] = mapped_column(String(512), nullable=True)  # encrypted
    language_preference: Mapped[LanguagePreference] = mapped_column(
        pg_enum(LanguagePreference, "language_preference"),
        default=LanguagePreference.BOTH,
        nullable=False,
    )
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    assigned_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="assigned_user", foreign_keys="Lead.assigned_to"
    )
