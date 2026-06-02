from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.world_models.generation import GenerationSuggestionRead

CampaignVisibility = Literal["dm_only", "player_visible", "discovered", "redacted"]
LoreTruthState = Literal["true", "false", "partial", "unknown"]
LoreSubjectType = Literal["world", "entity", "relationship", "timeline_event", "session"]


class CampaignSessionCreate(BaseModel):
    session_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    played_date: str | None = Field(default=None, max_length=120)
    in_world_date: str | None = Field(default=None, max_length=120)
    recap: str = Field(default="", max_length=20000)
    player_actions: str = Field(default="", max_length=20000)
    consequences: str = Field(default="", max_length=20000)
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_relationship_ids: list[UUID] = Field(default_factory=list)
    linked_timeline_event_ids: list[UUID] = Field(default_factory=list)


class CampaignSessionUpdate(BaseModel):
    session_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    played_date: str | None = Field(default=None, max_length=120)
    in_world_date: str | None = Field(default=None, max_length=120)
    recap: str | None = Field(default=None, max_length=20000)
    player_actions: str | None = Field(default=None, max_length=20000)
    consequences: str | None = Field(default=None, max_length=20000)
    linked_entity_ids: list[UUID] | None = None
    linked_relationship_ids: list[UUID] | None = None
    linked_timeline_event_ids: list[UUID] | None = None


class CampaignSessionRead(CampaignSessionCreate):
    id: UUID
    world_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignSessionListResponse(BaseModel):
    sessions: list[CampaignSessionRead]


class LoreNoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(default="", max_length=20000)
    subject_type: LoreSubjectType = "world"
    subject_id: UUID | None = None
    visibility: CampaignVisibility = "dm_only"
    truth_state: LoreTruthState = "unknown"
    reveal_condition: str | None = Field(default=None, max_length=1000)
    handout_text: str | None = Field(default=None, max_length=20000)


class LoreNoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=20000)
    subject_type: LoreSubjectType | None = None
    subject_id: UUID | None = None
    visibility: CampaignVisibility | None = None
    truth_state: LoreTruthState | None = None
    reveal_condition: str | None = Field(default=None, max_length=1000)
    handout_text: str | None = Field(default=None, max_length=20000)


class LoreNoteRead(LoreNoteCreate):
    id: UUID
    world_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoreNoteListResponse(BaseModel):
    notes: list[LoreNoteRead]


class FactionClockCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    linked_entity_id: UUID | None = None
    segments: int = Field(default=6, ge=1, le=20)
    filled_segments: int = Field(default=0, ge=0, le=20)
    stakes: str = Field(default="", max_length=5000)
    status: Literal["active", "paused", "completed", "failed"] = "active"
    linked_session_ids: list[UUID] = Field(default_factory=list)
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_relationship_ids: list[UUID] = Field(default_factory=list)
    linked_timeline_event_ids: list[UUID] = Field(default_factory=list)


class FactionClockUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    linked_entity_id: UUID | None = None
    segments: int | None = Field(default=None, ge=1, le=20)
    filled_segments: int | None = Field(default=None, ge=0, le=20)
    stakes: str | None = Field(default=None, max_length=5000)
    status: Literal["active", "paused", "completed", "failed"] | None = None
    linked_session_ids: list[UUID] | None = None
    linked_entity_ids: list[UUID] | None = None
    linked_relationship_ids: list[UUID] | None = None
    linked_timeline_event_ids: list[UUID] | None = None


class FactionClockRead(FactionClockCreate):
    id: UUID
    world_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FactionClockListResponse(BaseModel):
    clocks: list[FactionClockRead]


class CampaignImpactReviewRequest(BaseModel):
    instruction: str | None = Field(default=None, max_length=2000)


class CampaignImpactReviewResponse(BaseModel):
    suggestion: GenerationSuggestionRead
