from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_world_service
from app.schemas.world import (
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    GenerateRequest,
    GenerateResponse,
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
