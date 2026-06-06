"""
Tenant context middleware — extracts tenant_id from JWT or x-tenant-id header.

Injects tenant_id, user_id, and role into request.state for downstream handlers.
All tenant-scoped queries MUST use request.state.tenant_id.
"""

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/billing/webhook",
    "/api/v1/webhooks",
    "/metrics",
}


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        request.state.tenant_id = None
        request.state.user_id = None
        request.state.user_role = None

        path = request.url.path
        is_public = any(path.startswith(p) for p in PUBLIC_PATHS)

        # Optional header override (for service-to-service)
        header_tenant = request.headers.get("x-tenant-id")
        if header_tenant:
            request.state.tenant_id = header_tenant

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token, settings.secret_key, algorithms=[settings.algorithm]
                )
                request.state.user_id = payload.get("sub")
                request.state.tenant_id = payload.get("tenant_id") or request.state.tenant_id
                request.state.user_role = payload.get("role")
            except JWTError:
                if not is_public:
                    pass  # Let route dependencies raise 401

        response = await call_next(request)
        return response
