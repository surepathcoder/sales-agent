"""Lead schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    CompanySize,
    LeadPriority,
    LeadSource,
    LeadStatus,
    NextActionType,
)
from app.schemas.common import ORMBase, TargetCriteria


class LeadCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    trading_name: str | None = None
    source: LeadSource = LeadSource.MANUAL
    brela_reg_number: str | None = None
    industry_code: str = "0000"
    company_size: CompanySize = CompanySize.SMALL
    address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority: LeadPriority | None = None
    assigned_to: uuid.UUID | None = None
    tags: list[str] | None = None
    next_action_at: datetime | None = None
    next_action_type: NextActionType | None = None
    ai_insights: dict[str, Any] | None = None


class LeadResponse(ORMBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    source: LeadSource
    brela_reg_number: str | None
    company_name: str
    trading_name: str | None
    industry_code: str
    company_size: CompanySize
    annual_revenue_estimate: Decimal | None
    status: LeadStatus
    lead_score: int
    priority: LeadPriority
    assigned_to: uuid.UUID | None
    tags: list[str]
    custom_fields: dict[str, Any]
    ai_insights: dict[str, Any]
    location_lat: float | None
    location_lng: float | None
    address: str | None
    last_contact_at: datetime | None
    next_action_at: datetime | None
    next_action_type: NextActionType | None
    created_at: datetime
    updated_at: datetime
    contact_count: int = 0


from app.schemas.contact import LeadContactResponse
from app.schemas.deal import DealResponse
from app.schemas.interaction import InteractionResponse

class AgentMemorySchema(ORMBase):
    id: uuid.UUID
    agent_type: str
    memory_type: str
    content: str
    confidence_score: float

class LeadDossierResponse(LeadResponse):
    contacts: list[LeadContactResponse] = Field(default_factory=list)
    interactions: list[InteractionResponse] = Field(default_factory=list)
    deals: list[DealResponse] = Field(default_factory=list)
    agent_memories: list[AgentMemorySchema] = Field(default_factory=list)


class DiscoverLeadsRequest(BaseModel):
    target_criteria: TargetCriteria
    auto_enrich: bool = True
    auto_start_campaign: bool = False
