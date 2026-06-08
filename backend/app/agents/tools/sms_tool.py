"""SMS sender — Mock integration for Tanzanian telecom networks (Vodacom, Airtel, Tigo)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def send_sms_message(
  to: str,
  message: str,
  tenant_id: str = "system",
) -> dict[str, Any]:
  """
  MVP: log SMS to console instead of sending.
  Production: integrate local aggregator (e.g., Beem Africa SMS API).
  """
  logger.info("SMS [%s] to=%s message=%s", tenant_id, to, message)
  return {
    "status": "sent",
    "to": to,
    "message_preview": message[:50],
    "mock": True,
  }
