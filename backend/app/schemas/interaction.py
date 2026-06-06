"""Interaction schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import InteractionChannel, InteractionDirection
from app.schemas.common import ORMBase


class InteractionResponse(ORMBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    contact_id: uuid.UUID
    campaign_id: uuid.UUID | None = None
    channel: InteractionChannel
    direction: InteractionDirection
    content: str
    ai_generated: bool = False
    human_approved: bool | None = None
    extra_metadata: dict[str, Any] | None = None
    created_at: datetime


class ReplyRequest(BaseModel):
    content: str
    use_ai_draft: bool = False


class ApproveOutreachRequest(BaseModel):
  """Approve a pending outreach message and optionally send via WhatsApp."""
  send_now: bool = True
