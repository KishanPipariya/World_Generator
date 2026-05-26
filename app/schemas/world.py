from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WorldCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    tone: str | None = Field(default=None, max_length=200)
    era_notes: str | None = Field(default=None, max_length=5000)
    seed: str | None = Field(default=None, max_length=200)


class WorldRead(BaseModel):
    id: UUID
    title: str
    tone: str | None
    era_notes: str | None
    seed: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    section: Literal["glossary", "timeline_hint"] | None = Field(
        default=None,
        description="Which stub to generate; defaults to glossary.",
    )


class GenerateResponse(BaseModel):
    world_id: UUID
    section: Literal["glossary", "timeline_hint"]
    content: str


class EntityCreate(BaseModel):
    name: str = Field(..., max_length=200)
    entity_type: str = Field(..., max_length=100)
    description: str
    structured_fields: dict[str, str] = Field(default_factory=dict)


class EntityRead(EntityCreate):
    id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    entity_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    structured_fields: dict[str, str] | None = None


class EntityListResponse(BaseModel):
    entities: list[EntityRead]


class RelationshipCreate(BaseModel):
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: str = Field(..., max_length=100)
    notes: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=100)
    strength: int | None = Field(default=None, ge=1, le=5)
    history: str | None = Field(default=None, max_length=5000)
    stance: Literal["alliance", "conflict", "neutral", "unknown"] | None = None
    color: str | None = Field(default=None, max_length=32)
    display_priority: int | None = Field(default=None, ge=0, le=100)


class RelationshipRead(RelationshipCreate):
    id: UUID
    world_id: UUID
    source_entity_name: str
    target_entity_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RelationshipListResponse(BaseModel):
    relationships: list[RelationshipRead]


class MarkdownExportResponse(BaseModel):
    world_id: UUID
    filename: str
    content: str
    preset: str = "full_bible"


class DemoWorldResponse(BaseModel):
    world: WorldRead
    entities: list[EntityRead]
    relationships: list[RelationshipRead]


ConsistencyIssueStatus = Literal["open", "ignored", "resolved", "reopened"]
ConsistencyIssueTargetType = Literal["world", "entity", "relationship"]


