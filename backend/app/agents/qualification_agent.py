"""
Qualification Agent — evaluate lead readiness and intent.

Pipeline position:
  Scout → Researcher → Enrichment → Outreach → **Qualification** → Closer

Uses Groq LLM to analyze:
- Lead engagement signals (responses, sentiment)
- Business fit (company size, industry alignment)
- Budget indicators
- Decision-maker access
- Tanzania-specific buying signals (LPO readiness, tender participation)
"""

import json
import logging
from typing import Any

from app.agents.state import AgentState
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)

# BANT + Tanzania-specific qualification criteria
QUALIFICATION_CRITERIA = {
    "budget": {
        "weight": 25,
        "signals": [
            "mentions budget", "asks about pricing", "discusses payment terms",
            "LPO process", "procurement cycle",
        ],
    },
    "authority": {
        "weight": 25,
        "signals": [
            "decision-maker identified", "owner engaged", "director contact",
            "procurement officer", "multiple stakeholders",
        ],
    },
    "need": {
        "weight": 25,
        "signals": [
            "pain point expressed", "current challenges", "growth plans",
            "competitor dissatisfaction", "specific use case",
        ],
    },
    "timeline": {
        "weight": 25,
        "signals": [
            "urgency expressed", "deadline mentioned", "fiscal year end",
            "tender deadline", "seasonal demand",
        ],
    },
}


async def qualification_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: evaluate whether a lead is qualified to advance to Closer.

    Analyzes enrichment data, outreach interactions, and research to produce
    a qualification verdict with BANT scoring.
    """
    tenant = state.get("tenant", {})
    tenant_id = tenant.get("tenant_id", "system")
    lead = state.get("lead", {})
    enriched = state.get("enriched_lead", {})
    enrichment = state.get("enrichment_data", {})
    interactions = state.get("interaction_log", [])
    sent_message = state.get("sent_message", "")
    engagement = state.get("engagement_prediction", 0.0)
    risk_factors = state.get("risk_factors", [])
    research_report = enriched.get("research_report", {})

    company = lead.get("company_name", enriched.get("company_name", "Unknown"))
    contacts = lead.get("contacts", [])

    # Build qualification context for LLM
    context = {
        "company_name": company,
        "lead_score": lead.get("lead_score", enriched.get("ai_score", {}).get("score", 50)),
        "contacts_count": len(contacts),
        "has_decision_maker": any(
            c.get("is_decision_maker") for c in enrichment.get("decision_makers", [])
        ),
        "emails_found": len(enrichment.get("emails", [])),
        "phones_found": len(enrichment.get("phones", [])),
        "socials": enrichment.get("socials", {}),
        "engagement_prediction": engagement,
        "risk_factors": risk_factors,
        "research_summary": research_report.get("summary", ""),
        "pain_points": research_report.get("pain_points", []),
        "interactions": [
            {
                "channel": i.get("channel"),
                "direction": i.get("direction"),
                "status": i.get("status"),
            }
            for i in interactions[:5]  # last 5 interactions
        ],
        "sent_message_preview": sent_message[:200] if sent_message else "",
    }

    groq = GroqClient()
    prompt = (
        "You are a B2B lead qualification expert for the Tanzanian market.\n"
        "Analyze this lead and determine if they are qualified to advance to the deal stage.\n\n"
        f"Lead context:\n{json.dumps(context, indent=2)}\n\n"
        "Score using BANT framework (Budget, Authority, Need, Timeline).\n"
        "Each criterion is 0–25 points, total max 100.\n\n"
        "Consider Tanzania-specific factors:\n"
        "- LPO/procurement readiness\n"
        "- Relationship-first business culture\n"
        "- Decision-making hierarchy (often family-owned)\n"
        "- Seasonal business patterns\n"
        "- Mobile-first communication preference\n\n"
        "Return JSON:\n"
        "{\n"
        '  "qualified": true/false,\n'
        '  "score": 0-100,\n'
        '  "budget_score": 0-25,\n'
        '  "authority_score": 0-25,\n'
        '  "need_score": 0-25,\n'
        '  "timeline_score": 0-25,\n'
        '  "reasoning": "why qualified or not",\n'
        '  "recommended_action": "next step",\n'
        '  "objections": ["list of potential objections"],\n'
        '  "deal_readiness": "ready|nurture|disqualified",\n'
        '  "suggested_deal_value_tzs": 0,\n'
        '  "confidence": 0.0-1.0\n'
        "}"
    )

    try:
        raw = await groq.chat(
            [{"role": "user", "content": prompt}],
            json_mode=True,
            tenant_id=tenant_id,
        )
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Qualification LLM analysis failed: %s", e)
        # Fallback rule-based scoring
        rule_score = _rule_based_qualification(context)
        result = {
            "qualified": rule_score >= 50,
            "score": rule_score,
            "budget_score": 10,
            "authority_score": 15 if context["has_decision_maker"] else 5,
            "need_score": 15 if context["research_summary"] else 5,
            "timeline_score": 10,
            "reasoning": "Rule-based fallback (LLM unavailable)",
            "recommended_action": "Follow up via WhatsApp",
            "objections": [],
            "deal_readiness": "nurture" if rule_score < 50 else "ready",
            "suggested_deal_value_tzs": 0,
            "confidence": 0.4,
        }

    qualified = result.get("qualified", False)
    score = result.get("score", 0)
    should_advance = qualified and score >= 50

    # Determine pipeline recommendation
    deal_readiness = result.get("deal_readiness", "nurture")
    if deal_readiness == "disqualified":
        recommendation = f"Disqualify {company} — low fit"
        should_advance = False
    elif deal_readiness == "nurture":
        recommendation = f"Nurture {company} with value content before re-qualifying"
        should_advance = False
    else:
        recommendation = f"Advance {company} to deal stage — BANT score {score}/100"
        should_advance = True

    return {
        "qualification": result,
        "qualification_score": score,
        "should_advance": should_advance,
        "next_step_recommendation": recommendation,
        "current_agent": "qualification",
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"Qualification for {company}: "
                    f"{'✅ QUALIFIED' if qualified else '⏳ NOT YET QUALIFIED'} "
                    f"(score: {score}/100, readiness: {deal_readiness})"
                ),
            }
        ],
    }


def _rule_based_qualification(ctx: dict[str, Any]) -> int:
    """Fallback rule-based scoring when LLM is unavailable."""
    score = 0

    # Authority signals
    if ctx.get("has_decision_maker"):
        score += 20
    if ctx.get("contacts_count", 0) >= 2:
        score += 5

    # Need signals
    if ctx.get("research_summary"):
        score += 10
    if ctx.get("pain_points"):
        score += 10

    # Engagement signals
    if ctx.get("engagement_prediction", 0) > 0.4:
        score += 15
    elif ctx.get("engagement_prediction", 0) > 0.2:
        score += 8

    # Contact availability
    if ctx.get("emails_found", 0) > 0:
        score += 10
    if ctx.get("phones_found", 0) > 0:
        score += 10

    # Social presence
    socials = ctx.get("socials", {})
    if any(socials.values()):
        score += 5

    # Lead score from earlier stages
    lead_score = ctx.get("lead_score", 50)
    if lead_score >= 70:
        score += 15
    elif lead_score >= 40:
        score += 8

    # Risk penalty
    risk_factors = ctx.get("risk_factors", [])
    score -= len(risk_factors) * 5

    return max(0, min(score, 100))
