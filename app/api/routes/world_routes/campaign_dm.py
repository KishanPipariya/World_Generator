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
from app.api.routes.world_routes.lore import (
    create_faction_clock,
    create_lore_note,
    delete_faction_clock,
    delete_lore_note,
    list_faction_clocks,
    list_lore_notes,
    update_faction_clock,
    update_lore_note,
)
from app.api.routes.world_helpers import export_markdown_response, filter_suggestions_by_source, list_response, raise_not_found

router = APIRouter(prefix="/worlds", tags=["worlds"], dependencies=[Depends(require_world_access)])

@router.get("/{world_id}/campaign-sessions", response_model=CampaignSessionListResponse)
def list_campaign_sessions(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionListResponse:
    sessions = svc.list_campaign_sessions(world_id)
    if sessions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return CampaignSessionListResponse(sessions=sessions)


@router.post(
    "/{world_id}/campaign-sessions",
    response_model=CampaignSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign_session(
    world_id: UUID,
    body: CampaignSessionCreate,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionRead:
    try:
        return svc.create_campaign_session(world_id, body)
    except ValueError as exc:
        detail = "World not found" if str(exc) == "World not found" else str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.patch("/{world_id}/campaign-sessions/{session_id}", response_model=CampaignSessionRead)
def update_campaign_session(
    world_id: UUID,
    session_id: UUID,
    body: CampaignSessionUpdate,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionRead:
    try:
        session = svc.update_campaign_session(world_id, session_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign session not found")
    return session


@router.delete("/{world_id}/campaign-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign_session(
    world_id: UUID,
    session_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_campaign_session(world_id, session_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign session not found")


@router.post(
    "/{world_id}/campaign-sessions/{session_id}/impact-review",
    response_model=CampaignImpactReviewResponse,
)
def create_campaign_impact_review(
    world_id: UUID,
    session_id: UUID,
    body: CampaignImpactReviewRequest | None = None,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> CampaignImpactReviewResponse:
    suggestion = svc.create_session_impact_review(
        world_id, session_id, body.instruction if body else None
    )
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign session not found")
    return CampaignImpactReviewResponse(suggestion=suggestion)


@router.get("/{world_id}/dm/sessions", response_model=CampaignSessionListResponse)
def list_dm_sessions(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionListResponse:
    return list_campaign_sessions(world_id, svc)


@router.post(
    "/{world_id}/dm/sessions",
    response_model=CampaignSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dm_session(
    world_id: UUID,
    body: CampaignSessionCreate,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionRead:
    return create_campaign_session(world_id, body, svc)


@router.patch("/{world_id}/dm/sessions/{session_id}", response_model=CampaignSessionRead)
def update_dm_session(
    world_id: UUID,
    session_id: UUID,
    body: CampaignSessionUpdate,
    svc: WorldService = Depends(get_world_service),
) -> CampaignSessionRead:
    return update_campaign_session(world_id, session_id, body, svc)


@router.delete("/{world_id}/dm/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dm_session(
    world_id: UUID,
    session_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    return delete_campaign_session(world_id, session_id, svc)


@router.post(
    "/{world_id}/dm/sessions/{session_id}/impact-review",
    response_model=CampaignImpactReviewResponse,
)
def create_dm_impact_review(
    world_id: UUID,
    session_id: UUID,
    body: CampaignImpactReviewRequest | None = None,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> CampaignImpactReviewResponse:
    return create_campaign_impact_review(world_id, session_id, body, _rate_limited, svc)


@router.get("/{world_id}/dm/lore-notes", response_model=LoreNoteListResponse)
def list_dm_lore_notes(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteListResponse:
    return list_lore_notes(world_id, svc)


@router.post("/{world_id}/dm/lore-notes", response_model=LoreNoteRead, status_code=status.HTTP_201_CREATED)
def create_dm_lore_note(
    world_id: UUID,
    body: LoreNoteCreate,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteRead:
    return create_lore_note(world_id, body, svc)


@router.patch("/{world_id}/dm/lore-notes/{note_id}", response_model=LoreNoteRead)
def update_dm_lore_note(
    world_id: UUID,
    note_id: UUID,
    body: LoreNoteUpdate,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteRead:
    return update_lore_note(world_id, note_id, body, svc)


@router.delete("/{world_id}/dm/lore-notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dm_lore_note(
    world_id: UUID,
    note_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    return delete_lore_note(world_id, note_id, svc)


@router.get("/{world_id}/dm/faction-clocks", response_model=FactionClockListResponse)
def list_dm_faction_clocks(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockListResponse:
    return list_faction_clocks(world_id, svc)


@router.post(
    "/{world_id}/dm/faction-clocks",
    response_model=FactionClockRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dm_faction_clock(
    world_id: UUID,
    body: FactionClockCreate,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockRead:
    return create_faction_clock(world_id, body, svc)


@router.patch("/{world_id}/dm/faction-clocks/{clock_id}", response_model=FactionClockRead)
def update_dm_faction_clock(
    world_id: UUID,
    clock_id: UUID,
    body: FactionClockUpdate,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockRead:
    return update_faction_clock(world_id, clock_id, body, svc)


@router.delete("/{world_id}/dm/faction-clocks/{clock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dm_faction_clock(
    world_id: UUID,
    clock_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    return delete_faction_clock(world_id, clock_id, svc)


@router.get("/{world_id}/dm/suggestions", response_model=GenerationSuggestionListResponse)
def list_dm_suggestions(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> GenerationSuggestionListResponse:
    suggestions = svc.list_generation_suggestions(world_id)
    if suggestions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return GenerationSuggestionListResponse(
        suggestions=[suggestion for suggestion in suggestions if suggestion.source_type == "dm"]
    )
