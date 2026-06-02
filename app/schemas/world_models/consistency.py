from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

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
