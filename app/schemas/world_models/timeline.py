from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TimelineEventCreate(BaseModel):
    title: str = Field(..., max_length=200)
    event_order: int
    description: str = Field(default="", max_length=20000)
    participants: list[UUID] = Field(default_factory=list)
    causes: str | None = Field(default=None, max_length=5000)
    consequences: str | None = Field(default=None, max_length=5000)
    date_label: str | None = Field(default=None, max_length=120)
    era_label: str | None = Field(default=None, max_length=120)
    depends_on: list[UUID] = Field(default_factory=list)


class TimelineEventRead(TimelineEventCreate):
    id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEventListResponse(BaseModel):
    events: list[TimelineEventRead]
