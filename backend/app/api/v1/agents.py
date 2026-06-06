"""Agent trigger and memory endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.agent_memory import AgentMemory
from app.models.enums import AgentType

router = APIRouter()


class AgentTriggerRequest(BaseModel):
    lead_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    context: dict[str, Any] = {}


class AgentMemoryResponse(BaseModel):
    id: uuid.UUID
    agent_type: str
    memory_type: str
    content: str
    confidence_score: float

    class Config:
        from_attributes = True


@router.get("/memory/{lead_id}", response_model=list[AgentMemoryResponse])
async def get_agent_memory(
    lead_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[AgentMemoryResponse]:
    result = await db.execute(
        select(AgentMemory).where(
            AgentMemory.tenant_id == tenant_id,
            AgentMemory.lead_id == lead_id,
        )
    )
    return [AgentMemoryResponse.model_validate(m) for m in result.scalars().all()]


@router.get("/job/{job_id}")
async def get_agent_job_status(job_id: str) -> dict:
    """Poll agent job status and live progress events from Redis."""
    from app.services.job_progress import get_job

    data = await get_job(job_id)
    if data:
        return data
    return {"job_id": job_id, "status": "unknown", "events": []}


@router.post("/trigger/{agent_type}")
async def trigger_agent(
    agent_type: AgentType,
    data: AgentTriggerRequest,
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> dict:
    from app.agents.supervisor import trigger_agent_manual

    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        trigger_agent_manual,
        job_id=job_id,
        tenant_id=tenant_id,
        agent_type=agent_type,
        lead_id=data.lead_id,
        campaign_id=data.campaign_id,
        context=data.context,
    )
    return {"job_id": job_id, "agent_type": agent_type.value, "status": "queued"}
