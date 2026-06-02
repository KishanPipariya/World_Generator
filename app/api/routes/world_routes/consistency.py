# ruff: noqa: F401, I001
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_world_service
from app.schemas.world_models import (
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    CampaignImpactReviewRequest,
    CampaignImpactReviewResponse,
    CampaignSessionCreate,
    CampaignSessionListResponse,
    CampaignSessionRead,
    CampaignSessionUpdate,
    ConsistencyIssueStateListResponse,
    ConsistencyIssueStateRead,
    ConsistencyIssueUpdate,
    ConsistencyReportResponse,
    DemoWorldResponse,
    DraftCreate,
    DraftExtractionPreviewResponse,
    DraftExtractionQueueRequest,
    DraftExtractionRequest,
    DraftExtractionResponse,
    DraftListResponse,
    DraftRead,
    DraftUpdate,
    EntityCreate,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
    ExportPreset,
    FactionClockCreate,
    FactionClockListResponse,
    FactionClockRead,
    FactionClockUpdate,
    GenerateRequest,
    GenerateResponse,
    GenerationSuggestionCreate,
    GenerationSuggestionListResponse,
    GraphViewCreate,
    GraphViewListResponse,
    GraphViewRead,
    LoreNoteCreate,
    LoreNoteListResponse,
    LoreNoteRead,
    LoreNoteUpdate,
    MarkdownExportResponse,
    PassageCheckRequest,
    PassageCheckResponse,
    PlanningBoardCreate,
    PlanningBoardListResponse,
    PlanningBoardRead,
    PlanningCardCreate,
    PlanningCardRead,
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipRead,
    RevisionVersionListResponse,
    SuggestionApplyRequest,
    SuggestionApplyResponse,
    TimelineEventCreate,
    TimelineEventListResponse,
    TimelineEventRead,
    WorldCreate,
    WorldRead,
)
from app.security import check_generation_rate_limit, require_world_access
from app.services.world import WorldService
from app.api.routes.world_helpers import export_markdown_response, filter_suggestions_by_source, list_response, raise_not_found

router = APIRouter(prefix="/worlds", tags=["worlds"], dependencies=[Depends(require_world_access)])

@router.get("/{world_id}/consistency", response_model=ConsistencyReportResponse)
def consistency_report(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> ConsistencyReportResponse:
    report = svc.consistency_report(world_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return report


@router.get("/{world_id}/consistency/issues", response_model=ConsistencyIssueStateListResponse)
def list_consistency_issues(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> ConsistencyIssueStateListResponse:
    issues = svc.list_consistency_issue_states(world_id)
    if issues is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return ConsistencyIssueStateListResponse(issues=issues)


@router.patch("/{world_id}/consistency/issues/{issue_id}", response_model=ConsistencyIssueStateRead)
def update_consistency_issue(
    world_id: UUID,
    issue_id: UUID,
    body: ConsistencyIssueUpdate,
    svc: WorldService = Depends(get_world_service),
) -> ConsistencyIssueStateRead:
    issue = svc.update_consistency_issue_state(world_id, issue_id, body)
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.post(
    "/{world_id}/relationships",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    world_id: UUID,
    body: RelationshipCreate,
    svc: WorldService = Depends(get_world_service),
) -> RelationshipRead:
    try:
        return svc.create_relationship(
            world_id=world_id,
            source_entity_id=body.source_entity_id,
            target_entity_id=body.target_entity_id,
            relation_type=body.relation_type,
            notes=body.notes,
            category=body.category,
            strength=body.strength,
            history=body.history,
            stance=body.stance,
            color=body.color,
            display_priority=body.display_priority,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World or entity not found",
        )


@router.delete(
    "/{world_id}/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_relationship(
    world_id: UUID,
    relationship_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_relationship(world_id, relationship_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
