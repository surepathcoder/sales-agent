"""Authentication: JWT, password hashing, registration."""

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PlanType, TenantStatus, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.user import RegisterRequest
from app.utils.phone import normalize_tz_phone
from app.utils.validators import slugify

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_token(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        role: str,
        expires_delta: timedelta,
        token_type: str = "access",
    ) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role,
            "type": token_type,
            "exp": expire,
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.settings.algorithm)

    def create_tokens(self, user: User) -> tuple[str, str]:
        access = self.create_token(
            user.id,
            user.tenant_id,
            user.role.value,
            timedelta(minutes=self.settings.access_token_expire_minutes),
            "access",
        )
        refresh = self.create_token(
            user.id,
            user.tenant_id,
            user.role.value,
            timedelta(minutes=self.settings.refresh_token_expire_minutes),
            "refresh",
        )
        return access, refresh

    async def register(self, data: RegisterRequest) -> tuple[User, Tenant]:
        base_slug = slugify(data.company_name)
        slug = base_slug
        counter = 1
        while await self._slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        phone = normalize_tz_phone(data.phone)

        tenant = Tenant(
            name=data.company_name,
            slug=slug,
            plan_type=data.plan_type,
            industry_vertical=data.industry_vertical,
            status=TenantStatus.ACTIVE,
            settings={
                "locale": "sw_TZ",
                "timezone": "Africa/Dar_es_Salaam",
                "swahili_preference": 0.5,
                "auto_reply_enabled": True,
                "wallet_balance": 0.0,
            },
        )
        self.db.add(tenant)
        await self.db.flush()

        user = User(
            tenant_id=tenant.id,
            email=data.email.lower(),
            phone=phone,
            password_hash=self.hash_password(data.password),
            role=UserRole.SUPER_ADMIN,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(tenant)
        await self.db.refresh(user)
        return user, tenant

    async def _slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none() is not None

    async def authenticate(self, email: str, password: str, tenant_slug: str | None = None) -> User | None:
        query = select(User).join(Tenant).where(User.email == email.lower())
        if tenant_slug:
            query = query.where(Tenant.slug == tenant_slug)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if user and self.verify_password(password, user.password_hash):
            user.last_active = datetime.now(timezone.utc)
            return user
        return None

    async def get_user_with_tenant(self, user_id: uuid.UUID) -> tuple[User, Tenant] | None:
        result = await self.db.execute(
            select(User, Tenant).join(Tenant).where(User.id == user_id)
        )
        row = result.first()
        if not row:
            return None
        return row[0], row[1]

    def decode_refresh_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token, self.settings.secret_key, algorithms=[self.settings.algorithm]
            )
            if payload.get("type") != "refresh":
                return None
            return payload
        except Exception:
            return None

    async def verify_nida_mock(self, user: User, nida_number: str) -> User:
        """Mock NIDA verification — integrate real API later."""
        from app.utils.crypto import encrypt_field
        from app.utils.validators import validate_nida

        if not validate_nida(nida_number):
            raise ValueError("Invalid NIDA number format")
        user.nida_number = encrypt_field(nida_number)
        user.nida_verified = True
        return user
