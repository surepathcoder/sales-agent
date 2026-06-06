"""Deal schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import DealStage, PaymentTerms
from app.schemas.common import ORMBase


class DealCreate(BaseModel):
    lead_id: uuid.UUID
    deal_name: str = Field(min_length=1, max_length=255)
    value: Decimal = Field(gt=0)
    currency: str = "TZS"
    probability: int = Field(default=10, ge=0, le=100)
    stage: DealStage = DealStage.PROSPECTING
    expected_close_date: datetime | None = None
    contact_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    payment_terms: PaymentTerms = PaymentTerms.DAYS_30


class DealUpdate(BaseModel):
    deal_name: str | None = None
    value: Decimal | None = Field(default=None, gt=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    stage: DealStage | None = None
    expected_close_date: datetime | None = None
    loss_reason: str | None = None


class DealResponse(ORMBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    deal_name: str
    value: Decimal
    currency: str
    stage: DealStage
    probability: int
    expected_close_date: datetime
    actual_close_date: datetime | None
    created_at: datetime
    updated_at: datetime
