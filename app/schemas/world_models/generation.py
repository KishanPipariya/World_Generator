from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.world_models.core import EntityRead, RelationshipRead
from app.schemas.world_models.timeline import TimelineEventRead

if TYPE_CHECKING:
    from app.schemas.world_models.campaign import LoreNoteRead

class AgenticGenerateRequest(BaseModel):
    instruction: str = Field(
        ...,
        max_length=2000,
        description="Instruction for the LLM, e.g. 'Generate 3 major cities for the northern continent.'",
    )
    save_as_entity_type: str | None = Field(
        default=None, description="If provided, the result will be saved as an entity of this type."
    )
    save_as_name: str | None = Field(
        default=None, description="The name of the entity to save. Required if save_as_entity_type is provided."
    )


class AgenticGenerateResponse(BaseModel):
    world_id: UUID
    instruction: str
    content: str = Field(..., max_length=20000)
    entity_id: UUID | None = None
    suggestion_id: UUID | None = None


ExportPreset = Literal[
    "full_bible",
    "character_dossier",
    "faction_brief",
    "location_gazetteer",
    "timeline_only",
    "obsidian",
    "player_handout",
    "session_brief",
    "dm_campaign_brief",
]


class GenerationSuggestionCreate(BaseModel):
    instruction: str = Field(..., max_length=2000)
    content: str = Field(..., max_length=20000)
    suggested_name: str | None = Field(default=None, max_length=200)
    suggested_type: str | None = Field(default=None, max_length=100)


class GenerationSuggestionRead(GenerationSuggestionCreate):
    id: UUID
    world_id: UUID
    status: Literal["pending", "accepted", "discarded"]
    created_at: datetime
    candidate_kind: Literal["entity", "relationship", "timeline_event", "lore_note"] | None = None
    source_type: Literal["draft", "generation", "session", "dm"] | None = None
    source_id: UUID | None = None
    source_excerpt: str | None = None
    payload: dict[str, object] | None = None

    model_config = {"from_attributes": True}


class GenerationSuggestionListResponse(BaseModel):
    suggestions: list[GenerationSuggestionRead]


class SuggestionApplyRequest(BaseModel):
    mode: Literal[
        "create_entity",
        "append_to_entity",
        "replace_entity",
        "discard",
        "create_relationship",
        "create_timeline_event",
        "create_lore_note",
    ]
    entity_id: UUID | None = None
    name: str | None = Field(default=None, max_length=200)
    entity_type: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=20000)


class SuggestionApplyResponse(BaseModel):
    suggestion: GenerationSuggestionRead
    entity: EntityRead | None = None
    relationship: RelationshipRead | None = None
    timeline_event: TimelineEventRead | None = None
    lore_note: LoreNoteRead | None = None
