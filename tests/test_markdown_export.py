from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.world import EntityRead, RelationshipRead
from app.services.markdown_export import build_markdown_export


def _entity(name: str, entity_type: str, description: str) -> EntityRead:
    now = datetime.now(UTC)
    return EntityRead(
        id=uuid4(),
        world_id=uuid4(),
        name=name,
        entity_type=entity_type,
        description=description,
        structured_fields={},
        created_at=now,
    )


def _relationship(source: EntityRead, target: EntityRead) -> RelationshipRead:
    now = datetime.now(UTC)
    return RelationshipRead(
        id=uuid4(),
        world_id=source.world_id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type="protects",
        notes="Assigned after the winter treaty.",
        category=None,
        strength=4,
        history=None,
        stance="alliance",
        color=None,
        display_priority=None,
        source_entity_name=source.name,
        target_entity_name=target.name,
        created_at=now,
    )


def test_build_markdown_export_renders_full_world_bible() -> None:
    created_at = datetime(2026, 5, 27, tzinfo=UTC)
    character = _entity("Asha", "Character", "A bright scout with a secret goal.")
    location = _entity("Northgate", "Location", "A trade city with a landmark gate.")
    relationship = _relationship(character, location)

    content = build_markdown_export(
        title="Z",
        created_at=created_at,
        tone="bright",
        seed="seed",
        era_notes="Era notes.",
        entities=[character, location],
        relationships=[relationship],
        timeline=[],
    )

    assert "# Z" in content
    assert "- Created: 2026-05-27" in content
    assert "#### Asha" in content
    assert "- protects [[Northgate]]" in content
    assert "[[Asha]] protects [[Northgate]]" in content
    assert "strength: 4/5; stance: alliance" in content


def test_build_markdown_export_filters_character_dossier_scope() -> None:
    character = _entity("Asha", "Character", "A bright scout with a secret goal.")
    location = _entity("Northgate", "Location", "A trade city with a landmark gate.")

    content = build_markdown_export(
        title="Z",
        created_at=datetime(2026, 5, 27, tzinfo=UTC),
        tone=None,
        seed=None,
        era_notes=None,
        entities=[character, location],
        relationships=[],
        timeline=[],
        preset="character_dossier",
    )

    assert "#### Asha" in content
    assert "Northgate" not in content
