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

@router.get("/{world_id}/planning-boards", response_model=PlanningBoardListResponse)
def list_planning_boards(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> PlanningBoardListResponse:
    boards = svc.list_planning_boards(world_id)
    if boards is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return PlanningBoardListResponse(boards=boards)


@router.post(
    "/{world_id}/planning-boards",
    response_model=PlanningBoardRead,
    status_code=status.HTTP_201_CREATED,
)
def create_planning_board(
    world_id: UUID,
    body: PlanningBoardCreate,
    svc: WorldService = Depends(get_world_service),
) -> PlanningBoardRead:
    try:
        return svc.create_planning_board(world_id, body)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.post(
    "/{world_id}/planning-boards/{board_id}/cards",
    response_model=PlanningCardRead,
    status_code=status.HTTP_201_CREATED,
)
def create_planning_card(
    world_id: UUID,
    board_id: UUID,
    body: PlanningCardCreate,
    svc: WorldService = Depends(get_world_service),
) -> PlanningCardRead:
    try:
        return svc.create_planning_card(world_id, board_id, body)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World or board not found")
