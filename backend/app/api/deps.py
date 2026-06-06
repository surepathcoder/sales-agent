"""FastAPI dependencies: auth, tenant context, RBAC."""

import uuid
from collections.abc import Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.enums import UserRole


async def get_current_tenant_id(request: Request) -> uuid.UUID:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"en": "Not authenticated", "sw": "Haujathibitishwa"},
        )
    return uuid.UUID(str(tenant_id))


async def get_current_user_id(request: Request) -> uuid.UUID:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"en": "Not authenticated", "sw": "Haujathibitishwa"},
        )
    return uuid.UUID(str(user_id))


async def get_current_role(request: Request) -> str:
    role = getattr(request.state, "user_role", None)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return role


def require_roles(*allowed: UserRole) -> Callable:
    """RBAC decorator for route handlers."""

    async def checker(request: Request) -> None:
        role = getattr(request.state, "user_role", None)
        if not role or role not in [r.value for r in allowed]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"en": "Insufficient permissions", "sw": "Huna ruhusa"},
            )

    return checker


async def verify_access_token(request: Request) -> dict:
    settings = get_settings()
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        return jwt.decode(auth[7:], settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from None


# Re-export get_db for convenience
__all__ = ["get_db", "get_current_tenant_id", "get_current_user_id", "require_roles"]
