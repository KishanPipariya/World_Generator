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
    content: str = Field(..., max_length=20000)


class EntityCreate(BaseModel):
    name: str = Field(..., max_length=200)
    entity_type: str = Field(..., max_length=100)
    description: str = Field(..., max_length=20000)
    structured_fields: dict[str, str] = Field(default_factory=dict)


class EntityRead(EntityCreate):
    id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    entity_type: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=20000)
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
