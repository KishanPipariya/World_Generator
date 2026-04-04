from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from app.schemas.world import WorldCreate, WorldRead


@dataclass
class _WorldRecord:
    id: UUID
    title: str
    tone: str | None
    era_notes: str | None
    seed: str | None
    created_at: datetime


class WorldService:
    def __init__(self) -> None:
        self._store: dict[UUID, _WorldRecord] = {}

    def create(self, data: WorldCreate) -> WorldRead:
        wid = uuid4()
        now = datetime.now(UTC)
        rec = _WorldRecord(
            id=wid,
            title=data.title,
            tone=data.tone,
            era_notes=data.era_notes,
            seed=data.seed,
            created_at=now,
        )
        self._store[wid] = rec
        return self._to_read(rec)

    def list_worlds(self) -> list[WorldRead]:
        return [self._to_read(r) for r in self._store.values()]

    def get(self, world_id: UUID) -> WorldRead | None:
        rec = self._store.get(world_id)
        return self._to_read(rec) if rec else None

    def generate_stub(
        self,
        world_id: UUID,
        section: Literal["glossary", "timeline_hint"] | None,
    ) -> tuple[Literal["glossary", "timeline_hint"], str] | None:
        rec = self._store.get(world_id)
        if not rec:
            return None
        sec: Literal["glossary", "timeline_hint"] = section or "glossary"
        if sec == "glossary":
            text = (
                f"[stub glossary for “{rec.title}”] "
                "Placeholder entries will list invented terms, honorifics, "
                "and region-specific vocabulary tied to your tone and era notes."
            )
        else:
            text = (
                f"[stub timeline hint for “{rec.title}”] "
                "Placeholder beats: inciting change, midpoint shift, resolution pressure — "
                "to be expanded when timeline generation is implemented."
            )
        return sec, text

    @staticmethod
    def _to_read(rec: _WorldRecord) -> WorldRead:
        return WorldRead(
            id=rec.id,
            title=rec.title,
            tone=rec.tone,
            era_notes=rec.era_notes,
            seed=rec.seed,
            created_at=rec.created_at,
        )
