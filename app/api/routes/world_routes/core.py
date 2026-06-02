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

@router.post("", response_model=WorldRead, status_code=status.HTTP_201_CREATED)
def create_world(
    body: WorldCreate,
    svc: WorldService = Depends(get_world_service),
) -> WorldRead:
    return svc.create(body)


@router.get("", response_model=list[WorldRead])
def list_worlds(svc: WorldService = Depends(get_world_service)) -> list[WorldRead]:
    return svc.list_worlds()


@router.post("/demo", response_model=DemoWorldResponse, status_code=status.HTTP_201_CREATED)
def create_demo_world(svc: WorldService = Depends(get_world_service)) -> DemoWorldResponse:
    return svc.create_demo_world()


@router.get("/{world_id}", response_model=WorldRead)
def get_world(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> WorldRead:
    w = svc.get(world_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return w


@router.delete("/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_world(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    if not svc.delete_world(world_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.post("/{world_id}/generate", response_model=GenerateResponse)
def generate_stub(
    world_id: UUID,
    body: GenerateRequest | None = None,
    _rate_limited: object = Depends(check_generation_rate_limit),
    svc: WorldService = Depends(get_world_service),
) -> GenerateResponse:
    section = (body.section if body else None)
    result = svc.generate_stub(world_id, section)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    sec, content = result
    return GenerateResponse(world_id=world_id, section=sec, content=content)
