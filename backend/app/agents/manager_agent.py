"""
Manager Agent — workflow orchestrator and health monitor.

Wraps the full pipeline and provides:
- Pipeline health monitoring
- Error recovery / retry logic
- Agent performance telemetry
- Workflow optimization recommendations
- Token usage tracking
- SLA monitoring

Pipeline:
  Scout → Researcher → Enrichment → Outreach → Qualification → Closer
                    ↕ Manager (monitors all nodes) ↕
"""

import json
import logging
import time
from typing import Any

from app.agents.state import AgentState
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)

# Agent SLA thresholds (seconds)
AGENT_SLA = {
    "scout": 120,
    "researcher": 60,
    "enrichment": 90,
    "outreach": 30,
    "qualification": 15,
    "closer": 15,
}

MAX_RETRIES = 2


def _compute_pipeline_health(
    agent_results: dict[str, dict[str, Any]],
    errors: list[str],
) -> str:
    """Determine overall pipeline health based on agent results."""
    if not agent_results:
        return "unknown"

    error_count = len(errors)
    total_agents = len(agent_results)

    if error_count == 0:
        return "healthy"
    if error_count <= total_agents * 0.3:
        return "degraded"
    return "failed"


def _build_telemetry(state: AgentState) -> dict[str, Any]:
    """Build telemetry report from pipeline state."""
    messages = state.get("messages", [])
    errors = state.get("errors", [])

    # Count messages per agent
    agent_message_counts: dict[str, int] = {}
    for msg in messages:
        role = msg.get("role", "unknown")
        agent_message_counts[role] = agent_message_counts.get(role, 0) + 1

    return {
        "total_messages": len(messages),
        "total_errors": len(errors),
        "token_usage": state.get("token_usage", 0),
        "agents_executed": [
            agent for agent in
            ["scout", "researcher", "enrichment", "outreach", "qualification", "closer"]
            if any(msg.get("content", "").lower().startswith(agent)
                   for msg in messages if msg.get("role") == "assistant")
        ],
        "error_details": errors[-5:] if errors else [],  # last 5 errors
    }


async def manager_pre_pipeline(state: AgentState) -> dict[str, Any]:
    """Manager pre-check: validate inputs before pipeline starts.

    Called as the entry node to validate tenant context, criteria,
    and set up monitoring metadata.
    """
    tenant = state.get("tenant", {})
    target_criteria = state.get("target_criteria", {})
    errors: list[str] = []

    # Validate required inputs
    if not tenant.get("tenant_id"):
        errors.append("Missing tenant_id")

    pipeline_mode = target_criteria.get("pipeline_mode", "discovery")

    # Set initial pipeline status
    report = {
        "phase": "pre_pipeline",
        "pipeline_mode": pipeline_mode,
        "validation_passed": len(errors) == 0,
        "timestamp": time.time(),
        "checks": {
            "tenant_valid": bool(tenant.get("tenant_id")),
            "criteria_present": bool(target_criteria),
            "pipeline_mode": pipeline_mode,
        },
    }

    return {
        "manager_report": report,
        "pipeline_status": "healthy" if not errors else "degraded",
        "retry_count": 0,
        "current_agent": "manager",
        "errors": errors,
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"Manager: Pipeline initialized (mode={pipeline_mode}). "
                    f"{'All checks passed ✓' if not errors else f'{len(errors)} issues found'}"
                ),
            }
        ],
    }


