from __future__ import annotations

import hashlib
from uuid import UUID

from app.schemas.world import ConsistencyIssue, EntityRead, RelationshipRead
from app.services.entity_types import display_entity_type


def detect_consistency_issues(
    *,
    world_tone: str | None,
    entities: list[EntityRead],
    relationships: list[RelationshipRead],
) -> list[ConsistencyIssue]:
    issues: list[ConsistencyIssue] = []
    relationship_counts = _relationship_counts(relationships)

    if not entities:
        issues.append(
            ConsistencyIssue(
                code="empty_world",
                severity="warning",
                message="No entities have been saved yet.",
            )
        )

    name_to_entities: dict[str, list[EntityRead]] = {}
    for entity in entities:
        key = entity.name.strip().lower()
        name_to_entities.setdefault(key, []).append(entity)
        issues.extend(_entity_issues(world_tone, entity))

    for duplicates in name_to_entities.values():
        if len(duplicates) > 1:
            for entity in duplicates:
                issues.append(
                    ConsistencyIssue(
                        code="duplicate_name",
                        severity="error",
                        message=f"Duplicate entity name: {entity.name}.",
                        entity_id=entity.id,
                    )
                )

    for entity in entities:
        count = relationship_counts.get(entity.id, 0)
        if count == 0:
            issues.append(
                ConsistencyIssue(
                    code="orphaned_entity",
                    severity="warning",
                    message=f"{entity.name} has no relationships.",
                    entity_id=entity.id,
                )
            )
        elif display_entity_type(entity.entity_type) in {"Character", "Faction", "Event"} and count == 1:
            issues.append(
                ConsistencyIssue(
                    code="missing_relationship_context",
                    severity="info",
                    message=f"{entity.name} has limited relationship context for canon review.",
                    entity_id=entity.id,
                )
            )

    issues.extend(_relationship_issues(relationships))
    return issues


def _relationship_counts(relationships: list[RelationshipRead]) -> dict[UUID, int]:
    relationship_counts: dict[UUID, int] = {}
    for relationship in relationships:
        relationship_counts[relationship.source_entity_id] = (
            relationship_counts.get(relationship.source_entity_id, 0) + 1
        )
        relationship_counts[relationship.target_entity_id] = (
            relationship_counts.get(relationship.target_entity_id, 0) + 1
        )
    return relationship_counts


def _entity_issues(world_tone: str | None, entity: EntityRead) -> list[ConsistencyIssue]:
    issues: list[ConsistencyIssue] = []
    if not entity.description.strip():
        issues.append(
            ConsistencyIssue(
                code="missing_description",
                severity="warning",
                message=f"{entity.name} is missing a description.",
                entity_id=entity.id,
            )
        )
    elif len(entity.description.strip()) < 40:
        issues.append(
            ConsistencyIssue(
                code="thin_description",
                severity="info",
                message=f"{entity.name} has a short description.",
                entity_id=entity.id,
            )
        )
    if world_tone and world_tone.lower() not in entity.description.lower():
        issues.append(
            ConsistencyIssue(
                code="tone_check",
                severity="info",
                message=f"{entity.name} may need a pass for the world's tone.",
                entity_id=entity.id,
            )
        )

    displayed_type = display_entity_type(entity.entity_type)
    description = entity.description.strip().lower()
    if displayed_type in {"Character", "Faction"} and not any(
        cue in description
        for cue in ("wants", "goal", "needs", "seeks", "fears", "secret", "conflict")
    ):
        issues.append(
            ConsistencyIssue(
                code="thin_lore",
                severity="info",
                message=f"{entity.name} may need clearer goals, secrets, or story pressure.",
                entity_id=entity.id,
            )
        )
    if displayed_type == "Location" and not any(
        cue in description
        for cue in ("culture", "trade", "economy", "conflict", "ruled", "hazard", "landmark")
    ):
        issues.append(
            ConsistencyIssue(
                code="thin_lore",
                severity="info",
                message=f"{entity.name} may need culture, economy, conflict, or landmark context.",
                entity_id=entity.id,
            )
        )
    if displayed_type == "Event" and not any(
        cue in description
        for cue in (
            "before",
            "after",
            "during",
            "year",
            "century",
            "age",
            "era",
            "season",
            "day",
            "night",
        )
    ):
        issues.append(
            ConsistencyIssue(
                code="timeline_gap",
                severity="warning",
                message=f"{entity.name} is an event without clear chronology.",
                entity_id=entity.id,
            )
        )
    return issues


