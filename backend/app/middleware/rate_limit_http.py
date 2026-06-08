"""HTTP middleware wrapper for tier-based rate limiting."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.middleware.rate_limit import rate_limiter

SKIP_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc", "/metrics")


class RateLimitHTTPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not any(path.startswith(p) for p in SKIP_PREFIXES):
            plan = getattr(request.state, "plan_type", None) or "free"
            try:
                await rate_limiter.check(request, plan_type=str(plan))
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
        return await call_next(request)
