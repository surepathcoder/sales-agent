"""
Agent Supervisor — LangGraph orchestrator.

Full Multi-Agent Pipeline:
  Manager(pre) → Scout → Researcher → Enrichment → Outreach → Qualification → Closer → Manager(post) → END

Each node is a standalone async function operating on shared AgentState.
The Manager wraps the pipeline with pre-checks and post-analysis.
Supports human-in-the-loop gates and per-tenant cost tracking.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal

from langgraph.graph import END, StateGraph

from app.agents.closer_agent import closer_node
from app.agents.enrichment_agent import enrichment_node
from app.agents.manager_agent import (
    manager_error_handler,
    manager_post_pipeline,
    manager_pre_pipeline,
)
from app.agents.memory import AgentMemoryStore
from app.agents.outreach_agent import outreach_node
from app.agents.qualification_agent import qualification_node
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


# ── Routing functions ─────────────────────────────────────────────────

def _route_after_scout(state: AgentState) -> Literal["researcher", "end"]:
    """After Scout: proceed to Researcher if leads discovered, else end."""
    if state.get("discovered_leads"):
        return "researcher"
    return "end"


def _route_after_qualification(
    state: AgentState,
) -> Literal["closer", "manager_post"]:
    """After Qualification: advance to Closer if qualified, else skip to Manager(post)."""
    if state.get("should_advance", False):
        return "closer"
    return "manager_post"


def _route_pipeline_mode(
    state: AgentState,
) -> Literal["outreach", "closer", "manager_post"]:
    """After Enrichment: route based on pipeline_mode.

    - 'discovery' → finish (manager_post)
    - 'outreach' → outreach
    - 'close' → closer (skip outreach + qualification)
    """
    mode = state.get("target_criteria", {}).get("pipeline_mode", "discovery")
    if mode == "outreach":
        return "outreach"
    if mode == "close":
        return "closer"
    return "manager_post"


def _route_manager_pre(state: AgentState) -> Literal["scout", "end"]:
    """After Manager pre-check: proceed if healthy, abort if critical errors."""
    status = state.get("pipeline_status", "healthy")
    if status == "failed":
        return "end"
    return "scout"


# ── Graph builder ─────────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Build the full LangGraph StateGraph with 7 agents.

    Pipeline:
      manager_pre → scout → researcher → enrichment
        → [outreach → qualification → closer (conditional)] → manager_post → END

    Routing:
      - After scout: stop if no leads found
      - After enrichment: route by pipeline_mode
      - After qualification: advance to closer only if qualified
      - Manager wraps with pre/post monitoring
    """
    graph = StateGraph(AgentState)

    # Register all 7 agent nodes
    graph.add_node("manager_pre", manager_pre_pipeline)
    graph.add_node("scout", scout_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("enrichment", enrichment_node)
    graph.add_node("outreach", outreach_node)
    graph.add_node("qualification", qualification_node)
    graph.add_node("closer", closer_node)
    graph.add_node("manager_post", manager_post_pipeline)

    # Entry: Manager pre-check
    graph.set_entry_point("manager_pre")

    # Manager pre → Scout (or abort)
    graph.add_conditional_edges(
        "manager_pre",
        _route_manager_pre,
        {"scout": "scout", "end": END},
    )

    # Scout → Researcher (if leads) or END
    graph.add_conditional_edges(
        "scout",
        _route_after_scout,
        {"researcher": "researcher", "end": END},
    )

    # Researcher → Enrichment (always)
    graph.add_edge("researcher", "enrichment")

    # Enrichment → Outreach / Closer / Manager(post) based on pipeline_mode
    graph.add_conditional_edges(
        "enrichment",
        _route_pipeline_mode,
        {"outreach": "outreach", "closer": "closer", "manager_post": "manager_post"},
    )

    # Outreach → Qualification (always)
    graph.add_edge("outreach", "qualification")

    # Qualification → Closer (if qualified) or Manager(post) (nurture/disqualify)
    graph.add_conditional_edges(
        "qualification",
        _route_after_qualification,
        {"closer": "closer", "manager_post": "manager_post"},
    )

    # Closer → Manager post (always)
    graph.add_edge("closer", "manager_post")

    # Manager post → END
    graph.add_edge("manager_post", END)

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
    "research_report": enriched.get("research_report"),
  }
  lead.status = LeadStatus.RESEARCHING

  # Save contacts, emails, and socials from website_enriched
  website_enriched = enriched.get("website_enriched")
  if website_enriched:
    custom = lead.custom_fields or {}
    updated_custom = {**custom}
    if website_enriched.get("facebook"):
      updated_custom["facebook_url"] = website_enriched.get("facebook")
    if website_enriched.get("instagram"):
      updated_custom["instagram_url"] = website_enriched.get("instagram")
    if website_enriched.get("linkedin"):
      updated_custom["linkedin_url"] = website_enriched.get("linkedin")
    if website_enriched.get("email"):
      updated_custom["email"] = website_enriched.get("email")
    
    phones = website_enriched.get("phones") or []
    if phones and not custom.get("phone"):
      updated_custom["phone"] = phones[0]
      lead.custom_fields = updated_custom
      await lead_svc.add_contact_from_phone(lead.id, phones[0], lead.company_name)
    else:
      lead.custom_fields = updated_custom

    email = website_enriched.get("email")
    if email:
      existing_emails = [c.email for c in lead.contacts if c.email]
      if email not in existing_emails:
        from app.schemas.contact import LeadContactCreate
        from app.models.enums import ContactType
        await lead_svc.add_contact(
          lead.id,
          LeadContactCreate(
            first_name="Info / Support",
            last_name="",
            email=email,
            phone=phones[0] if phones else None,
            whatsapp_number=phones[0] if phones else None,
            contact_type=ContactType.PROCUREMENT,
            is_decision_maker=False,
          )
        )

  # ── Enrichment Agent — classify contacts and discover more data ──
  try:
    enrich_state: AgentState = {
      **state,
      "enriched_lead": enriched,
    }
    enrich_result = await enrichment_node(enrich_state)
    enrichment_data = enrich_result.get("enrichment_data", {})
    lead.ai_insights = {
      **lead.ai_insights,
      "enrichment": enrichment_data,
      "enrichment_confidence": enrich_result.get("enrichment_confidence", 0),
    }

    # Persist decision-makers discovered by enrichment
    for dm in enrichment_data.get("decision_makers", []):
      dm_email = dm.get("email", "")
      dm_phone = dm.get("phone", "")
      existing_emails = [c.email for c in lead.contacts if c.email]
      existing_phones = [c.whatsapp_number for c in lead.contacts if c.whatsapp_number]
      if dm_email and dm_email not in existing_emails:
        from app.schemas.contact import LeadContactCreate
        from app.models.enums import ContactType
        role_map = {
          "owner": ContactType.OWNER,
          "director": ContactType.DIRECTOR,
          "manager": ContactType.MANAGER,
          "procurement": ContactType.PROCUREMENT,
          "finance": ContactType.FINANCE,
          "operations": ContactType.OPERATIONS,
        }
        await lead_svc.add_contact(
          lead.id,
          LeadContactCreate(
            first_name=dm.get("name", "Decision Maker"),
            last_name="",
            email=dm_email,
            phone=dm_phone or None,
            whatsapp_number=dm_phone or None,
            contact_type=role_map.get(dm.get("role", ""), ContactType.PROCUREMENT),
            is_decision_maker=True,
          )
        )

    memory_store_e = AgentMemoryStore(db, tenant_id)
    await memory_store_e.store(
      AgentType.ENRICHMENT,
      f"Enrichment for {lead.company_name}: {enrichment_data.get('contacts_count', 0)} contacts",
      MemoryType.INSIGHT,
      lead_id=lead.id,
      confidence=enrich_result.get("enrichment_confidence", 0.5),
    )
  except Exception as e:
    logger.error("Enrichment agent failed for %s: %s", lead.company_name, e)

  memory_store = AgentMemoryStore(db, tenant_id)
  await memory_store.store(
    AgentType.RESEARCHER,
    f"Research complete for {lead.company_name}: {enriched.get('ai_score', {})}",
    MemoryType.INSIGHT,
    lead_id=lead.id,
    confidence=0.85,
  )


