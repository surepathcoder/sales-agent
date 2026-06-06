"""Shared schema types."""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int


class MessageResponse(BaseModel):
    message: str
    message_sw: str | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str = "queued"
    message: str = "Job queued successfully"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TargetCriteria(BaseModel):
    industries: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    company_sizes: list[str] = Field(default_factory=list)
    min_lead_score: int = 0
    max_results: int = Field(default=50, le=500)
    # Scraping sources per user entry
    sources: list[str] = Field(
        default_factory=lambda: ["google_maps", "web"],
        description="google_maps, facebook, instagram, web, brela",
    )
    search_query: str | None = Field(
        default=None, description="Free-text search for maps/social/web"
    )


class TimestampSchema(ORMBase):
    created_at: datetime
    updated_at: datetime | None = None
