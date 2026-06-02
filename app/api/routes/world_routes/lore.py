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

@router.get("/{world_id}/lore-notes", response_model=LoreNoteListResponse)
def list_lore_notes(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteListResponse:
    notes = svc.list_lore_notes(world_id)
    if notes is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return LoreNoteListResponse(notes=notes)


@router.post("/{world_id}/lore-notes", response_model=LoreNoteRead, status_code=status.HTTP_201_CREATED)
def create_lore_note(
    world_id: UUID,
    body: LoreNoteCreate,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteRead:
    try:
        return svc.create_lore_note(world_id, body)
    except ValueError as exc:
        detail = "World not found" if str(exc) == "World not found" else str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.patch("/{world_id}/lore-notes/{note_id}", response_model=LoreNoteRead)
def update_lore_note(
    world_id: UUID,
    note_id: UUID,
    body: LoreNoteUpdate,
    svc: WorldService = Depends(get_world_service),
) -> LoreNoteRead:
    try:
        note = svc.update_lore_note(world_id, note_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lore note not found")
    return note


@router.delete("/{world_id}/lore-notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lore_note(
    world_id: UUID,
    note_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_lore_note(world_id, note_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lore note not found")


@router.get("/{world_id}/faction-clocks", response_model=FactionClockListResponse)
def list_faction_clocks(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockListResponse:
    clocks = svc.list_faction_clocks(world_id)
    if clocks is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return FactionClockListResponse(clocks=clocks)


@router.post(
    "/{world_id}/faction-clocks",
    response_model=FactionClockRead,
    status_code=status.HTTP_201_CREATED,
)
def create_faction_clock(
    world_id: UUID,
    body: FactionClockCreate,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockRead:
    try:
        return svc.create_faction_clock(world_id, body)
    except ValueError as exc:
        detail = "World not found" if str(exc) == "World not found" else str(exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.patch("/{world_id}/faction-clocks/{clock_id}", response_model=FactionClockRead)
def update_faction_clock(
    world_id: UUID,
    clock_id: UUID,
    body: FactionClockUpdate,
    svc: WorldService = Depends(get_world_service),
) -> FactionClockRead:
    try:
        clock = svc.update_faction_clock(world_id, clock_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not clock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction clock not found")
    return clock


@router.delete("/{world_id}/faction-clocks/{clock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction_clock(
    world_id: UUID,
    clock_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_faction_clock(world_id, clock_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faction clock not found")


@router.get("/{world_id}/revisions", response_model=RevisionVersionListResponse)
def list_revisions(
    world_id: UUID,
    entity_id: UUID | None = None,
    svc: WorldService = Depends(get_world_service),
) -> RevisionVersionListResponse:
    versions = svc.list_revisions(world_id, entity_id)
    if versions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return RevisionVersionListResponse(versions=versions)


@router.post("/{world_id}/revisions/{revision_id}/restore", response_model=EntityRead)
def restore_revision(
    world_id: UUID,
    revision_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> EntityRead:
    entity = svc.restore_revision(world_id, revision_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    return entity
