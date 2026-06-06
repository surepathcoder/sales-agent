"""Researcher Agent — enriches leads with BRELA, web, and AI analysis."""

import logging
from typing import Any

from app.agents.state import AgentState
from app.agents.tools.brela_tool import brela_lookup
from app.agents.tools.web_scraper import scrape_web
from app.config import get_settings
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)


async def researcher_node(state: AgentState) -> dict[str, Any]:
  """LangGraph node: build lead dossier with ownership and buying signals."""
  tenant = state.get("tenant", {})
  tenant_id = tenant.get("tenant_id", "system")
  lead = state.get("lead", {})
  enriched = dict(lead)

  # BRELA enrichment
  brela_reg = lead.get("brela_reg_number") or lead.get("custom_fields", {}).get("brela_reg_number")
  if brela_reg:
    brela_data = await brela_lookup(brela_reg)
    if brela_data:
      enriched["brela"] = brela_data

  # Web enrichment (skip when mock scraper enabled — avoids slow Playwright)
  company = lead.get("company_name", "")
  settings = get_settings()
  if company and not settings.use_mock_scraper:
    web_data = await scrape_web(f"{company} Tanzania", max_results=3)
    enriched["web_mentions"] = web_data

  # AI analysis
  groq = GroqClient()
  try:
    scoring = await groq.score_lead(enriched, tenant_id=tenant_id)
  except Exception as e:
    logger.warning("Researcher scoring failed: %s", e)
    scoring = {"score": 50, "priority": "warm", "reasoning": "offline default"}
  enriched["ai_score"] = scoring

  risk_factors: list[str] = []
  if not enriched.get("phone") and not enriched.get("contacts"):
    risk_factors.append("No contact phone found")
  if scoring.get("score", 50) < 30:
    risk_factors.append("Low lead score")

  return {
    "enriched_lead": enriched,
    "risk_factors": risk_factors,
    "current_agent": "researcher",
    "messages": [{"role": "assistant", "content": f"Research complete for {company}"}],
  }
