from __future__ import annotations

from datetime import datetime

from app.schemas.world import (
    CampaignSessionRead,
    EntityRead,
    ExportPreset,
    FactionClockRead,
    LoreNoteRead,
    RelationshipRead,
    TimelineEventRead,
)
from app.services.entity_types import display_entity_type


def build_markdown_export(
    *,
    title: str,
    created_at: datetime,
    tone: str | None,
    seed: str | None,
    era_notes: str | None,
    entities: list[EntityRead],
    relationships: list[RelationshipRead],
    timeline: list[TimelineEventRead],
    preset: ExportPreset = "full_bible",
    lore_notes: list[LoreNoteRead] | None = None,
    sessions: list[CampaignSessionRead] | None = None,
    clocks: list[FactionClockRead] | None = None,
) -> str:
    lore_notes = lore_notes or []
    sessions = sessions or []
    clocks = clocks or []

    if preset == "player_handout":
        return campaign_player_handout_markdown(title, entities, lore_notes)
    if preset == "session_brief":
        return campaign_session_brief_markdown(title, sessions, lore_notes, clocks)
    if preset == "dm_campaign_brief":
        return campaign_dm_brief_markdown(title, sessions, lore_notes, clocks)
    if preset == "timeline_only":
        return timeline_markdown(title, timeline)

    entities, relationships = _filter_export_scope(preset, entities, relationships)

    lines = [
        f"# {title}",
        "",
        f"> {export_label(preset)}.",
        "",
        "## World Metadata",
        "",
        f"- Created: {created_at.date().isoformat()}",
        f"- Entities: {len(entities)}",
        f"- Relationships: {len(relationships)}",
    ]
    if tone:
        lines.append(f"- Tone: {tone}")
    if seed:
        lines.append(f"- Seed: {seed}")
    lines.append("")
    if era_notes:
        lines.extend(["## Era Notes", "", era_notes, ""])

    lines.extend(["## Entities", ""])
    if not entities:
        lines.extend(["No saved entities yet.", ""])
    else:
        _append_entities(lines, entities, relationships)

    _append_relationships(lines, relationships)
    _append_timeline(lines, timeline)

    return "\n".join(lines).strip() + "\n"


def _filter_export_scope(
    preset: ExportPreset,
    entities: list[EntityRead],
    relationships: list[RelationshipRead],
) -> tuple[list[EntityRead], list[RelationshipRead]]:
    entity_types_by_preset = {
        "character_dossier": {"Character"},
        "faction_brief": {"Faction"},
        "location_gazetteer": {"Location"},
    }
    if preset not in entity_types_by_preset:
        return entities, relationships

    allowed = entity_types_by_preset[preset]
    filtered_entities = [
        entity for entity in entities if display_entity_type(entity.entity_type) in allowed
    ]
    allowed_ids = {entity.id for entity in filtered_entities}
    filtered_relationships = [
        relationship
        for relationship in relationships
        if relationship.source_entity_id in allowed_ids or relationship.target_entity_id in allowed_ids
    ]
    return filtered_entities, filtered_relationships


def _append_entities(
    lines: list[str],
    entities: list[EntityRead],
    relationships: list[RelationshipRead],
) -> None:
    for entity_type in ("Character", "Location", "Faction", "Concept", "Event", "Other"):
        grouped = [
            entity for entity in entities if display_entity_type(entity.entity_type) == entity_type
        ]
        if not grouped:
            continue
        lines.extend([f"### {entity_type}", ""])
        for entity in grouped:
            related = [
                relationship
                for relationship in relationships
                if relationship.source_entity_id == entity.id
                or relationship.target_entity_id == entity.id
            ]
            lines.extend([f"#### {entity.name}", "", entity.description, ""])
            if entity.structured_fields:
                lines.extend(["Structured fields:", ""])
                for key, value in entity.structured_fields.items():
                    if value:
                        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
                lines.append("")
            if related:
                lines.extend(["Related:", ""])
                for relationship in related:
                    if relationship.source_entity_id == entity.id:
                        other = relationship.target_entity_name
                        rel = relationship.relation_type
                    else:
                        other = relationship.source_entity_name
                        rel = f"is {relationship.relation_type} by"
                    lines.append(f"- {rel} [[{other}]]")
                lines.append("")


def _append_relationships(lines: list[str], relationships: list[RelationshipRead]) -> None:
    lines.extend(["## Relationships", ""])
    if not relationships:
        lines.extend(["No relationships yet.", ""])
        return

    for relationship in relationships:
        lines.append(
            f"- [[{relationship.source_entity_name}]] "
            f"{relationship.relation_type} "
            f"[[{relationship.target_entity_name}]]"
        )
        if relationship.notes:
            lines.append(f"  - {relationship.notes}")
        details = []
        if relationship.category:
            details.append(f"category: {relationship.category}")
        if relationship.strength:
            details.append(f"strength: {relationship.strength}/5")
        if relationship.stance:
            details.append(f"stance: {relationship.stance}")
        if relationship.display_priority is not None:
            details.append(f"priority: {relationship.display_priority}")
        if details:
            lines.append(f"  - {'; '.join(details)}")
        if relationship.history:
            lines.append(f"  - History: {relationship.history}")
    lines.append("")


def _append_timeline(lines: list[str], timeline: list[TimelineEventRead]) -> None:
    if not timeline:
        return

    lines.extend(["## Timeline", ""])
    for event in timeline:
        lines.append(f"- {event.event_order}. {event.title}")
        if event.description:
            lines.append(f"  - {event.description}")
        if event.causes:
            lines.append(f"  - Cause: {event.causes}")
        if event.consequences:
            lines.append(f"  - Consequence: {event.consequences}")
        if event.date_label or event.era_label:
            lines.append(
                f"  - When: {' / '.join([part for part in (event.era_label, event.date_label) if part])}"
            )
        if event.depends_on:
            lines.append(f"  - Depends on: {', '.join(str(item) for item in event.depends_on)}")
    lines.append("")


