"""Redis-backed agent job progress with incremental event log."""

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

JOB_TTL_SECONDS = 3600
MAX_EVENTS = 50


async def get_job(job_id: str) -> dict | None:
  settings = get_settings()
  try:
    r = aioredis.from_url(settings.redis_url_str, decode_responses=True)
    raw = await r.get(f"agent_job:{job_id}")
    await r.aclose()
    if raw:
      return json.loads(raw)
  except Exception as e:
    logger.warning("Redis job read failed: %s", e)
  return None


async def update_job(
  job_id: str,
  status: str,
  *,
  data: dict | None = None,
  event: str | None = None,
  event_sw: str | None = None,
) -> None:
  """Merge job state and append optional bilingual progress event."""
  settings = get_settings()
  try:
    r = aioredis.from_url(settings.redis_url_str, decode_responses=True)
    key = f"agent_job:{job_id}"
    existing: dict = {}
    raw = await r.get(key)
    if raw:
      existing = json.loads(raw)

    events: list[dict] = list(existing.get("events", []))
    if event:
      events.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "message": event,
        "message_sw": event_sw or event,
      })
      events = events[-MAX_EVENTS:]

    payload = {
      **existing,
      "job_id": job_id,
      "status": status,
      **(data or {}),
      "events": events,
      "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await r.setex(key, JOB_TTL_SECONDS, json.dumps(payload))
    await r.aclose()
  except Exception as e:
    logger.warning("Redis job update failed: %s", e)