async def manager_post_pipeline(state: AgentState) -> dict[str, Any]:
    """Manager post-pipeline: analyze results, generate recommendations.

    Called as the final node after all pipeline stages complete.
    """
    tenant = state.get("tenant", {})
    tenant_id = tenant.get("tenant_id", "system")
    errors = state.get("errors", [])
    lead = state.get("lead", {})
    company = lead.get("company_name", "Unknown")

    # Gather results from all stages
    telemetry = _build_telemetry(state)
    pipeline_status = _compute_pipeline_health(
        {
            "scout": {"discovered": len(state.get("discovered_leads", []))},
            "researcher": {"enriched": bool(state.get("enriched_lead"))},
            "enrichment": {"data": bool(state.get("enrichment_data"))},
            "outreach": {"sent": bool(state.get("sent_message"))},
            "qualification": {"score": state.get("qualification_score", 0)},
            "closer": {"deal": bool(state.get("deal_update"))},
        },
        errors,
    )

    # Build comprehensive pipeline summary
    summary = {
        "company": company,
        "discovered_leads": len(state.get("discovered_leads", [])),
        "enrichment_confidence": state.get("enrichment_confidence", 0),
        "qualification_score": state.get("qualification_score", 0),
        "should_advance": state.get("should_advance", False),
        "deal_stage": state.get("deal_stage"),
        "deal_probability": state.get("probability", 0),
        "engagement_prediction": state.get("engagement_prediction", 0),
        "pipeline_status": pipeline_status,
    }

    # LLM-powered workflow recommendations
    recommendations = await _generate_recommendations(
        summary, telemetry, errors, tenant_id
    )

    report = {
        "phase": "post_pipeline",
        "timestamp": time.time(),
        "summary": summary,
        "telemetry": telemetry,
        "recommendations": recommendations,
        "pipeline_status": pipeline_status,
    }

    return {
        "manager_report": report,
        "pipeline_status": pipeline_status,
        "current_agent": "manager",
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"Manager Report for {company}:\n"
                    f"  Pipeline: {pipeline_status.upper()}\n"
                    f"  Qualification: {summary['qualification_score']}/100\n"
                    f"  Advance: {'YES ✓' if summary['should_advance'] else 'NO — nurture'}\n"
                    f"  Recommendations: {'; '.join(recommendations[:3]) if recommendations else 'None'}"
                ),
            }
        ],
    }


async def _generate_recommendations(
    summary: dict[str, Any],
    telemetry: dict[str, Any],
    errors: list[str],
    tenant_id: str,
) -> list[str]:
    """Use LLM to generate workflow optimization recommendations."""
    groq = GroqClient()
    prompt = (
        "You are a sales pipeline optimization expert for the Tanzanian market.\n"
        "Analyze this pipeline execution and provide 3-5 actionable recommendations.\n\n"
        f"Pipeline summary:\n{json.dumps(summary, indent=2)}\n\n"
        f"Telemetry:\n{json.dumps(telemetry, indent=2)}\n\n"
        f"Errors encountered: {errors}\n\n"
        "Focus on:\n"
        "- What went well and should be repeated\n"
        "- What needs improvement\n"
        "- Specific next actions for the sales team\n"
        "- Tanzania-specific business culture tips\n\n"
        "Return a JSON array of recommendation strings."
    )

    try:
        raw = await groq.chat(
            [{"role": "user", "content": prompt}],
            json_mode=True,
            tenant_id=tenant_id,
        )
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "recommendations" in result:
            return result["recommendations"]
        return ["Review pipeline results and adjust outreach strategy"]
    except Exception as e:
        logger.warning("Manager recommendations failed: %s", e)
        recommendations = []
        if summary.get("qualification_score", 0) < 50:
            recommendations.append("Lead needs more nurturing — send value content before re-qualifying")
        if summary.get("enrichment_confidence", 0) < 0.5:
            recommendations.append("Low enrichment confidence — try alternative data sources")
        if errors:
            recommendations.append(f"Fix {len(errors)} pipeline errors to improve reliability")
        if not recommendations:
            recommendations.append("Pipeline completed successfully — continue with standard follow-up")
        return recommendations


async def manager_error_handler(state: AgentState) -> dict[str, Any]:
    """Handle errors and decide whether to retry or escalate."""
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)
    current_agent = state.get("current_agent", "unknown")

    if retry_count >= MAX_RETRIES:
        return {
            "pipeline_status": "failed",
            "manager_report": {
                "phase": "error_handler",
                "action": "escalate",
                "reason": f"Max retries ({MAX_RETRIES}) exceeded for {current_agent}",
                "errors": errors,
                "timestamp": time.time(),
            },
            "current_agent": "manager",
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        f"Manager: Pipeline FAILED — max retries exceeded for {current_agent}. "
                        f"Escalating to human review. Errors: {'; '.join(errors[-3:])}"
                    ),
                }
            ],
        }

    return {
        "retry_count": retry_count + 1,
        "pipeline_status": "degraded",
        "manager_report": {
            "phase": "error_handler",
            "action": "retry",
            "retry_number": retry_count + 1,
            "failed_agent": current_agent,
            "timestamp": time.time(),
        },
        "current_agent": "manager",
        "messages": [
            {
                "role": "assistant",
                "content": (
                    f"Manager: Retrying {current_agent} "
                    f"(attempt {retry_count + 1}/{MAX_RETRIES})"
                ),
            }
        ],
    }