def calculate_rule_based_score(candidate: dict[str, Any]) -> tuple[int, list[str]]:
  """Compute rule-based scoring based on reviews, rating, and online presence."""
  score = 0
  reasons = []

  if candidate.get("website"):
    score += 20
    reasons.append("website_exists")
  if candidate.get("phone"):
    score += 10
    reasons.append("phone_exists")
  if candidate.get("email") or candidate.get("facebook_url") or candidate.get("instagram_url") or candidate.get("linkedin_url"):
    score += 20
    reasons.append("online_contacts_exist")

  rating_val = candidate.get("rating")
  if rating_val:
    try:
      rating = float(str(rating_val).replace(",", ""))
      if rating >= 4.0:
        score += 20
        reasons.append("rating_gt_4")
    except Exception:
      pass

  reviews_val = candidate.get("reviews_count")
  if reviews_val:
    try:
      reviews = int(str(reviews_val).replace(",", ""))
      if reviews >= 100:
        score += 20
        reasons.append("reviews_gt_100")
      elif reviews >= 10:
        score += 10
        reasons.append("reviews_gt_10")
    except Exception:
      pass

  return min(score, 100), reasons


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

    # Calculate rule-based heuristic score
    rule_score, rule_reasons = calculate_rule_based_score(candidate)

    # Combine LLM and rule-based heuristic score
    llm_score = scoring.get("score", 50)
    combined_score = int(0.4 * rule_score + 0.6 * llm_score)

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
        "linkedin_url": candidate.get("linkedin_url"),
        "category": candidate.get("category"),
        "rating": candidate.get("rating"),
        "reviews_count": candidate.get("reviews_count"),
        "search_metadata": search_metadata,
      },
    ))
    from app.models.enums import LeadPriority

    # Set priority based on combined score
    lead.lead_score = combined_score
    if combined_score >= 75:
      lead.priority = LeadPriority.HOT
    elif combined_score >= 40:
      lead.priority = LeadPriority.WARM
    else:
      lead.priority = LeadPriority.COLD

    lead.status = LeadStatus.NEW
    lead.ai_insights = {
      "initial_score": scoring,
      "rule_based_score": {
        "score": rule_score,
        "reasons": rule_reasons
      }
    }

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
  limit_warning = target_criteria.get("limit_warning")
  job_data = {"step": "starting", "progress_pct": 0, "total": total_target, "saved_count": 0}
  if limit_warning:
    job_data["limit_warning"] = limit_warning
  await _update_job_status(
    job_id,
    "running",
    job_data,
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

    warning_msg = None
    if len(discovered) > 0 and len(saved_ids) == 0:
      warning_msg = "Leads were found but could not be saved (duplicate or plan limit reached)."

    await _update_job_status(
      job_id,
      "completed",
      {
        "discovered_count": len(discovered),
        "saved_count": len(saved_ids),
        "lead_ids": saved_ids,
        "progress_pct": 100,
        "search_metadata": search_metadata,
        "warning": warning_msg,
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
      "ai_insights": lead.ai_insights,
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

  from app.models.enums import InteractionChannel
  channel_str = (step_config or {}).get("channel", "whatsapp")
  if channel_str == "voice_note":
    db_channel = InteractionChannel.WHATSAPP
  else:
    try:
      db_channel = InteractionChannel(channel_str)
    except ValueError:
      db_channel = InteractionChannel.WHATSAPP

  interaction = await interaction_svc.create_outreach_interaction(
    lead_id=lead.id,
    contact_id=contact.id,
    content=message,
    campaign_id=campaign_id,
    pending_approval=pending,
    channel=db_channel,
    metadata={"engagement_prediction": result.get("engagement_prediction"), **result.get("extra_metadata", {})},
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
        "enrichment": enrichment_node,
        "outreach": outreach_node,
        "qualification": qualification_node,
        "closer": closer_node,
        "manager": manager_post_pipeline,
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
            "ai_insights": lead.ai_insights,
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
