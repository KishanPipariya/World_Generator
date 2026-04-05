from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

from neo4j import Driver

from app.schemas.world import WorldCreate, WorldRead


class WorldLLM(Protocol):
    """Minimal surface used by :class:`WorldService` for generation."""

    def enabled(self) -> bool: ...

    def generate_section(
        self, world: WorldRead, section: Literal["glossary", "timeline_hint"]
    ) -> str | None: ...


@dataclass
class _WorldRecord:
    id: UUID
    title: str
    tone: str | None
    era_notes: str | None
    seed: str | None
    created_at: datetime


class WorldService:
    def __init__(self, driver: Driver, llm: WorldLLM | None = None) -> None:
        self._driver = driver
        self._llm = llm

    def _get_record(self, world_id: UUID) -> _WorldRecord | None:
        query = """
        MATCH (w:World {id: $id})
        RETURN w.id AS id, w.title AS title, w.tone AS tone,
               w.era_notes AS era_notes, w.seed AS seed, w.created_at AS created_at
        """
        with self._driver.session() as session:
            result = session.run(query, id=str(world_id))
            record = result.single()
            if not record:
                return None
            return _WorldRecord(
                id=UUID(record["id"]),
                title=record["title"],
                tone=record.get("tone"),
                era_notes=record.get("era_notes"),
                seed=record.get("seed"),
                created_at=datetime.fromisoformat(record["created_at"])
            )

    def create(self, data: WorldCreate) -> WorldRead:
        wid = uuid4()
        now = datetime.now(UTC)
        query = """
        CREATE (w:World {
            id: $id, title: $title, tone: $tone, 
            era_notes: $era_notes, seed: $seed, created_at: $created_at
        })
        """
        with self._driver.session() as session:
            session.run(query, 
                        id=str(wid), 
                        title=data.title, 
                        tone=data.tone,
                        era_notes=data.era_notes, 
                        seed=data.seed, 
                        created_at=now.isoformat())
        
        rec = _WorldRecord(
            id=wid,
            title=data.title,
            tone=data.tone,
            era_notes=data.era_notes,
            seed=data.seed,
            created_at=now,
        )
        return self._to_read(rec)

    def list_worlds(self) -> list[WorldRead]:
        query = """
        MATCH (w:World)
        RETURN w.id AS id, w.title AS title, w.tone AS tone,
               w.era_notes AS era_notes, w.seed AS seed, w.created_at AS created_at
        ORDER BY w.created_at DESC
        """
        worlds = []
        with self._driver.session() as session:
            result = session.run(query)
            for record in result:
                rec = _WorldRecord(
                    id=UUID(record["id"]),
                    title=record["title"],
                    tone=record.get("tone"),
                    era_notes=record.get("era_notes"),
                    seed=record.get("seed"),
                    created_at=datetime.fromisoformat(record["created_at"])
                )
                worlds.append(self._to_read(rec))
        return worlds

    def get(self, world_id: UUID) -> WorldRead | None:
        rec = self._get_record(world_id)
        return self._to_read(rec) if rec else None

    def generate_stub(
        self,
        world_id: UUID,
        section: Literal["glossary", "timeline_hint"] | None,
    ) -> tuple[Literal["glossary", "timeline_hint"], str] | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        sec: Literal["glossary", "timeline_hint"] = section or "glossary"
        wread = self._to_read(rec)
        if self._llm and self._llm.enabled():
            generated = self._llm.generate_section(wread, sec)
            if generated:
                return sec, generated
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
