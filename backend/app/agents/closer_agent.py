"""Closer Agent — deal stage management and forecasting."""

import logging
from typing import Any

from app.agents.state import AgentState
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)


async def closer_node(state: AgentState) -> dict[str, Any]:
  """LangGraph node: update deal stage and forecast."""
  tenant = state.get("tenant", {})
  tenant_id = tenant.get("tenant_id", "system")
  lead = state.get("lead", {})
  deal_context = state.get("target_criteria", {}).get("deal", {})

  stage = deal_context.get("stage", "qualification")
  probability = deal_context.get("probability", 25)

  groq = GroqClient()
  analysis = await groq.chat(
    [{
      "role": "user",
      "content": (
        f"Analyze deal for {lead.get('company_name')}. "
        f"Current stage: {stage}. Return JSON with recommended_stage, probability, next_actions."
      ),
    }],
    json_mode=True,
    tenant_id=tenant_id,
  )

  import json
  try:
    forecast = json.loads(analysis)
    stage = forecast.get("recommended_stage", stage)
    probability = forecast.get("probability", probability)
    next_actions = forecast.get("next_actions", ["Schedule follow-up meeting"])
  except json.JSONDecodeError:
    next_actions = ["Review proposal terms", "Confirm payment terms (30/60/90 days or LPO)"]

  return {
    "deal_stage": stage,
    "probability": probability,
    "deal_update": {
      "stage": stage,
      "probability": probability,
      "lead_id": lead.get("lead_id"),
    },
    "forecast_adjustment": {"category": "pipeline", "confidence": 0.6},
    "current_agent": "closer",
    "messages": [{"role": "assistant", "content": f"Deal updated to {stage} at {probability}%"}],
  }