class ConsistencyIssue(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    target_type: ConsistencyIssueTargetType | None = None
    entity_id: UUID | None = None
    relationship_id: UUID | None = None
    issue_id: UUID | None = None
    status: ConsistencyIssueStatus | None = None
    note: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None


class ConsistencyReportResponse(BaseModel):
    world_id: UUID
    score: int
    summary: str
    issues: list[ConsistencyIssue]


class ConsistencyIssueUpdate(BaseModel):
    status: ConsistencyIssueStatus | None = None
    note: str | None = Field(default=None, max_length=5000)


class ConsistencyIssueStateRead(BaseModel):
    id: UUID
    world_id: UUID
    fingerprint: str
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    target_type: ConsistencyIssueTargetType
    entity_id: UUID | None = None
    relationship_id: UUID | None = None
    status: ConsistencyIssueStatus
    note: str | None = None
    first_seen: datetime
    last_seen: datetime
    updated_at: datetime


class ConsistencyIssueStateListResponse(BaseModel):
    issues: list[ConsistencyIssueStateRead]


class AgenticGenerateRequest(BaseModel):
    instruction: str = Field(
        ..., description="Instruction for the LLM, e.g. 'Generate 3 major cities for the northern continent.'"
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
    content: str
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
    instruction: str
    content: str
    suggested_name: str | None = Field(default=None, max_length=200)
    suggested_type: str | None = Field(default=None, max_length=100)


class GenerationSuggestionRead(GenerationSuggestionCreate):
    id: UUID
    world_id: UUID
    status: Literal["pending", "accepted", "discarded"]
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationSuggestionListResponse(BaseModel):
    suggestions: list[GenerationSuggestionRead]


class SuggestionApplyRequest(BaseModel):
    mode: Literal["create_entity", "append_to_entity", "replace_entity", "discard"]
    entity_id: UUID | None = None
    name: str | None = Field(default=None, max_length=200)
    entity_type: str | None = Field(default=None, max_length=100)
    description: str | None = None


class SuggestionApplyResponse(BaseModel):
    suggestion: GenerationSuggestionRead
    entity: EntityRead | None = None


class TimelineEventCreate(BaseModel):
    title: str = Field(..., max_length=200)
    event_order: int
    description: str = ""
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


CampaignVisibility = Literal["dm_only", "player_visible", "discovered", "redacted"]
LoreTruthState = Literal["true", "false", "partial", "unknown"]
LoreSubjectType = Literal["world", "entity", "relationship", "timeline_event", "session"]


class CampaignSessionCreate(BaseModel):
    session_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    played_date: str | None = Field(default=None, max_length=120)
    in_world_date: str | None = Field(default=None, max_length=120)
    recap: str = ""
    player_actions: str = ""
    consequences: str = ""
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_relationship_ids: list[UUID] = Field(default_factory=list)
    linked_timeline_event_ids: list[UUID] = Field(default_factory=list)


class CampaignSessionUpdate(BaseModel):
    session_number: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    played_date: str | None = Field(default=None, max_length=120)
    in_world_date: str | None = Field(default=None, max_length=120)
    recap: str | None = None
    player_actions: str | None = None
    consequences: str | None = None
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
    body: str = ""
    subject_type: LoreSubjectType = "world"
    subject_id: UUID | None = None
    visibility: CampaignVisibility = "dm_only"
    truth_state: LoreTruthState = "unknown"
    reveal_condition: str | None = Field(default=None, max_length=1000)
    handout_text: str | None = None


class LoreNoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    subject_type: LoreSubjectType | None = None
    subject_id: UUID | None = None
    visibility: CampaignVisibility | None = None
    truth_state: LoreTruthState | None = None
    reveal_condition: str | None = Field(default=None, max_length=1000)
    handout_text: str | None = None


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
    stakes: str = ""
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
    stakes: str | None = None
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
    instruction: str | None = Field(default=None, max_length=1000)


class CampaignImpactReviewResponse(BaseModel):
    suggestion: GenerationSuggestionRead


GraphLayoutMode = Literal["manual", "force", "type_columns", "faction_clusters", "timeline_order"]


class GraphCamera(BaseModel):
    x: float = 0
    y: float = 0
    zoom: float = 1


class GraphViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    layout_mode: GraphLayoutMode = "manual"
    filters: dict[str, object] = Field(default_factory=dict)
    camera: GraphCamera = Field(default_factory=GraphCamera)
    node_positions: dict[str, dict[str, float]] = Field(default_factory=dict)


class GraphViewRead(GraphViewCreate):
    id: UUID
    world_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GraphViewListResponse(BaseModel):
    views: list[GraphViewRead]


class PlanningBoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    board_type: Literal[
        "arc",
        "chapter",
        "scene",
        "plot_thread",
        "quest",
        "front",
        "session_prep",
        "custom",
    ] = "plot_thread"


class PlanningBoardRead(PlanningBoardCreate):
    id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanningCardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    lane: str = Field(default="Backlog", max_length=100)
    position: int = 0
    entity_links: list[UUID] = Field(default_factory=list)
    relationship_links: list[UUID] = Field(default_factory=list)
    timeline_event_links: list[UUID] = Field(default_factory=list)


class PlanningCardRead(PlanningCardCreate):
    id: UUID
    board_id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanningBoardDetail(PlanningBoardRead):
    cards: list[PlanningCardRead] = Field(default_factory=list)


class PlanningBoardListResponse(BaseModel):
    boards: list[PlanningBoardDetail]


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
    body: str = Field(..., min_length=1, max_length=50000)
    status: Literal["draft", "revising", "ready", "archived"] = "draft"
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_relationship_ids: list[UUID] = Field(default_factory=list)
    linked_timeline_event_ids: list[UUID] = Field(default_factory=list)


class DraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=50000)
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
