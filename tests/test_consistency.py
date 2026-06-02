from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.world_models import EntityRead, RelationshipRead
from app.services.consistency import (
    consistency_issue_fingerprint,
    consistency_score,
    consistency_summary,
    detect_consistency_issues,
)


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


def _relationship(
    source: EntityRead,
    target: EntityRead,
    relation_type: str,
    notes: str | None = None,
) -> RelationshipRead:
    now = datetime.now(UTC)
    return RelationshipRead(
        id=uuid4(),
        world_id=source.world_id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        relation_type=relation_type,
        notes=notes,
        category=None,
        strength=None,
        history=None,
        stance=None,
        color=None,
        display_priority=None,
        source_entity_name=source.name,
        target_entity_name=target.name,
        created_at=now,
    )


def test_detect_consistency_issues_flags_entity_and_relationship_gaps() -> None:
    character = _entity("Asha", "Character", "")
    faction = _entity("Bell Guard", "Faction", "A city watch with polished armor.")
    first = _relationship(character, faction, "protects")
    second = _relationship(faction, character, "hunts")

    issues = detect_consistency_issues(
        world_tone="bright",
        entities=[character, faction],
        relationships=[first, second],
    )

    codes = {issue.code for issue in issues}
    assert {
        "missing_description",
        "thin_lore",
        "tone_check",
        "missing_relationship_context",
        "possible_contradiction",
    }.issubset(codes)
    assert any(issue.entity_id == character.id for issue in issues)
    assert any(issue.relationship_id == second.id for issue in issues)


def test_consistency_score_summary_and_fingerprint_are_stable() -> None:
    entity = _entity("Asha", "Character", "")
    issue = detect_consistency_issues(
        world_tone=None,
        entities=[entity],
        relationships=[],
    )[0]

    assert consistency_issue_fingerprint(issue) == consistency_issue_fingerprint(issue)
    assert consistency_score([issue]) == 92
    assert "Score 92" in consistency_summary(92, [issue])
