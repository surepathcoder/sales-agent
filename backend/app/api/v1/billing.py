"""Billing and mobile money endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.enums import PaymentMethod
from app.services.billing_service import BillingService

router = APIRouter()


class TopUpRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    phone_number: str


class TransactionResponse(BaseModel):
    id: uuid.UUID
    payment_reference: str
    amount: Decimal
    status: str

    class Config:
        from_attributes = True


@router.post("/top-up", response_model=TransactionResponse)
async def top_up(
    data: TopUpRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    svc = BillingService(db, tenant_id)
    txn = await svc.initiate_top_up(data.amount, data.payment_method, data.phone_number)
    return TransactionResponse.model_validate(txn)


@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Idempotent payment callback from M-Pesa/Tigo/Airtel."""
    body = await request.json()
    tenant_id = body.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")

    svc = BillingService(db, uuid.UUID(tenant_id))
    txn = await svc.process_webhook(
        provider=provider,
        payment_reference=body.get("payment_reference", ""),
        status=body.get("status", "failed"),
        amount=Decimal(str(body.get("amount", 0))) if body.get("amount") else None,
    )
    if not txn:
        raise HTTPException(status_code=404)
    return {"status": txn.status.value, "reference": txn.payment_reference}


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    svc = BillingService(db, tenant_id)
    txns = await svc.list_transactions()
    return [TransactionResponse.model_validate(t) for t in txns]
