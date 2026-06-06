"""Email sender — Resend.com integration stub for MVP."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def send_email(
  to: str,
  subject: str,
  body: str,
  tenant_id: str = "",
) -> dict[str, Any]:
  """
  MVP: log email instead of sending.
  Production: integrate Resend.com API.
  """
  logger.info("Email [%s] to=%s subject=%s", tenant_id, to, subject)
  return {
    "status": "queued",
    "to": to,
    "subject": subject,
    "mock": True,
  }
