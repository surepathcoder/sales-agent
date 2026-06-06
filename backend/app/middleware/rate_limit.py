"""Tier-based rate limiting via Redis sliding window."""

import time

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.config import get_settings

PLAN_LIMITS = {
    "free": 60,
    "starter": 300,
    "growth": 1000,
    "enterprise": 5000,
}


class RateLimitMiddleware:
    """Applied as dependency or inline check per route."""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = redis.from_url(settings.redis_url_str, decode_responses=True)
        return self._redis

    async def check(self, request: Request, plan_type: str = "free") -> None:
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            return

        limit = PLAN_LIMITS.get(plan_type, 60)
        key = f"rate:{tenant_id}:{int(time.time() // 60)}"
        try:
            r = await self.get_redis()
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "en": "Rate limit exceeded. Please upgrade your plan.",
                        "sw": "Kikomo cha maombi kimefikiwa. Tafadhali boresha mpango wako.",
                    },
                )
        except HTTPException:
            raise
        except Exception:
            return


rate_limiter = RateLimitMiddleware()
