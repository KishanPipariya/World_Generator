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
    entity_type: str = Field(..., max_length=100) # e.g. "City", "Faction", "Character"
    description: str


class EntityRead(EntityCreate):
    id: UUID
    world_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


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