def _relationship_issues(relationships: list[RelationshipRead]) -> list[ConsistencyIssue]:
    issues: list[ConsistencyIssue] = []
    pair_types: dict[tuple[UUID, UUID, str], RelationshipRead] = {}
    pair_stances: dict[frozenset[UUID], set[str]] = {}

    for relationship in relationships:
        relation_text = relationship.relation_type.strip().lower()
        if not relationship.relation_type.strip():
            issues.append(
                ConsistencyIssue(
                    code="missing_relation_type",
                    severity="error",
                    message="A relationship is missing its relation type.",
                    relationship_id=relationship.id,
                )
            )
        elif len(relation_text) < 3:
            issues.append(
                ConsistencyIssue(
                    code="weak_relationship",
                    severity="warning",
                    message=f"Relationship '{relationship.relation_type}' is too terse for demo review.",
                    relationship_id=relationship.id,
                )
            )
        if not relationship.notes or len(relationship.notes.strip()) < 20:
            issues.append(
                ConsistencyIssue(
                    code="missing_relationship_context",
                    severity="info",
                    message=(
                        f"Relationship between {relationship.source_entity_name} "
                        f"and {relationship.target_entity_name} needs more context."
                    ),
                    relationship_id=relationship.id,
                )
            )
        key = (
            relationship.source_entity_id,
            relationship.target_entity_id,
            relation_text,
        )
        if key in pair_types:
            issues.append(
                ConsistencyIssue(
                    code="duplicate_relationship",
                    severity="warning",
                    message=(
                        f"Duplicate relationship between {relationship.source_entity_name} "
                        f"and {relationship.target_entity_name}."
                    ),
                    relationship_id=relationship.id,
                )
            )
        pair_types[key] = relationship
        stance = relationship_stance(relation_text)
        if stance:
            pair_key = frozenset((relationship.source_entity_id, relationship.target_entity_id))
            existing = pair_stances.setdefault(pair_key, set())
            if existing and stance not in existing:
                issues.append(
                    ConsistencyIssue(
                        code="possible_contradiction",
                        severity="warning",
                        message=(
                            f"{relationship.source_entity_name} and "
                            f"{relationship.target_entity_name} have mixed alliance/conflict signals."
                        ),
                        relationship_id=relationship.id,
                    )
                )
            existing.add(stance)
    return issues


def consistency_score(issues: list[ConsistencyIssue]) -> int:
    severity_cost = {"info": 2, "warning": 8, "error": 18}
    return max(0, 100 - sum(severity_cost[issue.severity] for issue in issues))


def consistency_summary(score: int, issues: list[ConsistencyIssue]) -> str:
    if not issues:
        return "Canon looks ready: no heuristic consistency issues were found."
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    info_count = sum(1 for issue in issues if issue.severity == "info")
    parts = []
    if error_count:
        parts.append(f"{error_count} blocking issue(s)")
    if warning_count:
        parts.append(f"{warning_count} warning(s)")
    if info_count:
        parts.append(f"{info_count} improvement note(s)")
    focus = "Fix errors first, then connect isolated lore and add context where flagged."
    if score >= 85:
        focus = "Strong demo shape; the remaining notes are polish."
    elif score >= 65:
        focus = "Demoable, but relationship context and chronology need attention."
    return f"Score {score}: {', '.join(parts)}. {focus}"


def consistency_issue_target_type(issue: ConsistencyIssue) -> str:
    if issue.entity_id:
        return "entity"
    if issue.relationship_id:
        return "relationship"
    return "world"


def consistency_issue_fingerprint(issue: ConsistencyIssue) -> str:
    target_type = consistency_issue_target_type(issue)
    if issue.entity_id:
        target_id = str(issue.entity_id)
    elif issue.relationship_id:
        target_id = str(issue.relationship_id)
    else:
        target_id = " ".join(issue.message.lower().split())
    raw = f"{issue.code}:{target_type}:{target_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def relationship_stance(relation_type: str) -> str | None:
    ally_cues = {"ally", "allied", "protect", "supports", "serves", "trusts", "loves"}
    conflict_cues = {"enemy", "rival", "hunts", "opposes", "betrays", "hates", "fights"}
    if any(cue in relation_type for cue in ally_cues):
        return "alliance"
    if any(cue in relation_type for cue in conflict_cues):
        return "conflict"
    return None
