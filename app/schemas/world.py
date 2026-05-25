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


class EntityRead(EntityCreate):
    id: UUID
    world_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    entity_type: str | None = Field(default=None, max_length=100)
    description: str | None = None


class EntityListResponse(BaseModel):
    entities: list[EntityRead]


class RelationshipCreate(BaseModel):
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: str = Field(..., max_length=100)
    notes: str | None = Field(default=None, max_length=5000)


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


class DemoWorldResponse(BaseModel):
    world: WorldRead
    entities: list[EntityRead]
    relationships: list[RelationshipRead]


class ConsistencyIssue(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    entity_id: UUID | None = None
    relationship_id: UUID | None = None


class ConsistencyReportResponse(BaseModel):
    world_id: UUID
    score: int
    summary: str
    issues: list[ConsistencyIssue]


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
