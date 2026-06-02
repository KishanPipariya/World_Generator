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

@router.post("/{world_id}/agentic-generate", response_model=AgenticGenerateResponse)
def agentic_generate(
    world_id: UUID,
    body: AgenticGenerateRequest,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> AgenticGenerateResponse:
    try:
        content, entity_id = svc.agentic_generate(
            world_id=world_id,
            instruction=body.instruction,
            save_as_type=body.save_as_entity_type,
            save_as_name=body.save_as_name,
        )
        suggestion_id = None
        if entity_id is None:
            suggestion = svc.create_generation_suggestion(
                world_id=world_id,
                instruction=body.instruction,
                content=content,
                suggested_name=body.save_as_name,
                suggested_type=body.save_as_entity_type,
            )
            suggestion_id = suggestion.id
        return AgenticGenerateResponse(
            world_id=world_id,
            instruction=body.instruction,
            content=content,
            entity_id=entity_id,
            suggestion_id=suggestion_id,
        )
    except ValueError as e:
        if str(e) == "World not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
