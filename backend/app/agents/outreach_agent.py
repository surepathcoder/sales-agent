"""Outreach Agent — generates and sends WhatsApp/email messages."""

import logging
from typing import Any

from app.agents.state import AgentState
from app.agents.tools.email_tool import send_email
from app.agents.tools.whatsapp_tool import send_whatsapp_message
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)


async def outreach_node(state: AgentState) -> dict[str, Any]:
  """LangGraph node: generate bilingual message and send via WhatsApp."""
  tenant = state.get("tenant", {})
  tenant_id = tenant.get("tenant_id", "system")
  human_approval = tenant.get("human_approval_required", True)
  lead = state.get("lead", {})
  step_config = state.get("target_criteria", {}).get("step_config", {})

  company = lead.get("company_name", "your company")
  contacts = lead.get("contacts", [])
  contact_name = "Mpendwa"
  whatsapp_to = None

  if contacts:
    c = contacts[0]
    contact_name = c.get("first_name", contact_name)
    whatsapp_to = c.get("whatsapp_number")

  groq = GroqClient()
  message = await groq.generate_outreach_message(
    company_name=company,
    contact_name=contact_name,
    swahili_ratio=step_config.get("swahili_ratio", tenant.get("swahili_preference", 0.5)),
    tone=step_config.get("tone", "professional"),
    tenant_id=tenant_id,
  )

  sent_status = "pending_approval" if human_approval else "sent"
  interaction_log: list[dict[str, Any]] = []

  if not human_approval and whatsapp_to:
    result = await send_whatsapp_message(tenant_id, whatsapp_to, message)
    sent_status = result.get("status", "sent")
    interaction_log.append({
      "channel": "whatsapp",
      "direction": "outbound",
      "content": message,
      "status": sent_status,
    })
  else:
    interaction_log.append({
      "channel": "whatsapp",
      "direction": "outbound",
      "content": message,
      "status": sent_status,
      "requires_approval": True,
    })

  channel = step_config.get("channel", "whatsapp")
  if channel == "email" and contacts and contacts[0].get("email"):
    await send_email(contacts[0]["email"], f"Regarding {company}", message, tenant_id)

  return {
    "sent_message": message,
    "engagement_prediction": 0.35,
    "interaction_log": interaction_log,
    "next_step_recommendation": "Wait 48h then follow up via WhatsApp",
    "current_agent": "outreach",
    "messages": [{"role": "assistant", "content": message}],
  }
