from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.world_models.generation import GenerationSuggestionRead


class RevisionVersionRead(BaseModel):
    id: UUID
    world_id: UUID
    entity_id: UUID | None = None
    subject_type: Literal["entity", "world"]
    field_name: str
    previous_value: str | None = None
    new_value: str | None = None
    source: Literal["manual", "generated", "restore"] = "manual"
    created_at: datetime


class RevisionVersionListResponse(BaseModel):
    versions: list[RevisionVersionRead]


class PassageCheckRequest(BaseModel):
    passage: str = Field(..., min_length=1, max_length=20000)


class PassageCheckIssue(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    entity_id: UUID | None = None


class PassageCheckResponse(BaseModel):
    world_id: UUID
    summary: str
    issues: list[PassageCheckIssue]


class DraftCheckHistoryItem(BaseModel):
    checked_at: datetime
    summary: str
    issues: list[PassageCheckIssue]


class DraftCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=20000)
    status: Literal["draft", "revising", "ready", "archived"] = "draft"
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_relationship_ids: list[UUID] = Field(default_factory=list)
    linked_timeline_event_ids: list[UUID] = Field(default_factory=list)


class DraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=20000)
    status: Literal["draft", "revising", "ready", "archived"] | None = None
    linked_entity_ids: list[UUID] | None = None
    linked_relationship_ids: list[UUID] | None = None
    linked_timeline_event_ids: list[UUID] | None = None


class DraftRead(DraftCreate):
    id: UUID
    world_id: UUID
    check_history: list[DraftCheckHistoryItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DraftListResponse(BaseModel):
    drafts: list[DraftRead]


class DraftExtractionRequest(BaseModel):
    excerpt: str = Field(..., min_length=1, max_length=20000)
    instruction: str | None = Field(default=None, max_length=2000)
    max_candidates: int = Field(default=6, ge=1, le=12)


class DraftExtractionCandidate(BaseModel):
    candidate_kind: Literal["entity", "relationship", "timeline_event", "lore_note"]
    suggested_name: str = Field(..., min_length=1, max_length=200)
    suggested_type: str | None = Field(default=None, max_length=100)
    content: str = Field(..., min_length=1, max_length=20000)
    payload: dict[str, object] = Field(default_factory=dict)


class DraftExtractionPreviewResponse(BaseModel):
    world_id: UUID
    draft_id: UUID
    summary: str
    excerpt: str
    candidates: list[DraftExtractionCandidate]


class DraftExtractionQueueRequest(BaseModel):
    excerpt: str = Field(..., min_length=1, max_length=20000)
    instruction: str | None = Field(default=None, max_length=2000)
    candidates: list[DraftExtractionCandidate] = Field(..., min_length=1)


class DraftExtractionResponse(BaseModel):
    world_id: UUID
    draft_id: UUID
    summary: str
    suggestions: list[GenerationSuggestionRead]
