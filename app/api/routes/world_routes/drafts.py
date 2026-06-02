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

@router.post("/{world_id}/passage-check", response_model=PassageCheckResponse)
def passage_check(
    world_id: UUID,
    body: PassageCheckRequest,
    svc: WorldService = Depends(get_world_service),
) -> PassageCheckResponse:
    result = svc.passage_check(world_id, body.passage)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return result


@router.get("/{world_id}/drafts", response_model=DraftListResponse)
def list_drafts(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> DraftListResponse:
    drafts = svc.list_drafts(world_id)
    if drafts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return DraftListResponse(drafts=drafts)


@router.post("/{world_id}/drafts", response_model=DraftRead, status_code=status.HTTP_201_CREATED)
def create_draft(
    world_id: UUID,
    body: DraftCreate,
    svc: WorldService = Depends(get_world_service),
) -> DraftRead:
    try:
        return svc.create_draft(world_id, body)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.get("/{world_id}/drafts/{draft_id}", response_model=DraftRead)
def get_draft(
    world_id: UUID,
    draft_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> DraftRead:
    draft = svc.get_draft(world_id, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.patch("/{world_id}/drafts/{draft_id}", response_model=DraftRead)
def update_draft(
    world_id: UUID,
    draft_id: UUID,
    body: DraftUpdate,
    svc: WorldService = Depends(get_world_service),
) -> DraftRead:
    draft = svc.update_draft(world_id, draft_id, body)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.delete("/{world_id}/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    world_id: UUID,
    draft_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_draft(world_id, draft_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")


@router.post("/{world_id}/drafts/{draft_id}/check", response_model=PassageCheckResponse)
def check_draft(
    world_id: UUID,
    draft_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> PassageCheckResponse:
    result = svc.check_draft(world_id, draft_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return result


@router.post("/{world_id}/drafts/{draft_id}/extract", response_model=DraftExtractionResponse)
def extract_draft_excerpt(
    world_id: UUID,
    draft_id: UUID,
    body: DraftExtractionRequest,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> DraftExtractionResponse:
    try:
        result = svc.extract_draft_excerpt(
            world_id=world_id,
            draft_id=draft_id,
            excerpt=body.excerpt,
            instruction=body.instruction,
            max_candidates=body.max_candidates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return result


@router.post("/{world_id}/drafts/{draft_id}/extract/preview", response_model=DraftExtractionPreviewResponse)
def preview_draft_extraction(
    world_id: UUID,
    draft_id: UUID,
    body: DraftExtractionRequest,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> DraftExtractionPreviewResponse:
    try:
        result = svc.preview_draft_extraction(
            world_id=world_id,
            draft_id=draft_id,
            excerpt=body.excerpt,
            instruction=body.instruction,
            max_candidates=body.max_candidates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return result


@router.post("/{world_id}/drafts/{draft_id}/extract/queue", response_model=DraftExtractionResponse)
def queue_draft_extraction(
    world_id: UUID,
    draft_id: UUID,
    body: DraftExtractionQueueRequest,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> DraftExtractionResponse:
    try:
        result = svc.queue_draft_extraction(
            world_id=world_id,
            draft_id=draft_id,
            excerpt=body.excerpt,
            instruction=body.instruction,
            candidates=body.candidates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return result
