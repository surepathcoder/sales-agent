"""Billing and mobile money — mock M-Pesa for MVP."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import BillingTransaction
from app.models.enums import PaymentMethod, TransactionStatus, TransactionType
from app.models.tenant import Tenant


class BillingService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def initiate_top_up(
        self,
        amount: Decimal,
        payment_method: PaymentMethod,
        phone_number: str,
    ) -> BillingTransaction:
        reference = f"KIJANI-{uuid.uuid4().hex[:12].upper()}"
        txn = BillingTransaction(
            tenant_id=self.tenant_id,
            transaction_type=TransactionType.TOP_UP,
            amount=amount,
            payment_method=payment_method,
            payment_reference=reference,
            status=TransactionStatus.PENDING,
            extra_metadata={"phone": phone_number, "mock": True},
        )
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def process_webhook(
        self,
        provider: str,
        payment_reference: str,
        status: str,
        amount: Decimal | None = None,
    ) -> BillingTransaction | None:
        """Idempotent webhook processing."""
        result = await self.db.execute(
            select(BillingTransaction).where(
                BillingTransaction.payment_reference == payment_reference,
                BillingTransaction.tenant_id == self.tenant_id,
            )
        )
        txn = result.scalar_one_or_none()
        if not txn:
            return None
        if txn.status == TransactionStatus.COMPLETED:
            return txn  # idempotent

        if status == "completed":
            txn.status = TransactionStatus.COMPLETED
            txn.completed_at = datetime.now(timezone.utc)
            await self._credit_wallet(txn.amount)
        elif status == "failed":
            txn.status = TransactionStatus.FAILED

        txn.extra_metadata = {**txn.extra_metadata, "provider": provider}
        return txn

    async def _credit_wallet(self, amount: Decimal) -> None:
        result = await self.db.execute(select(Tenant).where(Tenant.id == self.tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant:
            balance = tenant.settings.get("wallet_balance", 0.0)
            tenant.settings = {
                **tenant.settings,
                "wallet_balance": float(balance) + float(amount),
            }

    async def list_transactions(self, limit: int = 50) -> list[BillingTransaction]:
        result = await self.db.execute(
            select(BillingTransaction)
            .where(BillingTransaction.tenant_id == self.tenant_id)
            .order_by(BillingTransaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
