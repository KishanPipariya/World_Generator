from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_world_service
from app.schemas.world import (
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    ConsistencyIssueStateListResponse,
    ConsistencyIssueStateRead,
    ConsistencyIssueUpdate,
    ConsistencyReportResponse,
    DemoWorldResponse,
    DraftCreate,
    DraftListResponse,
    DraftRead,
    DraftUpdate,
    EntityCreate,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
    ExportPreset,
    GenerateRequest,
    GenerateResponse,
    GenerationSuggestionCreate,
    GenerationSuggestionListResponse,
    GraphViewCreate,
    GraphViewListResponse,
    GraphViewRead,
    PassageCheckRequest,
    PassageCheckResponse,
    PlanningBoardCreate,
    PlanningBoardListResponse,
    PlanningBoardRead,
    PlanningCardCreate,
    PlanningCardRead,
    MarkdownExportResponse,
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

from app.services.world_service import WorldService

router = APIRouter(prefix="/worlds", tags=["worlds"])


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
    svc: WorldService = Depends(get_world_service),
) -> GenerateResponse:
    section = (body.section if body else None)
    result = svc.generate_stub(world_id, section)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    sec, content = result
    return GenerateResponse(world_id=world_id, section=sec, content=content)


@router.post("/{world_id}/agentic-generate", response_model=AgenticGenerateResponse)
def agentic_generate(
    world_id: UUID,
    body: AgenticGenerateRequest,
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


@router.get("/{world_id}/suggestions", response_model=GenerationSuggestionListResponse)
def list_suggestions(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> GenerationSuggestionListResponse:
    suggestions = svc.list_generation_suggestions(world_id)
    if suggestions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return GenerationSuggestionListResponse(suggestions=suggestions)


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
    suggestion, entity = result
    return SuggestionApplyResponse(suggestion=suggestion, entity=entity)


@router.get("/{world_id}/timeline", response_model=TimelineEventListResponse)
def list_timeline_events(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> TimelineEventListResponse:
    events = svc.list_timeline_events(world_id)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return TimelineEventListResponse(events=events)


@router.post("/{world_id}/timeline", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def create_timeline_event(
    world_id: UUID,
    body: TimelineEventCreate,
    svc: WorldService = Depends(get_world_service),
) -> TimelineEventRead:
    try:
        return svc.create_timeline_event(world_id, body)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.get("/{world_id}/graph-views", response_model=GraphViewListResponse)
def list_graph_views(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> GraphViewListResponse:
    views = svc.list_graph_views(world_id)
    if views is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return GraphViewListResponse(views=views)


@router.post("/{world_id}/graph-views", response_model=GraphViewRead, status_code=status.HTTP_201_CREATED)
def create_graph_view(
    world_id: UUID,
    body: GraphViewCreate,
    svc: WorldService = Depends(get_world_service),
) -> GraphViewRead:
    try:
        return svc.create_graph_view(world_id, body)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")


@router.delete("/{world_id}/graph-views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_view(
    world_id: UUID,
    view_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> None:
    deleted = svc.delete_graph_view(world_id, view_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph view not found")


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


@router.get("/{world_id}/export/markdown", response_model=MarkdownExportResponse)
def export_markdown(
    world_id: UUID,
    preset: ExportPreset = "full_bible",
    svc: WorldService = Depends(get_world_service),
) -> MarkdownExportResponse:
    world = svc.get(world_id)
    content = svc.export_markdown(world_id, preset)
    if not world or content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    slug = world.title.strip().lower().replace(" ", "-") or "world"
    filename = f"{slug}-{preset.replace('_', '-')}.md"
    return MarkdownExportResponse(world_id=world_id, filename=filename, content=content, preset=preset)