def export_label(preset: str) -> str:
    labels = {
        "full_bible": "Full world bible export",
        "character_dossier": "Character dossier export",
        "faction_brief": "Faction brief export",
        "location_gazetteer": "Location gazetteer export",
        "timeline_only": "Timeline export",
        "obsidian": "Obsidian-friendly world bible export",
        "player_handout": "Player-safe campaign handout",
        "session_brief": "Next-session campaign brief",
        "dm_campaign_brief": "Full DM campaign brief",
    }
    return labels.get(preset, "World bible export")


def timeline_markdown(title: str, timeline: list[TimelineEventRead]) -> str:
    lines = [f"# {title} Timeline", ""]
    if not timeline:
        lines.extend(["No timeline events yet.", ""])
    for event in timeline:
        lines.extend([f"## {event.event_order}. {event.title}", ""])
        if event.description:
            lines.extend([event.description, ""])
        if event.causes:
            lines.extend([f"- Cause: {event.causes}"])
        if event.consequences:
            lines.extend([f"- Consequence: {event.consequences}"])
        if event.date_label or event.era_label:
            lines.extend(
                [f"- When: {' / '.join([part for part in (event.era_label, event.date_label) if part])}"]
            )
        if event.depends_on:
            lines.extend([f"- Depends on: {', '.join(str(item) for item in event.depends_on)}"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def campaign_player_handout_markdown(
    title: str, entities: list[EntityRead], notes: list[LoreNoteRead]
) -> str:
    visible_notes = [
        note for note in notes if note.visibility in {"player_visible", "discovered", "redacted"}
    ]
    lines = [f"# {title} Player Handout", "", "## Known Lore", ""]
    if not visible_notes:
        lines.extend(["No player-visible lore notes yet.", ""])
    for note in visible_notes:
        text = note.handout_text or note.body
        if note.visibility == "redacted":
            text = "[redacted]"
        lines.extend([f"### {note.title}", "", text or "No handout text recorded.", ""])
    known_entity_ids = {
        note.subject_id for note in visible_notes if note.subject_type == "entity" and note.subject_id
    }
    if known_entity_ids:
        lines.extend(["## Known Entities", ""])
        for entity in entities:
            if entity.id in known_entity_ids:
                lines.extend([f"### {entity.name}", "", entity.description, ""])
    return "\n".join(lines).strip() + "\n"


def campaign_session_brief_markdown(
    title: str,
    sessions: list[CampaignSessionRead],
    notes: list[LoreNoteRead],
    clocks: list[FactionClockRead],
) -> str:
    lines = [f"# {title} Session Brief", "", "## Recent Sessions", ""]
    for session in sessions[:3]:
        lines.extend([f"### {session.session_number}. {session.title}", ""])
        if session.recap:
            lines.extend([session.recap, ""])
        if session.consequences:
            lines.extend([f"- Consequences: {session.consequences}", ""])
    active_clocks = [clock for clock in clocks if clock.status == "active"]
    lines.extend(["## Active Clocks", ""])
    if not active_clocks:
        lines.extend(["No active clocks.", ""])
    for clock in active_clocks:
        lines.extend([f"- {clock.title}: {clock.filled_segments}/{clock.segments}"])
        if clock.stakes:
            lines.extend([f"  - Stakes: {clock.stakes}"])
    prep_notes = [note for note in notes if note.visibility != "player_visible"][:8]
    lines.extend(["", "## Prep Notes", ""])
    if not prep_notes:
        lines.extend(["No prep notes recorded.", ""])
    for note in prep_notes:
        lines.extend([f"### {note.title}", "", note.body or note.handout_text or "", ""])
    return "\n".join(lines).strip() + "\n"


def campaign_dm_brief_markdown(
    title: str,
    sessions: list[CampaignSessionRead],
    notes: list[LoreNoteRead],
    clocks: list[FactionClockRead],
) -> str:
    lines = [f"# {title} DM Campaign Brief", "", "## Faction Clocks", ""]
    if not clocks:
        lines.extend(["No faction clocks yet.", ""])
    for clock in clocks:
        lines.extend([f"### {clock.title}", ""])
        lines.extend([f"- Status: {clock.status}", f"- Progress: {clock.filled_segments}/{clock.segments}"])
        if clock.stakes:
            lines.extend([f"- Stakes: {clock.stakes}"])
        lines.append("")
    lines.extend(["## Sessions", ""])
    if not sessions:
        lines.extend(["No campaign sessions yet.", ""])
    for session in sessions:
        lines.extend([f"### {session.session_number}. {session.title}", ""])
        for label, text in (
            ("Recap", session.recap),
            ("Player Actions", session.player_actions),
            ("Consequences", session.consequences),
        ):
            if text:
                lines.extend([f"**{label}:** {text}", ""])
    lines.extend(["## Lore Notes", ""])
    if not notes:
        lines.extend(["No lore notes yet.", ""])
    for note in notes:
        lines.extend([f"### {note.title}", ""])
        lines.extend([f"- Visibility: {note.visibility}", f"- Truth: {note.truth_state}"])
        if note.reveal_condition:
            lines.extend([f"- Reveal: {note.reveal_condition}"])
        body = note.body or note.handout_text
        if body:
            lines.extend(["", body])
        lines.append("")
    return "\n".join(lines).strip() + "\n"
