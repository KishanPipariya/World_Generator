from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

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
    description: str = Field(default="", max_length=5000)
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
