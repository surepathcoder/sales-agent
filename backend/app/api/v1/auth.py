"""Authentication endpoints: register, login, refresh, NIDA."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.common import TokenResponse
from app.schemas.user import (
    AuthResponse,
    LoginRequest,
    NIDAVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from app.schemas.tenant import TenantResponse
from app.services.auth_service import AuthService
from app.utils.phone import normalize_tz_phone

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        data.phone = normalize_tz_phone(data.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"en": str(e), "sw": "Nambari ya simu si sahihi"}) from e

    auth_svc = AuthService(db)
    try:
        user, tenant = await auth_svc.register(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"en": str(e)}) from e

    access, refresh = auth_svc.create_tokens(user)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant),
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    auth_svc = AuthService(db)
    user = await auth_svc.authenticate(data.email, data.password, data.tenant_slug)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"en": "Invalid credentials", "sw": "Taarifa za kuingia si sahihi"},
        )
    pair = await auth_svc.get_user_with_tenant(user.id)
    if not pair:
        raise HTTPException(status_code=404)
    user, tenant = pair
    access, refresh = auth_svc.create_tokens(user)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    auth_svc = AuthService(db)
    payload = auth_svc.decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = uuid.UUID(payload["sub"])
    pair = await auth_svc.get_user_with_tenant(user_id)
    if not pair:
        raise HTTPException(status_code=404)
    user, _ = pair
    access, refresh = auth_svc.create_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/nida/verify", response_model=UserResponse)
async def verify_nida(
    data: NIDAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> UserResponse:
    auth_svc = AuthService(db)
    pair = await auth_svc.get_user_with_tenant(user_id)
    if not pair:
        raise HTTPException(status_code=404)
    user, _ = pair
    try:
        user = await auth_svc.verify_nida_mock(user, data.nida_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return UserResponse.model_validate(user)
