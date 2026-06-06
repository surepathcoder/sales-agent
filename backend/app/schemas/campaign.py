"""Campaign schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import CampaignStatus, CampaignType
from app.schemas.common import ORMBase, TargetCriteria


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    campaign_type: CampaignType
    target_criteria: dict[str, Any] = Field(default_factory=dict)
    lead_pool: list[uuid.UUID] = Field(default_factory=list)
    agent_configuration: dict[str, Any] = Field(default_factory=dict)
    sequence_steps: list[dict[str, Any]] = Field(default_factory=list)


class CampaignResponse(ORMBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    campaign_type: CampaignType
    status: CampaignStatus
    target_criteria: dict[str, Any]
    lead_pool: list[uuid.UUID]
    agent_configuration: dict[str, Any]
    sequence_steps: list[dict[str, Any]]
    start_date: datetime | None
    end_date: datetime | None
    total_leads: int
    contacted_count: int
    engaged_count: int
    qualified_count: int
    converted_count: int
    budget_allocated: Decimal
    spend_to_date: Decimal
    roi_estimate: Decimal | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CampaignAnalytics(BaseModel):
    funnel: dict[str, int]
    channel_performance: dict[str, Any]
    sentiment_trends: list[dict[str, Any]]
    cost_per_lead: Decimal
    roi: Decimal | None
