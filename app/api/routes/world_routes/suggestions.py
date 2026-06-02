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

@router.get("/{world_id}/suggestions", response_model=GenerationSuggestionListResponse)
def list_suggestions(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> GenerationSuggestionListResponse:
    suggestions = svc.list_generation_suggestions(world_id)
    if suggestions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return GenerationSuggestionListResponse(
        suggestions=[suggestion for suggestion in suggestions if suggestion.source_type != "dm"]
    )


@router.post(
    "/{world_id}/suggestions",
    response_model=AgenticGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion(
    world_id: UUID,
    body: GenerationSuggestionCreate,
    svc: WorldService = Depends(get_world_service),
) -> AgenticGenerateResponse:
    try:
        suggestion = svc.create_generation_suggestion(
            world_id=world_id,
            instruction=body.instruction,
            content=body.content,
            suggested_name=body.suggested_name,
            suggested_type=body.suggested_type,
        )
        return AgenticGenerateResponse(
            world_id=world_id,
            instruction=body.instruction,
            content=body.content,
            suggestion_id=suggestion.id,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.post("/{world_id}/suggestions/{suggestion_id}/apply", response_model=SuggestionApplyResponse)
def apply_suggestion(
    world_id: UUID,
    suggestion_id: UUID,
    body: SuggestionApplyRequest,
    svc: WorldService = Depends(get_world_service),
) -> SuggestionApplyResponse:
    try:
        result = svc.apply_generation_suggestion(
            world_id=world_id,
            suggestion_id=suggestion_id,
            mode=body.mode,
            entity_id=body.entity_id,
            name=body.name,
            entity_type=body.entity_type,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion or entity not found")
    suggestion, entity, relationship, timeline_event, lore_note = result
    return SuggestionApplyResponse(
        suggestion=suggestion,
        entity=entity,
        relationship=relationship,
        timeline_event=timeline_event,
        lore_note=lore_note,
    )
