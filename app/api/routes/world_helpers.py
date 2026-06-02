from collections.abc import Iterable
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.schemas.world_models import (
    ExportPreset,
    GenerationSuggestionRead,
    MarkdownExportResponse,
    WorldRead,
)


def raise_not_found(detail: str = "World not found") -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def list_response(model: type[BaseModel], field_name: str, items: Iterable[object]) -> BaseModel:
    return model(**{field_name: list(items)})


def filter_suggestions_by_source(
    suggestions: Iterable[GenerationSuggestionRead],
    *,
    source_type: str | None,
) -> list[GenerationSuggestionRead]:
    return [suggestion for suggestion in suggestions if suggestion.source_type == source_type]


def export_filename(world: WorldRead, preset: ExportPreset) -> str:
    slug = world.title.strip().lower().replace(" ", "-") or "world"
    return f"{slug}-{preset.replace('_', '-')}.md"


def export_markdown_response(
    world_id: UUID,
    world: WorldRead,
    content: str,
    preset: ExportPreset,
) -> MarkdownExportResponse:
    return MarkdownExportResponse(
        world_id=world_id,
        filename=export_filename(world, preset),
        content=content,
        preset=preset,
    )
