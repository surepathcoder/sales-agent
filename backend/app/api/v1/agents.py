"""Agent trigger and memory endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db, require_roles
from app.models.agent_memory import AgentMemory
from app.models.enums import AgentType, UserRole

router = APIRouter()


class AgentTriggerRequest(BaseModel):
    lead_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    context: dict[str, Any] = {}

class DiscoverChatRequest(BaseModel):
    prompt: str


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


@router.post(
    "/trigger/{agent_type}",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER, UserRole.AGENT))],
)
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

@router.post(
    "/discover/chat",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER))],
)
async def discover_chat(
    data: DiscoverChatRequest,
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.agents.supervisor import run_scout_discovery
    from app.integrations.groq_client import GroqClient
    from app.models.tenant import Tenant

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    groq = GroqClient()
    parsed_criteria = await groq.parse_discovery_intent(data.prompt, tenant_id=str(tenant_id))
    
    # Enforce Subscription Tier Limits
    plan = tenant.plan_type.value if hasattr(tenant.plan_type, "value") else str(tenant.plan_type).lower()
    limit_map = {
        "free": 20,
        "growth": 500,
        "agency": 5000
    }
    max_allowed = limit_map.get(plan, 20)
    requested = parsed_criteria.get("max_results", 50)
    
    # Cap the requested results
    if requested > max_allowed:
        parsed_criteria["max_results"] = max_allowed
        parsed_criteria["limit_warning"] = f"Your {plan} plan limits discovery to {max_allowed} leads per request."
        
    job_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        run_scout_discovery,
        job_id=job_id,
        tenant_id=tenant_id,
        target_criteria=parsed_criteria,
        auto_enrich=True
    )
    
    return {
        "job_id": job_id, 
        "criteria": parsed_criteria,
        "status": "queued"
    }
