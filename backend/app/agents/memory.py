"""Agent memory store with pgvector semantic search."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_memory import AgentMemory
from app.models.enums import AgentType, MemoryType


class AgentMemoryStore:
  def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
    self.db = db
    self.tenant_id = tenant_id

  async def store(
    self,
    agent_type: AgentType,
    content: str,
    memory_type: MemoryType,
    lead_id: uuid.UUID | None = None,
    contact_id: uuid.UUID | None = None,
    confidence: float = 0.8,
    source_interaction_id: uuid.UUID | None = None,
    expiration_days: int | None = None,
    embedding: list[float] | None = None,
  ) -> AgentMemory:
    expiration = None
    if expiration_days:
      expiration = datetime.now(timezone.utc) + __import__("datetime").timedelta(
        days=expiration_days
      )

    memory = AgentMemory(
      tenant_id=self.tenant_id,
      agent_type=agent_type,
      lead_id=lead_id,
      contact_id=contact_id,
      memory_type=memory_type,
      content=content,
      content_vector=embedding,
      confidence_score=Decimal(str(confidence)),
      source_interaction_id=source_interaction_id,
      expiration_date=expiration,
    )
    self.db.add(memory)
    await self.db.flush()
    return memory

  async def retrieve_for_lead(self, lead_id: uuid.UUID) -> list[AgentMemory]:
    now = datetime.now(timezone.utc)
    result = await self.db.execute(
      select(AgentMemory).where(
        AgentMemory.tenant_id == self.tenant_id,
        AgentMemory.lead_id == lead_id,
        (AgentMemory.expiration_date.is_(None)) | (AgentMemory.expiration_date > now),
      )
    )
    return list(result.scalars().all())

  async def semantic_search(
    self, query_embedding: list[float], lead_id: uuid.UUID | None = None, limit: int = 10
  ) -> list[AgentMemory]:
    """Vector similarity search using pgvector cosine distance."""
    q = select(AgentMemory).where(AgentMemory.tenant_id == self.tenant_id)
    if lead_id:
      q = q.where(AgentMemory.lead_id == lead_id)
    q = q.order_by(
      text("content_vector <=> :embedding")
    ).params(embedding=str(query_embedding)).limit(limit)
    result = await self.db.execute(q)
    return list(result.scalars().all())
