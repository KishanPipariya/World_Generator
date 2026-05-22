from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_world_service
from app.schemas.world import (
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    EntityCreate,
    EntityListResponse,
    EntityRead,
    EntityUpdate,
    GenerateRequest,
    GenerateResponse,
    MarkdownExportResponse,
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipRead,
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


@router.get("/{world_id}", response_model=WorldRead)
def get_world(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> WorldRead:
    w = svc.get(world_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    return w


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
        return AgenticGenerateResponse(
            world_id=world_id,
            instruction=body.instruction,
            content=content,
            entity_id=entity_id,
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


@router.get("/{world_id}/export/markdown", response_model=MarkdownExportResponse)
def export_markdown(
    world_id: UUID,
    svc: WorldService = Depends(get_world_service),
) -> MarkdownExportResponse:
    world = svc.get(world_id)
    content = svc.export_markdown(world_id)
    if not world or content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")
    filename = f"{world.title.strip().lower().replace(' ', '-') or 'world'}-bible.md"
    return MarkdownExportResponse(world_id=world_id, filename=filename, content=content)
