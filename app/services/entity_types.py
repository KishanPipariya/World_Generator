from __future__ import annotations


def display_entity_type(entity_type: str) -> str:
    normalized = entity_type.strip().lower()
    if normalized in {"character", "person", "historical figure"}:
        return "Character"
    if normalized in {"location", "city", "region", "landmark", "continent"}:
        return "Location"
    if normalized in {"faction", "guild", "kingdom", "organization"}:
        return "Faction"
    if normalized in {"concept", "magic system", "technology", "term"}:
        return "Concept"
    if normalized in {"event", "historical event", "battle"}:
        return "Event"
    return "Other"
