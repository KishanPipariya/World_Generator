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

@router.get("/{world_id}/entities", response_model=EntityListResponse)
def list_entities(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> EntityListResponse:
    entities = svc.list_entities(world_id)
    if entities is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return EntityListResponse(entities=entities)


@router.post(
    "/{world_id}/entities",
    response_model=EntityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entity(
    world_id: UUID,
    body: EntityCreate,
    svc: WorldService = Depends(get_world_service),
) -> EntityRead:
    try:
        return svc.create_entity(
            world_id=world_id,
            name=body.name,
            entity_type=body.entity_type,
            description=body.description,
            structured_fields=body.structured_fields,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.patch("/{world_id}/entities/{entity_id}", response_model=EntityRead)
def update_entity(
    world_id: UUID,
    entity_id: UUID,
    body: EntityUpdate,
    svc: WorldService = Depends(get_world_service),
) -> EntityRead:
    entity = svc.update_entity(world_id, entity_id, body)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity


@router.delete("/{world_id}/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(
    world_id: UUID,
    entity_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_entity(world_id, entity_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")


@router.get("/{world_id}/relationships", response_model=RelationshipListResponse)
def list_relationships(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> RelationshipListResponse:
    relationships = svc.list_relationships(world_id)
    if relationships is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return RelationshipListResponse(relationships=relationships)
