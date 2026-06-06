"""
Scout Agent — discovers lead candidates from multiple sources.

Sources (per user entry in target_criteria):
- google_maps (Playwright)
- facebook (Playwright)
- instagram (Playwright)
- web (Playwright + Google search)
- brela (BRELA ORS lookup)
"""

import logging
from typing import Any

from app.agents.state import AgentState
from app.agents.tools.brela_tool import brela_lookup
from app.agents.tools.maps_tool import scrape_google_maps
from app.agents.tools.mock_scraper import mock_scrape_leads
from app.agents.tools.web_scraper import scrape_facebook, scrape_instagram, scrape_web
from app.config import get_settings

logger = logging.getLogger(__name__)


async def scout_node(state: AgentState) -> dict[str, Any]:
  """LangGraph node: discover leads from configured sources."""
  criteria = state.get("target_criteria", {})
  sources = criteria.get("sources", ["google_maps", "web"])
  locations = criteria.get("locations", ["Dar es Salaam, Tanzania"])
  industries = criteria.get("industries", ["business"])
  max_results = criteria.get("max_results", 50)
  search_query = criteria.get("search_query") or " ".join(industries)

  discovered: list[dict[str, Any]] = []
  metadata: dict[str, Any] = {"sources_used": [], "total_found": 0}

  settings = get_settings()
  if settings.use_mock_scraper:
    logger.info("Scout: using mock scraper (USE_MOCK_SCRAPER=true)")
    for location in locations:
      mock_results = await mock_scrape_leads(search_query, location, max_results)
      discovered.extend(mock_results)
      metadata["sources_used"].append({"source": "mock_scraper", "count": len(mock_results)})
    seen: set[str] = set()
    unique_mock: list[dict[str, Any]] = []
    for lead in discovered:
      name = (lead.get("company_name") or "").lower().strip()
      if name and name not in seen:
        seen.add(name)
        unique_mock.append(lead)
    metadata["total_found"] = len(unique_mock[:max_results])
    return {
      "discovered_leads": unique_mock[:max_results],
      "search_metadata": metadata,
      "current_agent": "scout",
      "messages": [{"role": "assistant", "content": f"Discovered {len(unique_mock[:max_results])} mock lead candidates"}],
    }

  per_source_limit = max(5, max_results // max(len(sources), 1))

  for location in locations:
    if "google_maps" in sources:
      logger.info("Scout: Google Maps — %s in %s", search_query, location)
      maps_results = await scrape_google_maps(search_query, location, per_source_limit)
      discovered.extend(maps_results)
      metadata["sources_used"].append({"source": "google_maps", "count": len(maps_results)})

    if "facebook" in sources:
      logger.info("Scout: Facebook — %s in %s", search_query, location)
      fb_results = await scrape_facebook(search_query, location, per_source_limit)
      discovered.extend(fb_results)
      metadata["sources_used"].append({"source": "facebook", "count": len(fb_results)})

    if "instagram" in sources:
      logger.info("Scout: Instagram — %s in %s", search_query, location)
      ig_results = await scrape_instagram(search_query, location, per_source_limit)
      discovered.extend(ig_results)
      metadata["sources_used"].append({"source": "instagram", "count": len(ig_results)})

    if "web" in sources:
      logger.info("Scout: Web — %s in %s", search_query, location)
      web_results = await scrape_web(search_query, location, per_source_limit)
      discovered.extend(web_results)
      metadata["sources_used"].append({"source": "web", "count": len(web_results)})

  if "brela" in sources:
    brela_numbers = criteria.get("brela_numbers", [])
    for reg in brela_numbers:
      result = await brela_lookup(reg)
      if result:
        discovered.append({**result, "source": "brela_verified"})
    metadata["sources_used"].append({"source": "brela", "count": len(brela_numbers)})

  # Deduplicate by company name
  seen: set[str] = set()
  unique: list[dict[str, Any]] = []
  for lead in discovered:
    name = (lead.get("company_name") or "").lower().strip()
    if name and name not in seen:
      seen.add(name)
      unique.append(lead)

  metadata["total_found"] = len(unique[:max_results])

  return {
    "discovered_leads": unique[:max_results],
    "search_metadata": metadata,
    "current_agent": "scout",
    "messages": [{"role": "assistant", "content": f"Discovered {len(unique[:max_results])} lead candidates"}],
  }
