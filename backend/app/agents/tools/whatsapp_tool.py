"""WhatsApp message tool with template substitution and rate limiting."""

import asyncio
import re
from typing import Any

from app.integrations.whatsapp_web import WhatsAppWebClient

# Simple in-memory queue rate limiter (production: Redis)
_send_queue: asyncio.Queue | None = None
RATE_LIMIT_SECONDS = 2.0


async def _get_queue() -> asyncio.Queue:
  global _send_queue
  if _send_queue is None:
    _send_queue = asyncio.Queue()
  return _send_queue


def substitute_template(template: str, variables: dict[str, str]) -> str:
  result = template
  for key, value in variables.items():
    result = result.replace(f"{{{{{key}}}}}", value)
    result = result.replace(f"{{{{ {key} }}}}", value)
  return result


async def send_whatsapp_message(
  tenant_id: str,
  to: str,
  message: str,
  template_vars: dict[str, str] | None = None,
) -> dict[str, Any]:
  if template_vars:
    message = substitute_template(message, template_vars)

  await asyncio.sleep(RATE_LIMIT_SECONDS)

  client = WhatsAppWebClient()
  result = await client.send_message(tenant_id, to, message)
  return {
    "status": result.get("status", "queued"),
    "to": to,
    "message_preview": message[:100],
    "delivery_id": result.get("id"),
  }
