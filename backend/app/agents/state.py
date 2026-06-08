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
  """State passed through the LangGraph pipeline.

  Full pipeline: Scout → Researcher → Enrichment → Outreach → Qualification → Closer
  Manager wraps the pipeline and monitors health / retries.
  """

  # --- Core context ---
  tenant: TenantContext
  lead: LeadContext
  target_criteria: dict[str, Any]

  # --- Scout ---
  discovered_leads: Annotated[list[dict[str, Any]], operator.add]
  search_metadata: dict[str, Any]

  # --- Researcher ---
  enriched_lead: dict[str, Any]
  risk_factors: list[str]

  # --- Enrichment Agent ---
  enrichment_data: dict[str, Any]       # contacts, emails, phones, socials discovered
  enrichment_confidence: float          # 0.0–1.0 confidence in enriched data

  # --- Outreach ---
  sent_message: str
  engagement_prediction: float
  interaction_log: list[dict[str, Any]]
  next_step_recommendation: str

  # --- Qualification Agent ---
  qualification: dict[str, Any]         # {qualified: bool, score: int, reason: str, …}
  qualification_score: int              # 0–100 composite qualification score
  should_advance: bool                  # True → proceed to closer; False → nurture/discard

  # --- Closer ---
  deal_stage: str
  probability: int
  deal_update: dict[str, Any]
  forecast_adjustment: dict[str, Any]

  # --- Manager Agent ---
  manager_report: dict[str, Any]        # workflow health, recommendations, telemetry
  pipeline_status: str                  # "healthy" | "degraded" | "failed"
  retry_count: int                      # how many retries the manager has issued

  # --- Shared ---
  messages: Annotated[list[dict[str, str]], operator.add]
  agent_memories: list[dict[str, Any]]
  token_usage: int
  current_agent: str
  job_id: str
  errors: Annotated[list[str], operator.add]
