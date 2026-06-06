"""
Agent Supervisor — LangGraph orchestrator.

Pipeline: scout → researcher → outreach → closer → END
Supports human-in-the-loop gates and per-tenant cost tracking.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from app.agents.closer_agent import closer_node
from app.agents.memory import AgentMemoryStore
from app.agents.outreach_agent import outreach_node
from app.agents.researcher_agent import researcher_node
from app.agents.scout_agent import scout_node
from app.agents.state import AgentState
from app.config import get_settings
from app.database import get_db_context
from app.integrations.groq_client import GroqClient
from app.models.enums import AgentType, DealStage, LeadSource, LeadStatus, MemoryType
from app.schemas.deal import DealCreate
from app.schemas.lead import LeadCreate
from app.services.deal_service import DealService
from app.services.interaction_service import InteractionService
from app.services.lead_service import LeadService

logger = logging.getLogger(__name__)


def _route_after_scout(state: AgentState) -> Literal["researcher", "end"]:
  if state.get("discovered_leads"):
    return "researcher"
  return "end"


def _route_pipeline(state: AgentState) -> Literal["outreach", "closer", "end"]:
  mode = state.get("target_criteria", {}).get("pipeline_mode", "discovery")
  if mode == "outreach":
    return "outreach"
  if mode == "close":
    return "closer"
  return "end"


def build_agent_graph() -> StateGraph:
  """Build the LangGraph StateGraph with conditional routing."""
  graph = StateGraph(AgentState)

  graph.add_node("scout", scout_node)
  graph.add_node("researcher", researcher_node)
  graph.add_node("outreach", outreach_node)
  graph.add_node("closer", closer_node)

  graph.set_entry_point("scout")
  graph.add_conditional_edges("scout", _route_after_scout, {"researcher": "researcher", "end": END})
  graph.add_edge("researcher", "outreach")
  graph.add_conditional_edges("outreach", _route_pipeline, {"outreach": END, "closer": "closer", "end": END})
  graph.add_edge("closer", END)

  return graph.compile()


async def _update_job_status(
  job_id: str,
  status: str,
  data: dict | None = None,
  *,
  event: str | None = None,
  event_sw: str | None = None,
) -> None:
  from app.services.job_progress import update_job

  await update_job(job_id, status, data=data, event=event, event_sw=event_sw)


def _source_for_candidate(candidate: dict[str, Any]) -> LeadSource:
  source_map = {
    "google_maps": LeadSource.AI_DISCOVERED,
    "web_scraped": LeadSource.WEB_SCRAPED,
    "mock_scraper": LeadSource.AI_DISCOVERED,
    "brela_verified": LeadSource.BRELA_VERIFIED,
  }
  return source_map.get(candidate.get("source", ""), LeadSource.AI_DISCOVERED)


async def _enrich_lead(
  db,
  tenant_id: uuid.UUID,
  lead_id: uuid.UUID,
  human_approval_required: bool = True,
) -> None:
  """Run researcher agent and persist insights + memory."""
  lead_svc = LeadService(db, tenant_id)
  lead = await lead_svc.get_lead(lead_id)
  if not lead:
    return

  state: AgentState = {
    "tenant": {
      "tenant_id": str(tenant_id),
      "human_approval_required": human_approval_required,
    },
    "lead": {
      "lead_id": str(lead.id),
      "company_name": lead.company_name,
      "brela_reg_number": lead.brela_reg_number,
      "custom_fields": lead.custom_fields,
      "phone": lead.custom_fields.get("phone"),
      "contacts": [
        {"first_name": c.first_name, "whatsapp_number": c.whatsapp_number, "email": c.email}
        for c in lead.contacts
      ],
    },
    "target_criteria": {},
    "messages": [],
  }

  result = await researcher_node(state)
  enriched = result.get("enriched_lead", {})
  lead.ai_insights = {
    **lead.ai_insights,
    "research": enriched,
    "risk_factors": result.get("risk_factors", []),
    "ai_score": enriched.get("ai_score"),
  }
  lead.status = LeadStatus.RESEARCHING

  memory_store = AgentMemoryStore(db, tenant_id)
  await memory_store.store(
    AgentType.RESEARCHER,
    f"Research complete for {lead.company_name}: {enriched.get('ai_score', {})}",
    MemoryType.INSIGHT,
    lead_id=lead.id,
    confidence=0.85,
  )


async def _save_discovered_candidate(
  db,
  tenant_id: uuid.UUID,
  candidate: dict[str, Any],
  search_metadata: dict[str, Any],
) -> str | None:
  lead_svc = LeadService(db, tenant_id)
  groq = GroqClient()

  try:
    try:
      scoring = await groq.score_lead(candidate, tenant_id=str(tenant_id))
    except Exception as e:
      logger.warning("Lead scoring unavailable, using defaults: %s", e)
      scoring = {"score": 50, "priority": "warm", "reasoning": "Default score (LLM unavailable)"}

    lead = await lead_svc.create_lead(LeadCreate(
      company_name=candidate.get("company_name", "Unknown"),
      address=candidate.get("address"),
      location_lat=candidate.get("location_lat"),
      location_lng=candidate.get("location_lng"),
      source=_source_for_candidate(candidate),
      custom_fields={
        "discovery_source": candidate.get("source"),
        "phone": candidate.get("phone"),
        "website": candidate.get("website"),
        "facebook_url": candidate.get("facebook_url"),
        "instagram_url": candidate.get("instagram_url"),
        "search_metadata": search_metadata,
      },
    ))
    from app.models.enums import LeadPriority

    priority_map = {"hot": LeadPriority.HOT, "warm": LeadPriority.WARM, "cold": LeadPriority.COLD}
    lead.lead_score = scoring.get("score", 30)
    lead.priority = priority_map.get(scoring.get("priority", "cold"), LeadPriority.COLD)
    lead.status = LeadStatus.NEW
    lead.ai_insights = {"initial_score": scoring}

    phone = candidate.get("phone") or candidate.get("custom_fields", {}).get("phone")
    await lead_svc.add_contact_from_phone(lead.id, phone, lead.company_name)
    return str(lead.id)
  except ValueError as e:
    if "Duplicate" in str(e) or "tayari" in str(e):
      logger.info("Skipped duplicate: %s", candidate.get("company_name"))
    else:
      logger.error("Failed to save lead %s: %s", candidate.get("company_name"), e)
    return None
  except Exception as e:
    logger.error("Failed to save lead %s: %s", candidate.get("company_name"), e)
    return None


async def run_scout_discovery(
  job_id: str,
  tenant_id: uuid.UUID,
  target_criteria: dict[str, Any],
  auto_enrich: bool = True,
) -> None:
  """Run scout agent and persist discovered leads to database."""
  total_target = target_criteria.get("max_results", 50)
  await _update_job_status(
    job_id,
    "running",
    {"step": "starting", "progress_pct": 0, "total": total_target, "saved_count": 0},
    event="Starting Scout agent...",
    event_sw="Inaanza kutafuta wateja...",
  )

  try:
    initial_state: AgentState = {
      "tenant": {
        "tenant_id": str(tenant_id),
        "plan_type": "free",
        "swahili_preference": 0.5,
        "human_approval_required": True,
      },
      "target_criteria": {**target_criteria, "pipeline_mode": "discovery"},
      "discovered_leads": [],
      "messages": [],
      "job_id": job_id,
    }

    await _update_job_status(
      job_id,
      "running",
      {"step": "scouting", "progress_pct": 10},
      event="Searching Google Maps, Facebook, Instagram, and web...",
      event_sw="Inatafuta kwenye Ramani, Facebook, Instagram na mtandao...",
    )
    scout_result = await scout_node(initial_state)
    discovered = scout_result.get("discovered_leads", [])
    search_metadata = scout_result.get("search_metadata", {})

    if not discovered:
      await _update_job_status(
        job_id,
        "completed",
        {
          "discovered_count": 0,
          "saved_count": 0,
          "lead_ids": [],
          "progress_pct": 100,
          "search_metadata": search_metadata,
          "warning": "No leads found. Try a different query or location.",
        },
        event="No leads found for this search.",
        event_sw="Hakuna wateja waliopatikana kwa utafutaji huu.",
      )
      return

    await _update_job_status(
      job_id,
      "running",
      {
        "step": "found",
        "progress_pct": 25,
        "discovered_count": len(discovered),
        "total": len(discovered),
      },
      event=f"Found {len(discovered)} lead candidates",
      event_sw=f"Wateja {len(discovered)} wamepatikana",
    )

    saved_ids: list[str] = []
    async with get_db_context() as db:
      for idx, candidate in enumerate(discovered):
        name = candidate.get("company_name", "Unknown")
        pct = 25 + int((idx / max(len(discovered), 1)) * 65)
        await _update_job_status(
          job_id,
          "running",
          {
            "step": "saving",
            "progress_pct": pct,
            "current_company": name,
            "processed": idx,
            "total": len(discovered),
            "saved_count": len(saved_ids),
          },
          event=f"Scoring and saving: {name}",
          event_sw=f"Inahifadhi: {name}",
        )
        lead_id = await _save_discovered_candidate(db, tenant_id, candidate, search_metadata)
        if lead_id:
          saved_ids.append(lead_id)
          await _update_job_status(
            job_id,
            "running",
            {
              "step": "saved",
              "progress_pct": pct,
              "current_company": name,
              "processed": idx + 1,
              "total": len(discovered),
              "saved_count": len(saved_ids),
              "last_saved_lead_id": lead_id,
            },
            event=f"Saved ✓ {name}",
            event_sw=f"Imehifadhiwa ✓ {name}",
          )
          if auto_enrich:
            await _update_job_status(
              job_id,
              "running",
              {"step": "enriching", "current_company": name},
              event=f"Researching {name}...",
              event_sw=f"Inachambua {name}...",
            )
            try:
              await _enrich_lead(db, tenant_id, uuid.UUID(lead_id))
            except Exception as e:
              logger.error("Enrich failed for %s: %s", lead_id, e)

    await _update_job_status(
      job_id,
      "completed",
      {
        "discovered_count": len(discovered),
        "saved_count": len(saved_ids),
        "lead_ids": saved_ids,
        "progress_pct": 100,
        "search_metadata": search_metadata,
      },
      event=f"Done! {len(saved_ids)} leads saved to your pipeline.",
      event_sw=f"Imekamilika! Wateja {len(saved_ids)} wamehifadhiwa.",
    )
  except Exception as e:
    logger.exception("Scout discovery failed: %s", e)
    await _update_job_status(job_id, "failed", {"error": str(e)})


async def run_outreach_for_lead(
  db,
  tenant_id: uuid.UUID,
  lead_id: uuid.UUID,
  *,
  campaign_id: uuid.UUID | None = None,
  human_approval_required: bool = True,
  step_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
  """Run outreach agent for a single lead and persist interaction."""
  lead_svc = LeadService(db, tenant_id)
  interaction_svc = InteractionService(db, tenant_id)
  lead = await lead_svc.get_lead(lead_id)
  if not lead:
    return {"error": "Lead not found"}

  if not lead.contacts:
    return {"error": "No contacts on lead — add a WhatsApp number first"}

  state: AgentState = {
    "tenant": {
      "tenant_id": str(tenant_id),
      "human_approval_required": human_approval_required,
      "swahili_preference": 0.5,
    },
    "lead": {
      "lead_id": str(lead.id),
      "company_name": lead.company_name,
      "contacts": [
        {"first_name": c.first_name, "whatsapp_number": c.whatsapp_number, "email": c.email}
        for c in lead.contacts
      ],
    },
    "target_criteria": {"step_config": step_config or {}, "pipeline_mode": "outreach"},
    "messages": [],
  }

  result = await outreach_node(state)
  contact = lead.contacts[0]
  message = result.get("sent_message", "")
  pending = human_approval_required

  interaction = await interaction_svc.create_outreach_interaction(
    lead_id=lead.id,
    contact_id=contact.id,
    content=message,
    campaign_id=campaign_id,
    pending_approval=pending,
    metadata={"engagement_prediction": result.get("engagement_prediction")},
  )

  if not pending:
    lead.status = LeadStatus.CONTACTED

  memory_store = AgentMemoryStore(db, tenant_id)
  await memory_store.store(
    AgentType.OUTREACH,
    f"Outreach to {lead.company_name}: {message[:200]}",
    MemoryType.TASK,
    lead_id=lead.id,
    contact_id=contact.id,
    confidence=0.75,
  )

  return {
    "interaction_id": str(interaction.id),
    "status": "pending_approval" if pending else "sent",
    "message": message,
  }


async def trigger_agent_manual(
  job_id: str,
  tenant_id: uuid.UUID,
  agent_type: Any,
  lead_id: uuid.UUID | None = None,
  campaign_id: uuid.UUID | None = None,
  context: dict | None = None,
) -> None:
  """Manually trigger a specific agent for testing."""
  await _update_job_status(job_id, "running", {"agent_type": agent_type.value})

  try:
    async with get_db_context() as db:
      if agent_type.value == "outreach" and lead_id:
        result = await run_outreach_for_lead(
          db,
          tenant_id,
          lead_id,
          campaign_id=campaign_id,
          human_approval_required=context.get("human_approval_required", True) if context else True,
          step_config=context.get("step_config") if context else None,
        )
        await _update_job_status(job_id, "completed", result)
        return

      if agent_type.value == "researcher" and lead_id:
        await _enrich_lead(db, tenant_id, lead_id)
        await _update_job_status(job_id, "completed", {"lead_id": str(lead_id), "status": "enriched"})
        return

      nodes = {
        "scout": scout_node,
        "researcher": researcher_node,
        "outreach": outreach_node,
        "closer": closer_node,
      }
      node_fn = nodes.get(agent_type.value)
      if not node_fn:
        await _update_job_status(job_id, "failed", {"error": "Unknown agent type"})
        return

      state: AgentState = {
        "tenant": {"tenant_id": str(tenant_id), "human_approval_required": False},
        "target_criteria": context or {},
        "lead": {"lead_id": str(lead_id)} if lead_id else {},
        "messages": [],
        "job_id": job_id,
      }

      if lead_id:
        lead_svc = LeadService(db, tenant_id)
        lead = await lead_svc.get_lead(lead_id)
        if lead:
          state["lead"] = {
            "lead_id": str(lead.id),
            "company_name": lead.company_name,
            "status": lead.status.value,
            "contacts": [
              {"first_name": c.first_name, "whatsapp_number": c.whatsapp_number, "email": c.email}
              for c in lead.contacts
            ],
          }

      result = await node_fn(state)

      if agent_type.value == "closer" and lead_id and result.get("deal_update"):
        deal_svc = DealService(db, tenant_id)
        stage_str = result.get("deal_stage", "qualification")
        stage_map = {
          "prospecting": DealStage.PROSPECTING,
          "qualification": DealStage.QUALIFICATION,
          "proposal": DealStage.PROPOSAL,
          "negotiation": DealStage.NEGOTIATION,
          "closed_won": DealStage.CLOSED_WON,
        }
        await deal_svc.create_deal(
          DealCreate(
            lead_id=lead_id,
            deal_name=f"{state['lead'].get('company_name', 'Deal')} — AI Forecast",
            value=Decimal("1000000"),
            probability=result.get("probability", 25),
            stage=stage_map.get(stage_str, DealStage.QUALIFICATION),
            expected_close_date=datetime.now(timezone.utc) + timedelta(days=60),
          ),
        )

      await _update_job_status(job_id, "completed", result)
  except Exception as e:
    logger.exception("Agent trigger failed: %s", e)
    await _update_job_status(job_id, "failed", {"error": str(e)})
