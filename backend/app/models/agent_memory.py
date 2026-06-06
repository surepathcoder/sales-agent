"""Agent memory — persistent facts and insights with vector search."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TenantScopedMixin
from app.models.enums import pg_enum, AgentType, MemoryType

if TYPE_CHECKING:
    from app.models.lead import Lead


class AgentMemory(Base, TenantScopedMixin):
    __tablename__ = "agent_memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_type: Mapped[AgentType] = mapped_column(
        pg_enum(AgentType, "agent_type"),
        nullable=False,
        index=True,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_contacts.id", ondelete="CASCADE"),
        nullable=True,
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        pg_enum(MemoryType, "memory_type"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_vector: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.80"), nullable=False)
    source_interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped["Lead | None"] = relationship("Lead", back_populates="agent_memories")
