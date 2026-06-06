"""Shared LangGraph agent state definitions."""

import operator
from typing import Annotated, Any, TypedDict


class TenantContext(TypedDict):
  tenant_id: str
  plan_type: str
  swahili_preference: float
  human_approval_required: bool


class LeadContext(TypedDict, total=False):
  lead_id: str
  company_name: str
  status: str
  lead_score: int
  contacts: list[dict[str, Any]]


class AgentState(TypedDict, total=False):
  """State passed through the LangGraph pipeline."""

  tenant: TenantContext
  lead: LeadContext
  target_criteria: dict[str, Any]
  discovered_leads: Annotated[list[dict[str, Any]], operator.add]
  enriched_lead: dict[str, Any]
  risk_factors: list[str]
  interaction_log: list[dict[str, Any]]
  next_step_recommendation: str
  deal_stage: str
  probability: int
  messages: Annotated[list[dict[str, str]], operator.add]
  agent_memories: list[dict[str, Any]]
  search_metadata: dict[str, Any]
  sent_message: str
  engagement_prediction: float
  deal_update: dict[str, Any]
  forecast_adjustment: dict[str, Any]
  token_usage: int
  current_agent: str
  job_id: str
  errors: Annotated[list[str], operator.add]
