"""Lead contact schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ContactType, InfluenceLevel, LanguagePreference
from app.schemas.common import ORMBase


class LeadContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(default="", max_length=100)
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp_number: str = Field(min_length=10, max_length=20)
    contact_type: ContactType = ContactType.MANAGER
    is_decision_maker: bool = False
    influence_level: InfluenceLevel = InfluenceLevel.SECONDARY
    language_preference: LanguagePreference = LanguagePreference.BOTH


class LeadContactResponse(ORMBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    tenant_id: uuid.UUID
    first_name: str
    last_name: str
    title: str | None
    email: str | None
    phone: str | None
    whatsapp_number: str
    contact_type: ContactType
    is_decision_maker: bool
    influence_level: InfluenceLevel
    language_preference: LanguagePreference
    created_at: datetime
    updated_at: datetime
