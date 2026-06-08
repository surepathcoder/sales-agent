"""Outreach Agent — generates and sends WhatsApp/email/SMS/voice outreach."""

import logging
import json
from typing import Any

from app.agents.state import AgentState
from app.agents.tools.email_tool import send_email
from app.agents.tools.whatsapp_tool import send_whatsapp_message
from app.agents.tools.sms_tool import send_sms_message
from app.agents.tools.voice_tool import generate_voice_note
from app.integrations.groq_client import GroqClient

logger = logging.getLogger(__name__)


async def outreach_node(state: AgentState) -> dict[str, Any]:
  """LangGraph node: generate channel-specific outreach message."""
  tenant = state.get("tenant", {})
  tenant_id = tenant.get("tenant_id", "system")
  human_approval = tenant.get("human_approval_required", True)
  lead = state.get("lead", {})
  step_config = state.get("target_criteria", {}).get("step_config", {})
  channel = step_config.get("channel", "whatsapp")
  sequence_step = step_config.get("sequence_step", 0)

  company = lead.get("company_name", "your company")
  contacts = lead.get("contacts", [])
  contact_name = "Mpendwa"
  whatsapp_to = None
  email_to = None

  if contacts:
    c = contacts[0]
    contact_name = c.get("first_name", contact_name)
    whatsapp_to = c.get("whatsapp_number")
    email_to = c.get("email")

  # AI message generation
  groq = GroqClient()
  raw_result = await groq.generate_outreach_message(
    company_name=company,
    contact_name=contact_name,
    channel=channel,
    research_report=lead.get("ai_insights", {}).get("research_report"),
    sequence_step=sequence_step,
    swahili_ratio=step_config.get("swahili_ratio", tenant.get("swahili_preference", 0.5)),
    tone=step_config.get("tone", "professional"),
    tenant_id=tenant_id,
  )

  # Parse JSON result
  parsed_msg = {}
  try:
    parsed_msg = json.loads(raw_result)
  except Exception:
    pass

  # Extract final texts depending on channel
  email_subject = parsed_msg.get("subject", f"Regarding {company}")
  email_body = parsed_msg.get("body", raw_result)
  
  whatsapp_text = parsed_msg.get("message", raw_result)
  sms_text = parsed_msg.get("message", raw_result)
  voice_script = parsed_msg.get("voice_script", raw_result)

  # Determine standard message log
  if channel == "email":
    message = f"Subject: {email_subject}\n\n{email_body}"
  elif channel == "voice_note":
    message = f"[Voice Script]: {voice_script}"
  elif channel == "sms":
    message = sms_text
  else:
    message = whatsapp_text

  sent_status = "pending_approval" if human_approval else "sent"
  interaction_log: list[dict[str, Any]] = []
  extra_metadata: dict[str, Any] = {
    "channel": channel,
    "sequence_step": sequence_step,
  }

  # Add channel-specific detail metadata
  if channel == "email":
    extra_metadata.update({"email_subject": email_subject, "email_body": email_body})
  elif channel == "voice_note":
    extra_metadata.update({"voice_script": voice_script})

  if not human_approval:
    # Channel dispatch logic
    if channel == "email" and email_to:
      res = await send_email(email_to, email_subject, email_body, tenant_id)
      sent_status = res.get("status", "sent")
    elif channel == "sms" and whatsapp_to:
      res = await send_sms_message(whatsapp_to, sms_text, tenant_id)
      sent_status = res.get("status", "sent")
    elif channel == "voice_note" and whatsapp_to:
      voice_res = await generate_voice_note(voice_script, tenant_id)
      extra_metadata["voice_note_url"] = voice_res.get("url")
      extra_metadata["voice_note_filepath"] = voice_res.get("filepath")
      res = await send_whatsapp_message(
        tenant_id, whatsapp_to, f"[Voice Note] {voice_script}", template_vars={"voice_note_url": voice_res.get("url")}
      )
      sent_status = res.get("status", "sent")
    elif channel == "whatsapp" and whatsapp_to:
      res = await send_whatsapp_message(tenant_id, whatsapp_to, whatsapp_text)
      sent_status = res.get("status", "sent")

    interaction_log.append({
      "channel": channel,
      "direction": "outbound",
      "content": message,
      "status": sent_status,
      "metadata": extra_metadata,
    })
  else:
    # If human approval is required, voice note files are still generated for preview!
    if channel == "voice_note":
      voice_res = await generate_voice_note(voice_script, tenant_id)
      extra_metadata["voice_note_url"] = voice_res.get("url")
      extra_metadata["voice_note_filepath"] = voice_res.get("filepath")
      
    interaction_log.append({
      "channel": channel,
      "direction": "outbound",
      "content": message,
      "status": sent_status,
      "requires_approval": True,
      "metadata": extra_metadata,
    })

  return {
    "sent_message": message,
    "engagement_prediction": 0.45 if channel == "whatsapp" or channel == "voice_note" else 0.25,
    "interaction_log": interaction_log,
    "next_step_recommendation": f"Wait 48h then follow up via {channel}",
    "current_agent": "outreach",
    "messages": [{"role": "assistant", "content": message}],
    "extra_metadata": extra_metadata,
  }
