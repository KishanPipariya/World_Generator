from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol
from uuid import UUID, uuid4

from app.schemas.world import (
    CampaignSessionCreate,
    CampaignSessionRead,
    CampaignSessionUpdate,
    ConsistencyIssue,
    ConsistencyIssueStateRead,
    ConsistencyIssueUpdate,
    ConsistencyReportResponse,
    DemoWorldResponse,
    DraftCheckHistoryItem,
    DraftCreate,
    DraftExtractionResponse,
    DraftRead,
    DraftUpdate,
    EntityRead,
    EntityUpdate,
    ExportPreset,
    FactionClockCreate,
    FactionClockRead,
    FactionClockUpdate,
    GenerationSuggestionRead,
    GraphViewCreate,
    GraphViewRead,
    LoreNoteCreate,
    LoreNoteRead,
    LoreNoteUpdate,
    PassageCheckIssue,
    PassageCheckResponse,
    PlanningBoardCreate,
    PlanningBoardDetail,
    PlanningBoardRead,
    PlanningCardCreate,
    PlanningCardRead,
    RelationshipRead,
    RevisionVersionRead,
    TimelineEventCreate,
    TimelineEventRead,
    WorldCreate,
    WorldRead,
)
from app.services.consistency import (
    consistency_issue_fingerprint,
    consistency_issue_target_type,
    consistency_score,
    consistency_summary,
    detect_consistency_issues,
)
from app.services.entity_types import display_entity_type
from app.services.markdown_export import build_markdown_export


class WorldLLM(Protocol):
    """Minimal surface used by :class:`WorldService` for generation."""

    def enabled(self) -> bool: ...

    def generate_section(
        self, world: WorldRead, section: Literal["glossary", "timeline_hint"]
    ) -> str | None: ...

    def generate_agentic(
        self, world: WorldRead, context: str, instruction: str
    ) -> str | None: ...


class Neo4jDriverLike(Protocol):
    def session(self) -> Any: ...


@dataclass
class _WorldRecord:
    id: UUID
    title: str
    tone: str | None
    era_notes: str | None
    seed: str | None
    created_at: datetime


class WorldService:
    def __init__(self, driver: Neo4jDriverLike, llm: WorldLLM | None = None) -> None:
        self._driver = driver
        self._llm = llm
        self._world_cache: dict[UUID, _WorldRecord] = {}

    def initialize_schema(self) -> None:
        """Create lookup constraints used by the service's hot queries."""
        queries = [
            "CREATE CONSTRAINT world_id_unique IF NOT EXISTS FOR (w:World) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX entity_world_id IF NOT EXISTS FOR (e:Entity) ON (e.world_id)",
            "CREATE INDEX relationship_world_id IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.world_id)",
            "CREATE INDEX canon_issue_world_id IF NOT EXISTS FOR (i:CanonIssue) ON (i.world_id)",
            "CREATE INDEX canon_suggestion_world_id IF NOT EXISTS FOR (s:CanonSuggestion) ON (s.world_id)",
            "CREATE INDEX timeline_event_world_id IF NOT EXISTS FOR (t:TimelineEvent) ON (t.world_id)",
            "CREATE INDEX graph_view_world_id IF NOT EXISTS FOR (v:GraphView) ON (v.world_id)",
            "CREATE INDEX planning_board_world_id IF NOT EXISTS FOR (b:PlanningBoard) ON (b.world_id)",
            "CREATE INDEX campaign_session_world_id IF NOT EXISTS FOR (cs:CampaignSession) ON (cs.world_id)",
            "CREATE INDEX lore_note_world_id IF NOT EXISTS FOR (ln:LoreNote) ON (ln.world_id)",
            "CREATE INDEX faction_clock_world_id IF NOT EXISTS FOR (fc:FactionClock) ON (fc.world_id)",
            "CREATE INDEX draft_passage_world_id IF NOT EXISTS FOR (d:DraftPassage) ON (d.world_id)",
            "CREATE INDEX revision_version_world_id IF NOT EXISTS FOR (r:RevisionVersion) ON (r.world_id)",
        ]
        with self._driver.session() as session:
            for query in queries:
                session.run(query)

    def _get_record(self, world_id: UUID) -> _WorldRecord | None:
        if cached := self._world_cache.get(world_id):
            return cached
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $id
        RETURN properties(w) AS props
        """
        with self._driver.session() as session:
            result = session.run(query, id=str(world_id))
            record = result.single()
            if not record:
                return None
            world = self._world_from_props(record.get("props", record))
            self._world_cache[world.id] = world
            return world

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
        self._world_cache[wid] = rec
        return self._to_read(rec)

    def create_demo_world(self) -> DemoWorldResponse:
        world = self.create(
            WorldCreate(
                title="The Ember Archipelago",
                tone="mythic intrigue with practical survival stakes",
                era_notes=(
                    "Post-imperial island city-states compete for relic engines, "
                    "storm-safe harbors, and legitimacy after the Ashen Crown fell."
                ),
                seed="demo-ember-archipelago",
            )
        )
        entity_specs = [
            (
                "Mara Vey",
                "Character",
                "A lighthouse cartographer who can read stormlight residue. Mara wants to prove the old imperial sea charts were deliberately falsified.",
            ),
            (
                "Ithoros",
                "Location",
                "A tiered harbor city built around a dormant volcanic vent and the last functioning ember engine.",
            ),
            (
                "The Glass Concord",
                "Faction",
                "Merchant-magistrates who control mirror relays, debt ledgers, and most legal trade between islands.",
            ),
            (
                "Ash Choir",
                "Faction",
                "Exiled ritual engineers who believe the fallen empire's relics are bound to human memory.",
            ),
            (
                "The Ember Engine",
                "Concept",
                "A relic power core that burns stored vows instead of fuel, making every activation politically dangerous.",
            ),
            (
                "Night of Falling Bells",
                "Event",
                "The coup that ended the Ashen Crown when every warning bell in the archipelago rang once and cracked.",
            ),
        ]
        entities = [
            self.create_entity(world.id, name, entity_type, description)
            for name, entity_type, description in entity_specs
        ]
        by_name = {entity.name: entity for entity in entities}
        relationship_specs = [
            ("Mara Vey", "investigates", "Night of Falling Bells", "Her father's final chart marks impossible bell paths."),
            ("The Glass Concord", "governs trade in", "Ithoros", "Their permits decide which ships reach the ember engine."),
            ("Ash Choir", "seeks", "The Ember Engine", "They need it to restore memories erased during the coup."),
            ("The Ember Engine", "powers", "Ithoros", "The city dims whenever public promises are broken."),
            ("The Glass Concord", "hunts", "Ash Choir", "The Concord calls them terrorists; the Choir calls them archivists."),
        ]
        relationships = [
            self.create_relationship(
                world.id,
                by_name[source].id,
                by_name[target].id,
                relation_type,
                notes,
            )
            for source, relation_type, target, notes in relationship_specs
        ]
        return DemoWorldResponse(world=world, entities=entities, relationships=relationships)

    def list_worlds(self) -> list[WorldRead]:
        query = """
        MATCH (w)
        WHERE "World" IN labels(w)
        WITH properties(w) AS props
        RETURN props
        ORDER BY props.created_at DESC
        """
        worlds = []
        with self._driver.session() as session:
            result = session.run(query)
            for record in result:
                world = self._world_from_props(record.get("props", record))
                self._world_cache[world.id] = world
                worlds.append(self._to_read(world))
        return worlds

    def get(self, world_id: UUID) -> WorldRead | None:
        rec = self._get_record(world_id)
        return self._to_read(rec) if rec else None

    def delete_world(self, world_id: UUID) -> bool:
        if not self._get_record(world_id):
            return False
        delete_entities_query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO" AND "Entity" IN labels(e)
        DETACH DELETE e
        """
        delete_issue_query = """
        MATCH (i)
        WHERE "CanonIssue" IN labels(i) AND properties(i).world_id = $w_id
        DETACH DELETE i
        """
        delete_world_query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        WITH w
        DETACH DELETE w
        RETURN 1 AS deleted
        """
        with self._driver.session() as session:
            session.run(delete_entities_query, w_id=str(world_id))
            session.run(delete_issue_query, w_id=str(world_id))
            result = session.run(delete_world_query, w_id=str(world_id))
            record = result.single()
            if record and record["deleted"]:
                self._world_cache.pop(world_id, None)
            return bool(record and record["deleted"])

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

    def create_entity(
        self,
        world_id: UUID,
        name: str,
        entity_type: str,
        description: str,
        structured_fields: dict[str, str] | None = None,
    ) -> EntityRead:
        eid = uuid4()
        now = datetime.now(UTC)
        structured_json = json.dumps(structured_fields or {}, sort_keys=True)
        query = """
        MATCH (w:World {id: $w_id})
        CREATE (w)<-[:BELONGS_TO]-(e:Entity {
            id: $e_id, world_id: $w_id, name: $name, 
            entity_type: $entity_type, description: $description,
            structured_fields_json: $structured_fields_json, created_at: $created_at
        })
        RETURN e.id AS id, e.world_id AS world_id, e.name AS name,
               e.entity_type AS entity_type, e.description AS description,
               e.structured_fields_json AS structured_fields_json, e.created_at AS created_at
        """
        with self._driver.session() as session:
            result = session.run(query, 
                                 w_id=str(world_id), 
                                 e_id=str(eid),
                                 name=name,
                                 entity_type=entity_type,
                                 description=description,
                                 structured_fields_json=structured_json,
                                 created_at=now.isoformat())
            record = result.single()
            if not record:
                raise ValueError("Failed to create entity. World not found?")
            return EntityRead(
                id=UUID(record["id"]),
                world_id=UUID(record["world_id"]),
                name=record["name"],
                entity_type=record["entity_type"],
                description=record["description"],
                structured_fields=self._decode_structured_fields(record.get("structured_fields_json")),
                created_at=datetime.fromisoformat(record["created_at"])
            )

    def list_entities(self, world_id: UUID) -> list[EntityRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO" AND "Entity" IN labels(e)
        WITH properties(e) AS props
        RETURN props
        ORDER BY props.entity_type ASC, props.name ASC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._entity_from_record(record) for record in result]

    def update_entity(
        self, world_id: UUID, entity_id: UUID, data: EntityUpdate
    ) -> EntityRead | None:
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return self.get_entity(world_id, entity_id)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO"
          AND "Entity" IN labels(e)
          AND properties(e).id = $e_id
        SET e.name = coalesce($name, e.name),
            e.entity_type = coalesce($entity_type, e.entity_type),
            e.description = coalesce($description, e.description),
            e.structured_fields_json = coalesce($structured_fields_json, e.structured_fields_json)
        RETURN properties(e) AS props, $source AS source
        """
        with self._driver.session() as session:
            current = self.get_entity(world_id, entity_id)
            result = session.run(
                query,
                w_id=str(world_id),
                e_id=str(entity_id),
                name=updates.get("name"),
                entity_type=updates.get("entity_type"),
                description=updates.get("description"),
                structured_fields_json=(
                    json.dumps(updates["structured_fields"], sort_keys=True)
                    if "structured_fields" in updates
                    else None
                ),
                source="manual",
            )
            record = result.single()
            updated = self._entity_from_record(record) if record else None
            if current and updated and updates.get("description") is not None:
                self._record_revision(
                    world_id=world_id,
                    entity_id=entity_id,
                    subject_type="entity",
                    field_name="description",
                    previous_value=current.description,
                    new_value=updated.description,
                    source="manual",
                )
            return updated

    def get_entity(self, world_id: UUID, entity_id: UUID) -> EntityRead | None:
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO"
          AND "Entity" IN labels(e)
          AND properties(e).id = $e_id
        RETURN properties(e) AS props
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), e_id=str(entity_id))
            record = result.single()
            return self._entity_from_record(record) if record else None

    def delete_entity(self, world_id: UUID, entity_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO"
          AND "Entity" IN labels(e)
          AND properties(e).id = $e_id
        OPTIONAL MATCH (e)-[linked]-()
        DELETE linked, e
        RETURN count(e) AS deleted
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), e_id=str(entity_id))
            record = result.single()
            return bool(record and record["deleted"])

    def create_relationship(
        self,
        world_id: UUID,
        source_entity_id: UUID,
        target_entity_id: UUID,
        relation_type: str,
        notes: str | None,
        category: str | None = None,
        strength: int | None = None,
        history: str | None = None,
        stance: str | None = None,
        color: str | None = None,
        display_priority: int | None = None,
    ) -> RelationshipRead:
        rid = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[source_belongs]-(source)
        WHERE type(source_belongs) = "BELONGS_TO"
          AND "Entity" IN labels(source)
          AND properties(source).id = $source_id
        MATCH (w)<-[target_belongs]-(target)
        WHERE type(target_belongs) = "BELONGS_TO"
          AND "Entity" IN labels(target)
          AND properties(target).id = $target_id
        CREATE (source)-[r:RELATED_TO {
            id: $r_id, world_id: $w_id, relation_type: $relation_type,
            notes: $notes, category: $category, strength: $strength,
            history: $history, stance: $stance, color: $color,
            display_priority: $display_priority, created_at: $created_at
        }]->(target)
        WITH properties(r) AS rel_props,
             properties(source) AS source_props,
             properties(target) AS target_props
        RETURN rel_props, source_props, target_props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                source_id=str(source_entity_id),
                target_id=str(target_entity_id),
                r_id=str(rid),
                relation_type=relation_type,
                notes=notes,
                category=category,
                strength=strength,
                history=history,
                stance=stance,
                color=color,
                display_priority=display_priority,
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World or entity not found")
            return self._relationship_from_record(record)

    def list_relationships(self, world_id: UUID) -> list[RelationshipRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (source)-[r]->(target)
        WHERE type(r) = "RELATED_TO"
          AND properties(r).world_id = $w_id
          AND "Entity" IN labels(source)
          AND "Entity" IN labels(target)
        WITH properties(r) AS rel_props,
             properties(source) AS source_props,
             properties(target) AS target_props
        RETURN rel_props, source_props, target_props
        ORDER BY rel_props.created_at DESC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._relationship_from_record(record) for record in result]

    def delete_relationship(self, world_id: UUID, relationship_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH ()-[r]->()
        WHERE type(r) = "RELATED_TO"
          AND properties(r).id = $r_id
          AND properties(r).world_id = $w_id
        DELETE r
        RETURN count(r) AS deleted
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), r_id=str(relationship_id))
            record = result.single()
            return bool(record and record["deleted"])

    def export_markdown(self, world_id: UUID, preset: ExportPreset = "full_bible") -> str | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        entities = self.list_entities(world_id) or []
        relationships = self.list_relationships(world_id) or []
        timeline = self.list_timeline_events(world_id) or []
        lore_presets = {
            "player_handout",
            "session_brief",
            "dm_campaign_brief",
        }
        campaign_brief_presets = {"session_brief", "dm_campaign_brief"}
        lore_notes = (self.list_lore_notes(world_id) or []) if preset in lore_presets else None
        sessions = (
            (self.list_campaign_sessions(world_id) or [])
            if preset in campaign_brief_presets
            else None
        )
        clocks = (
            (self.list_faction_clocks(world_id) or [])
            if preset in campaign_brief_presets
            else None
        )

        return build_markdown_export(
            title=rec.title,
            created_at=rec.created_at,
            tone=rec.tone,
            seed=rec.seed,
            era_notes=rec.era_notes,
            entities=entities,
            relationships=relationships,
            timeline=timeline,
            preset=preset,
            lore_notes=lore_notes,
            sessions=sessions,
            clocks=clocks,
        )

    def consistency_report(self, world_id: UUID) -> ConsistencyReportResponse | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        entities = self.list_entities(world_id) or []
        relationships = self.list_relationships(world_id) or []
        issues = detect_consistency_issues(
            world_tone=rec.tone,
            entities=entities,
            relationships=relationships,
        )
        issues = self._sync_consistency_issues(world_id, issues)
        score = consistency_score(issues)
        summary = consistency_summary(score, issues)
        return ConsistencyReportResponse(
            world_id=world_id,
            score=score,
            summary=summary,
            issues=issues,
        )

    def list_consistency_issue_states(self, world_id: UUID) -> list[ConsistencyIssueStateRead] | None:
        if not self._get_record(world_id):
            return None
        self.consistency_report(world_id)
        return self._list_consistency_issue_states(world_id)

    def update_consistency_issue_state(
        self,
        world_id: UUID,
        issue_id: UUID,
        data: ConsistencyIssueUpdate,
    ) -> ConsistencyIssueStateRead | None:
        if not self._get_record(world_id):
            return None
        now = datetime.now(UTC)
        note_is_set = "note" in data.model_fields_set
        query = """
        MATCH (i)
        WHERE "CanonIssue" IN labels(i)
          AND properties(i).world_id = $w_id
          AND properties(i).id = $issue_id
        SET i.status = coalesce($status, i.status),
            i.note = CASE WHEN $note_is_set THEN $note ELSE i.note END,
            i.updated_at = $updated_at
        RETURN properties(i) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                issue_id=str(issue_id),
                status=data.status,
                note=data.note,
                note_is_set=note_is_set,
                updated_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                return None
            return self._consistency_issue_state_from_record(record)

    def get_world_context(self, world_id: UUID) -> str:
        """Retrieves existing lore/entities for a world via RAG-style DB query."""
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $id
        MATCH (w)<-[belongs]-(e)
        WHERE type(belongs) = "BELONGS_TO" AND "Entity" IN labels(e)
        WITH properties(e) AS props
        RETURN props
        ORDER BY props.created_at ASC
        """
        entities = []
        with self._driver.session() as session:
            result = session.run(query, id=str(world_id))
            for record in result:
                props = record.get("props", record)
                entities.append(
                    f"[{props['entity_type']}] {props['name']}:\n{props['description']}"
                )
        
        if not entities:
            return "No previous world lore has been generated yet."
        return "\n\n".join(entities)

    def _sync_consistency_issues(
        self,
        world_id: UUID,
        detected_issues: list[ConsistencyIssue],
    ) -> list[ConsistencyIssue]:
        if not detected_issues:
            return []
        now = datetime.now(UTC)
        existing_by_fingerprint = {
            issue.fingerprint: issue for issue in self._list_consistency_issue_states(world_id)
        }
        active: list[ConsistencyIssue] = []
        for issue in detected_issues:
            fingerprint = consistency_issue_fingerprint(issue)
            target_type = consistency_issue_target_type(issue)
            state = existing_by_fingerprint.get(fingerprint)
            if state:
                status = "reopened" if state.status == "resolved" else state.status
                state = self._update_detected_consistency_issue(
                    issue=issue,
                    state=state,
                    target_type=target_type,
                    status=status,
                    now=now,
                )
            else:
                state = self._create_consistency_issue_state(
                    world_id=world_id,
                    issue=issue,
                    fingerprint=fingerprint,
                    target_type=target_type,
                    now=now,
                )
            hydrated = issue.model_copy(
                update={
                    "target_type": state.target_type,
                    "issue_id": state.id,
                    "status": state.status,
                    "note": state.note,
                    "first_seen": state.first_seen,
                    "last_seen": state.last_seen,
                }
            )
            if state.status in {"open", "reopened"}:
                active.append(hydrated)
        return active

    def _create_consistency_issue_state(
        self,
        world_id: UUID,
        issue: ConsistencyIssue,
        fingerprint: str,
        target_type: str,
        now: datetime,
    ) -> ConsistencyIssueStateRead:
        issue_id = uuid4()
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(i:CanonIssue {
            id: $issue_id, world_id: $w_id, fingerprint: $fingerprint,
            code: $code, severity: $severity, message: $message,
            target_type: $target_type, entity_id: $entity_id,
            relationship_id: $relationship_id, status: "open", note: $note,
            first_seen: $first_seen, last_seen: $last_seen, updated_at: $updated_at
        })
        RETURN properties(i) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                issue_id=str(issue_id),
                fingerprint=fingerprint,
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                target_type=target_type,
                entity_id=str(issue.entity_id) if issue.entity_id else None,
                relationship_id=str(issue.relationship_id) if issue.relationship_id else None,
                note=None,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._consistency_issue_state_from_record(record)

    def _update_detected_consistency_issue(
        self,
        issue: ConsistencyIssue,
        state: ConsistencyIssueStateRead,
        target_type: str,
        status: str,
        now: datetime,
    ) -> ConsistencyIssueStateRead:
        query = """
        MATCH (i)
        WHERE "CanonIssue" IN labels(i) AND properties(i).id = $issue_id
        SET i.code = $code,
            i.severity = $severity,
            i.message = $message,
            i.target_type = $target_type,
            i.entity_id = $entity_id,
            i.relationship_id = $relationship_id,
            i.status = $status,
            i.last_seen = $last_seen,
            i.updated_at = $updated_at
        RETURN properties(i) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                issue_id=str(state.id),
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                target_type=target_type,
                entity_id=str(issue.entity_id) if issue.entity_id else None,
                relationship_id=str(issue.relationship_id) if issue.relationship_id else None,
                status=status,
                last_seen=now.isoformat(),
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._consistency_issue_state_from_record(record)

    def _list_consistency_issue_states(self, world_id: UUID) -> list[ConsistencyIssueStateRead]:
        query = """
        MATCH (i)
        WHERE "CanonIssue" IN labels(i) AND properties(i).world_id = $w_id
        WITH properties(i) AS props
        RETURN props
        ORDER BY props.updated_at DESC
        """
        states = []
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            for record in result:
                states.append(self._consistency_issue_state_from_record(record))
        return states

    def agentic_generate(
        self, world_id: UUID, instruction: str, save_as_type: str | None, save_as_name: str | None
    ) -> tuple[str, UUID | None]:
        rec = self._get_record(world_id)
        if not rec:
            raise ValueError("World not found")
        wread = self._to_read(rec)

        wcontext = self.get_world_context(world_id)

        if self._llm and self._llm.enabled():
            result_text = self._llm.generate_agentic(wread, wcontext, instruction)
            if not result_text:
                result_text = "[Agentic generation returned empty or failed.]"
        else:
            result_text = (
                f"[Stub agentic generation for {rec.title}]\n"
                f"Instruction: {instruction}\n"
                "Would run Author -> Critic pipeline using world context here."
            )

        entity_id: UUID | None = None
        if save_as_type and save_as_name:
            entity = self.create_entity(
                world_id=world_id,
                name=save_as_name,
                entity_type=save_as_type,
                description=result_text
            )
            entity_id = entity.id

        return result_text, entity_id

    def create_generation_suggestion(
        self,
        world_id: UUID,
        instruction: str,
        content: str,
        suggested_name: str | None = None,
        suggested_type: str | None = None,
        candidate_kind: str | None = None,
        source_type: str | None = None,
        source_id: UUID | None = None,
        source_excerpt: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> GenerationSuggestionRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        sid = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(s:CanonSuggestion {
            id: $s_id, world_id: $w_id, instruction: $instruction,
            content: $content, suggested_name: $suggested_name,
            suggested_type: $suggested_type, status: "pending",
            candidate_kind: $candidate_kind, source_type: $source_type,
            source_id: $source_id, source_excerpt: $source_excerpt,
            payload_json: $payload_json,
            created_at: $created_at
        })
        RETURN properties(s) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                s_id=str(sid),
                instruction=instruction,
                content=content,
                suggested_name=suggested_name,
                suggested_type=suggested_type,
                candidate_kind=candidate_kind,
                source_type=source_type,
                source_id=str(source_id) if source_id else None,
                source_excerpt=source_excerpt,
                payload_json=json.dumps(payload or {}),
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World not found")
            return self._suggestion_from_record(record)

    def list_generation_suggestions(self, world_id: UUID) -> list[GenerationSuggestionRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(s)
        WHERE type(belongs) = "BELONGS_TO" AND "CanonSuggestion" IN labels(s)
        RETURN properties(s) AS props
        ORDER BY props.created_at DESC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._suggestion_from_record(record) for record in result]

    def apply_generation_suggestion(
        self,
        world_id: UUID,
        suggestion_id: UUID,
        mode: str,
        entity_id: UUID | None = None,
        name: str | None = None,
        entity_type: str | None = None,
        description: str | None = None,
    ) -> tuple[
        GenerationSuggestionRead,
        EntityRead | None,
        RelationshipRead | None,
        TimelineEventRead | None,
        LoreNoteRead | None,
    ] | None:
        suggestion = self._get_suggestion(world_id, suggestion_id)
        if not suggestion:
            return None
        entity: EntityRead | None = None
        relationship: RelationshipRead | None = None
        timeline_event: TimelineEventRead | None = None
        lore_note: LoreNoteRead | None = None
        content = description if description is not None else suggestion.content
        payload = suggestion.payload or {}
        if mode == "discard":
            status_value = "discarded"
        elif mode == "create_entity":
            entity = self.create_entity(
                world_id,
                name or suggestion.suggested_name or "Generated Lore",
                entity_type or suggestion.suggested_type or "Concept",
                content,
            )
            self._record_revision(
                world_id, entity.id, "entity", "description", None, entity.description, "generated"
            )
            status_value = "accepted"
        elif mode in {"append_to_entity", "replace_entity"} and entity_id:
            current = self.get_entity(world_id, entity_id)
            if not current:
                return None
            next_description = (
                f"{current.description.strip()}\n\n{content}".strip()
                if mode == "append_to_entity"
                else content
            )
            entity = self.update_entity(
                world_id, entity_id, EntityUpdate(description=next_description)
            )
            status_value = "accepted"
        elif mode == "create_relationship":
            source_id = payload.get("source_entity_id")
            target_id = payload.get("target_entity_id")
            strength = payload.get("strength")
            if not source_id or not target_id:
                raise ValueError("Relationship suggestions require source and target entities")
            relationship = self.create_relationship(
                world_id=world_id,
                source_entity_id=UUID(str(source_id)),
                target_entity_id=UUID(str(target_id)),
                relation_type=str(payload.get("relation_type") or suggestion.suggested_type or "related_to"),
                notes=str(payload.get("notes") or content),
                category=str(payload["category"]) if payload.get("category") else None,
                strength=int(str(strength)) if strength is not None else None,
                history=str(payload["history"]) if payload.get("history") else None,
                stance=str(payload["stance"]) if payload.get("stance") else None,
            )
            status_value = "accepted"
        elif mode == "create_timeline_event":
            raw_event_order = payload.get("event_order")
            raw_participants = payload.get("participants")
            next_order = len(self.list_timeline_events(world_id) or []) + 1
            participants = [
                UUID(str(item))
                for item in raw_participants
                if self._looks_like_uuid(str(item))
            ] if isinstance(raw_participants, list) else []
            timeline_event = self.create_timeline_event(
                world_id,
                TimelineEventCreate(
                    title=str(payload.get("title") or suggestion.suggested_name or "Draft event"),
                    event_order=int(str(raw_event_order)) if raw_event_order is not None else next_order,
                    description=str(payload.get("description") or content),
                    participants=participants,
                    date_label=str(payload["date_label"]) if payload.get("date_label") else None,
                    era_label=str(payload["era_label"]) if payload.get("era_label") else None,
                ),
            )
            status_value = "accepted"
        elif mode == "create_lore_note":
            lore_note = self.create_lore_note(
                world_id,
                LoreNoteCreate(
                    title=str(payload.get("title") or suggestion.suggested_name or "Draft lore note"),
                    body=str(payload.get("body") or content),
                    subject_type="world",
                    visibility="dm_only",
                    truth_state="unknown",
                ),
            )
            status_value = "accepted"
        else:
            raise ValueError("Invalid suggestion apply request")
        updated = self._set_suggestion_status(world_id, suggestion_id, status_value)
        return updated, entity, relationship, timeline_event, lore_note

    def create_timeline_event(
        self, world_id: UUID, data: TimelineEventCreate
    ) -> TimelineEventRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        event_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(t:TimelineEvent {
            id: $event_id, world_id: $w_id, title: $title,
            event_order: $event_order, description: $description,
            participants_json: $participants_json, causes: $causes,
            consequences: $consequences, created_at: $created_at,
            date_label: $date_label, era_label: $era_label,
            depends_on_json: $depends_on_json
        })
        RETURN properties(t) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                event_id=str(event_id),
                title=data.title,
                event_order=data.event_order,
                description=data.description,
                participants_json=json.dumps([str(item) for item in data.participants]),
                causes=data.causes,
                consequences=data.consequences,
                date_label=data.date_label,
                era_label=data.era_label,
                depends_on_json=json.dumps([str(item) for item in data.depends_on]),
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World not found")
            return self._timeline_event_from_record(record)

    def list_timeline_events(self, world_id: UUID) -> list[TimelineEventRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(t)
        WHERE type(belongs) = "BELONGS_TO" AND "TimelineEvent" IN labels(t)
        RETURN properties(t) AS props
        ORDER BY props.event_order ASC, props.created_at ASC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._timeline_event_from_record(record) for record in result]

    def create_graph_view(self, world_id: UUID, data: GraphViewCreate) -> GraphViewRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        view_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(v:GraphView {
            id: $view_id, world_id: $w_id, name: $name,
            layout_mode: $layout_mode, filters_json: $filters_json,
            camera_json: $camera_json, node_positions_json: $node_positions_json,
            created_at: $created_at, updated_at: $updated_at
        })
        RETURN properties(v) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                view_id=str(view_id),
                name=data.name,
                layout_mode=data.layout_mode,
                filters_json=json.dumps(data.filters, sort_keys=True),
                camera_json=data.camera.model_dump_json(),
                node_positions_json=json.dumps(data.node_positions, sort_keys=True),
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World not found")
            return self._graph_view_from_record(record)

    def list_graph_views(self, world_id: UUID) -> list[GraphViewRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(v)
        WHERE type(belongs) = "BELONGS_TO" AND "GraphView" IN labels(v)
        RETURN properties(v) AS props
        ORDER BY props.updated_at DESC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._graph_view_from_record(record) for record in result]

    def delete_graph_view(self, world_id: UUID, view_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (v)
        WHERE "GraphView" IN labels(v)
          AND properties(v).world_id = $w_id
          AND properties(v).id = $view_id
        DETACH DELETE v
        RETURN count(v) AS deleted
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), view_id=str(view_id))
            record = result.single()
            return bool(record and record["deleted"])

    def create_planning_board(self, world_id: UUID, data: PlanningBoardCreate) -> PlanningBoardRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        board_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(b:PlanningBoard {
            id: $board_id, world_id: $w_id, name: $name,
            board_type: $board_type, created_at: $created_at
        })
        RETURN properties(b) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                board_id=str(board_id),
                name=data.name,
                board_type=data.board_type,
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World not found")
            return self._planning_board_from_record(record)

    def list_planning_boards(self, world_id: UUID) -> list[PlanningBoardDetail] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(b)
        WHERE type(belongs) = "BELONGS_TO" AND "PlanningBoard" IN labels(b)
        RETURN properties(b) AS props
        ORDER BY props.created_at ASC
        """
        with self._driver.session() as session:
            boards = [self._planning_board_from_record(record) for record in session.run(query, w_id=str(world_id))]
        return [
            PlanningBoardDetail(**board.model_dump(), cards=self.list_planning_cards(world_id, board.id) or [])
            for board in boards
        ]

    def create_planning_card(
        self, world_id: UUID, board_id: UUID, data: PlanningCardCreate
    ) -> PlanningCardRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        card_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (b)
        WHERE "PlanningBoard" IN labels(b)
          AND properties(b).world_id = $w_id
          AND properties(b).id = $board_id
        CREATE (b)<-[:BELONGS_TO]-(c:PlanningCard {
            id: $card_id, board_id: $board_id, world_id: $w_id,
            title: $title, description: $description, lane: $lane,
            position: $position, entity_links_json: $entity_links_json,
            relationship_links_json: $relationship_links_json,
            timeline_event_links_json: $timeline_event_links_json,
            created_at: $created_at
        })
        RETURN properties(c) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                board_id=str(board_id),
                card_id=str(card_id),
                title=data.title,
                description=data.description,
                lane=data.lane,
                position=data.position,
                entity_links_json=json.dumps([str(item) for item in data.entity_links]),
                relationship_links_json=json.dumps([str(item) for item in data.relationship_links]),
                timeline_event_links_json=json.dumps([str(item) for item in data.timeline_event_links]),
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("Board not found")
            return self._planning_card_from_record(record)

    def list_planning_cards(self, world_id: UUID, board_id: UUID) -> list[PlanningCardRead] | None:
        query = """
        MATCH (b)<-[belongs]-(c)
        WHERE type(belongs) = "BELONGS_TO"
          AND "PlanningBoard" IN labels(b)
          AND "PlanningCard" IN labels(c)
          AND properties(b).world_id = $w_id
          AND properties(b).id = $board_id
        RETURN properties(c) AS props
        ORDER BY props.lane ASC, props.position ASC, props.created_at ASC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), board_id=str(board_id))
            return [self._planning_card_from_record(record) for record in result]

    def create_campaign_session(
        self, world_id: UUID, data: CampaignSessionCreate
    ) -> CampaignSessionRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        self._validate_campaign_links(world_id, data)
        session_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(cs:CampaignSession {
            id: $session_id, world_id: $w_id, session_number: $session_number,
            title: $title, played_date: $played_date, in_world_date: $in_world_date,
            recap: $recap, player_actions: $player_actions, consequences: $consequences,
            linked_entity_ids_json: $linked_entity_ids_json,
            linked_relationship_ids_json: $linked_relationship_ids_json,
            linked_timeline_event_ids_json: $linked_timeline_event_ids_json,
            created_at: $created_at, updated_at: $updated_at
        })
        RETURN properties(cs) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                session_id=str(session_id),
                session_number=data.session_number,
                title=data.title,
                played_date=data.played_date,
                in_world_date=data.in_world_date,
                recap=data.recap,
                player_actions=data.player_actions,
                consequences=data.consequences,
                linked_entity_ids_json=self._uuid_list_json(data.linked_entity_ids),
                linked_relationship_ids_json=self._uuid_list_json(data.linked_relationship_ids),
                linked_timeline_event_ids_json=self._uuid_list_json(data.linked_timeline_event_ids),
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            return self._campaign_session_from_record(result.single())

    def list_campaign_sessions(self, world_id: UUID) -> list[CampaignSessionRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(cs)
        WHERE type(belongs) = "BELONGS_TO" AND "CampaignSession" IN labels(cs)
        RETURN properties(cs) AS props
        ORDER BY props.session_number DESC, props.created_at DESC
        """
        with self._driver.session() as session:
            return [self._campaign_session_from_record(record) for record in session.run(query, w_id=str(world_id))]

    def update_campaign_session(
        self, world_id: UUID, session_id: UUID, data: CampaignSessionUpdate
    ) -> CampaignSessionRead | None:
        if not self._get_record(world_id):
            return None
        current = self._get_campaign_session(world_id, session_id)
        if not current:
            return None
        merged = CampaignSessionCreate(**(current.model_dump() | data.model_dump(exclude_unset=True)))
        self._validate_campaign_links(world_id, merged)
        now = datetime.now(UTC)
        query = """
        MATCH (cs)
        WHERE "CampaignSession" IN labels(cs)
          AND properties(cs).world_id = $w_id
          AND properties(cs).id = $session_id
        SET cs.session_number = $session_number,
            cs.title = $title,
            cs.played_date = $played_date,
            cs.in_world_date = $in_world_date,
            cs.recap = $recap,
            cs.player_actions = $player_actions,
            cs.consequences = $consequences,
            cs.linked_entity_ids_json = $linked_entity_ids_json,
            cs.linked_relationship_ids_json = $linked_relationship_ids_json,
            cs.linked_timeline_event_ids_json = $linked_timeline_event_ids_json,
            cs.updated_at = $updated_at
        RETURN properties(cs) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                session_id=str(session_id),
                session_number=merged.session_number,
                title=merged.title,
                played_date=merged.played_date,
                in_world_date=merged.in_world_date,
                recap=merged.recap,
                player_actions=merged.player_actions,
                consequences=merged.consequences,
                linked_entity_ids_json=self._uuid_list_json(merged.linked_entity_ids),
                linked_relationship_ids_json=self._uuid_list_json(merged.linked_relationship_ids),
                linked_timeline_event_ids_json=self._uuid_list_json(merged.linked_timeline_event_ids),
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._campaign_session_from_record(record) if record else None

    def delete_campaign_session(self, world_id: UUID, session_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        return self._delete_campaign_node(world_id, session_id, "CampaignSession", "cs")

    def create_lore_note(self, world_id: UUID, data: LoreNoteCreate) -> LoreNoteRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        self._validate_lore_subject(world_id, data.subject_type, data.subject_id)
        note_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(ln:LoreNote {
            id: $note_id, world_id: $w_id, title: $title, body: $body,
            subject_type: $subject_type, subject_id: $subject_id,
            visibility: $visibility, truth_state: $truth_state,
            reveal_condition: $reveal_condition, handout_text: $handout_text,
            created_at: $created_at, updated_at: $updated_at
        })
        RETURN properties(ln) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                note_id=str(note_id),
                title=data.title,
                body=data.body,
                subject_type=data.subject_type,
                subject_id=str(data.subject_id) if data.subject_id else None,
                visibility=data.visibility,
                truth_state=data.truth_state,
                reveal_condition=data.reveal_condition,
                handout_text=data.handout_text,
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            return self._lore_note_from_record(result.single())

    def list_lore_notes(self, world_id: UUID) -> list[LoreNoteRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(ln)
        WHERE type(belongs) = "BELONGS_TO" AND "LoreNote" IN labels(ln)
        RETURN properties(ln) AS props
        ORDER BY props.updated_at DESC, props.created_at DESC
        """
        with self._driver.session() as session:
            return [self._lore_note_from_record(record) for record in session.run(query, w_id=str(world_id))]

    def update_lore_note(
        self, world_id: UUID, note_id: UUID, data: LoreNoteUpdate
    ) -> LoreNoteRead | None:
        if not self._get_record(world_id):
            return None
        current = self._get_lore_note(world_id, note_id)
        if not current:
            return None
        merged = LoreNoteCreate(**(current.model_dump() | data.model_dump(exclude_unset=True)))
        self._validate_lore_subject(world_id, merged.subject_type, merged.subject_id)
        now = datetime.now(UTC)
        query = """
        MATCH (ln)
        WHERE "LoreNote" IN labels(ln)
          AND properties(ln).world_id = $w_id
          AND properties(ln).id = $note_id
        SET ln.title = $title,
            ln.body = $body,
            ln.subject_type = $subject_type,
            ln.subject_id = $subject_id,
            ln.visibility = $visibility,
            ln.truth_state = $truth_state,
            ln.reveal_condition = $reveal_condition,
            ln.handout_text = $handout_text,
            ln.updated_at = $updated_at
        RETURN properties(ln) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                note_id=str(note_id),
                title=merged.title,
                body=merged.body,
                subject_type=merged.subject_type,
                subject_id=str(merged.subject_id) if merged.subject_id else None,
                visibility=merged.visibility,
                truth_state=merged.truth_state,
                reveal_condition=merged.reveal_condition,
                handout_text=merged.handout_text,
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._lore_note_from_record(record) if record else None

    def delete_lore_note(self, world_id: UUID, note_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        return self._delete_campaign_node(world_id, note_id, "LoreNote", "ln")

    def create_faction_clock(self, world_id: UUID, data: FactionClockCreate) -> FactionClockRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        self._validate_clock_links(world_id, data)
        clock_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(fc:FactionClock {
            id: $clock_id, world_id: $w_id, title: $title,
            linked_entity_id: $linked_entity_id, segments: $segments,
            filled_segments: $filled_segments, stakes: $stakes, status: $status,
            linked_session_ids_json: $linked_session_ids_json,
            linked_entity_ids_json: $linked_entity_ids_json,
            linked_relationship_ids_json: $linked_relationship_ids_json,
            linked_timeline_event_ids_json: $linked_timeline_event_ids_json,
            created_at: $created_at, updated_at: $updated_at
        })
        RETURN properties(fc) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                clock_id=str(clock_id),
                title=data.title,
                linked_entity_id=str(data.linked_entity_id) if data.linked_entity_id else None,
                segments=data.segments,
                filled_segments=data.filled_segments,
                stakes=data.stakes,
                status=data.status,
                linked_session_ids_json=self._uuid_list_json(data.linked_session_ids),
                linked_entity_ids_json=self._uuid_list_json(data.linked_entity_ids),
                linked_relationship_ids_json=self._uuid_list_json(data.linked_relationship_ids),
                linked_timeline_event_ids_json=self._uuid_list_json(data.linked_timeline_event_ids),
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            return self._faction_clock_from_record(result.single())

    def list_faction_clocks(self, world_id: UUID) -> list[FactionClockRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(fc)
        WHERE type(belongs) = "BELONGS_TO" AND "FactionClock" IN labels(fc)
        RETURN properties(fc) AS props
        ORDER BY props.status ASC, props.updated_at DESC
        """
        with self._driver.session() as session:
            return [self._faction_clock_from_record(record) for record in session.run(query, w_id=str(world_id))]

    def update_faction_clock(
        self, world_id: UUID, clock_id: UUID, data: FactionClockUpdate
    ) -> FactionClockRead | None:
        if not self._get_record(world_id):
            return None
        current = self._get_faction_clock(world_id, clock_id)
        if not current:
            return None
        merged = FactionClockCreate(**(current.model_dump() | data.model_dump(exclude_unset=True)))
        self._validate_clock_links(world_id, merged)
        now = datetime.now(UTC)
        query = """
        MATCH (fc)
        WHERE "FactionClock" IN labels(fc)
          AND properties(fc).world_id = $w_id
          AND properties(fc).id = $clock_id
        SET fc.title = $title,
            fc.linked_entity_id = $linked_entity_id,
            fc.segments = $segments,
            fc.filled_segments = $filled_segments,
            fc.stakes = $stakes,
            fc.status = $status,
            fc.linked_session_ids_json = $linked_session_ids_json,
            fc.linked_entity_ids_json = $linked_entity_ids_json,
            fc.linked_relationship_ids_json = $linked_relationship_ids_json,
            fc.linked_timeline_event_ids_json = $linked_timeline_event_ids_json,
            fc.updated_at = $updated_at
        RETURN properties(fc) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                clock_id=str(clock_id),
                title=merged.title,
                linked_entity_id=str(merged.linked_entity_id) if merged.linked_entity_id else None,
                segments=merged.segments,
                filled_segments=merged.filled_segments,
                stakes=merged.stakes,
                status=merged.status,
                linked_session_ids_json=self._uuid_list_json(merged.linked_session_ids),
                linked_entity_ids_json=self._uuid_list_json(merged.linked_entity_ids),
                linked_relationship_ids_json=self._uuid_list_json(merged.linked_relationship_ids),
                linked_timeline_event_ids_json=self._uuid_list_json(merged.linked_timeline_event_ids),
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._faction_clock_from_record(record) if record else None

    def delete_faction_clock(self, world_id: UUID, clock_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        return self._delete_campaign_node(world_id, clock_id, "FactionClock", "fc")

    def create_session_impact_review(
        self, world_id: UUID, session_id: UUID, instruction: str | None = None
    ) -> GenerationSuggestionRead | None:
        session = self._get_campaign_session(world_id, session_id)
        if not session:
            return None
        content = (
            f"Session {session.session_number}: {session.title}\n\n"
            f"Recap:\n{session.recap or 'No recap recorded.'}\n\n"
            f"Player actions:\n{session.player_actions or 'No player actions recorded.'}\n\n"
            f"Consequences to review:\n{session.consequences or 'No consequences recorded.'}"
        )
        return self.create_generation_suggestion(
            world_id=world_id,
            instruction=instruction or f"Review campaign impact for session {session.session_number}",
            content=content,
            suggested_name=f"Session {session.session_number} Impact Review",
            suggested_type="Event",
        )

    def list_revisions(
        self, world_id: UUID, entity_id: UUID | None = None
    ) -> list[RevisionVersionRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (r)
        WHERE "RevisionVersion" IN labels(r)
          AND properties(r).world_id = $w_id
          AND ($entity_id IS NULL OR properties(r).entity_id = $entity_id)
        RETURN properties(r) AS props
        ORDER BY props.created_at DESC
        """
        with self._driver.session() as session:
            result = session.run(
                query, w_id=str(world_id), entity_id=str(entity_id) if entity_id else None
            )
            return [self._revision_from_record(record) for record in result]

    def restore_revision(
        self, world_id: UUID, revision_id: UUID
    ) -> EntityRead | None:
        revisions = self.list_revisions(world_id) or []
        revision = next((item for item in revisions if item.id == revision_id), None)
        if not revision or revision.subject_type != "entity" or not revision.entity_id:
            return None
        entity = self.update_entity(
            world_id, revision.entity_id, EntityUpdate(description=revision.previous_value or "")
        )
        if entity:
            self._record_revision(
                world_id,
                entity.id,
                "entity",
                "description",
                revision.new_value,
                revision.previous_value,
                "restore",
            )
        return entity

    def passage_check(self, world_id: UUID, passage: str) -> PassageCheckResponse | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        entities = self.list_entities(world_id) or []
        issues: list[PassageCheckIssue] = []
        lower_passage = passage.lower()
        mentioned = [
            entity
            for entity in entities
            if entity.name.lower() in lower_passage
            or any(word and word in lower_passage for word in entity.name.lower().split())
        ]
        if not mentioned:
            issues.append(
                PassageCheckIssue(
                    code="missing_setup",
                    severity="warning",
                    message="The passage does not mention saved canon entities by name.",
                )
            )
        if rec.tone and rec.tone.lower() not in lower_passage:
            issues.append(
                PassageCheckIssue(
                    code="tone_drift",
                    severity="info",
                    message="The passage may need a tone pass against the world's stated tone.",
                )
            )
        contradiction_cues = ("never", "always", "impossible", "only", "last")
        for entity in mentioned:
            entity_text = entity.description.lower()
            if any(cue in lower_passage and cue in entity_text for cue in contradiction_cues):
                issues.append(
                    PassageCheckIssue(
                        code="canon_absolute",
                        severity="warning",
                        message=f"{entity.name} uses absolute wording in both passage and canon; verify continuity.",
                        entity_id=entity.id,
                    )
                )
            if entity.entity_type.lower() in {"event", "historical event"} and not any(
                cue in lower_passage for cue in ("before", "after", "during", "year", "season", "night")
            ):
                issues.append(
                    PassageCheckIssue(
                        code="timeline_context",
                        severity="info",
                        message=f"{entity.name} is referenced without clear chronology.",
                        entity_id=entity.id,
                    )
                )
        summary = "Passage check found no heuristic warnings."
        if issues:
            summary = f"Passage check found {len(issues)} item(s) to review."
        return PassageCheckResponse(world_id=world_id, summary=summary, issues=issues)

    def extract_draft_excerpt(
        self,
        world_id: UUID,
        draft_id: UUID,
        excerpt: str,
        instruction: str | None = None,
        max_candidates: int = 6,
    ) -> DraftExtractionResponse | None:
        draft = self.get_draft(world_id, draft_id)
        if not draft:
            return None
        excerpt = excerpt.strip()
        if not excerpt:
            raise ValueError("Excerpt is required")
        if excerpt not in draft.body:
            raise ValueError("Excerpt must be selected from the saved draft body")

        candidates = self._llm_extract_draft_candidates(
            world_id, draft.title, excerpt, instruction, max_candidates
        )
        if not candidates:
            candidates = self._fallback_extract_draft_candidates(world_id, excerpt)
        candidates = self._dedupe_draft_candidates(candidates)[:max_candidates]

        suggestions = [
            self.create_generation_suggestion(
                world_id=world_id,
                instruction=instruction or f"Extract canon candidate from draft: {draft.title}",
                content=str(candidate["content"]),
                suggested_name=str(candidate["suggested_name"]),
                suggested_type=str(candidate.get("suggested_type") or candidate["candidate_kind"]),
                candidate_kind=str(candidate["candidate_kind"]),
                source_type="draft",
                source_id=draft_id,
                source_excerpt=excerpt,
                payload=(
                    dict(payload)
                    if isinstance((payload := candidate.get("payload")), dict)
                    else {}
                ),
            )
            for candidate in candidates
        ]
        summary = (
            f"Queued {len(suggestions)} canon suggestion(s) from selected draft excerpt."
            if suggestions
            else "No canon suggestions could be extracted from the selected excerpt."
        )
        return DraftExtractionResponse(
            world_id=world_id,
            draft_id=draft_id,
            summary=summary,
            suggestions=suggestions,
        )

    def create_draft(self, world_id: UUID, data: DraftCreate) -> DraftRead:
        if not self._get_record(world_id):
            raise ValueError("World not found")
        draft_id = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        CREATE (w)<-[:BELONGS_TO]-(d:DraftPassage {
            id: $draft_id, world_id: $w_id, title: $title, body: $body,
            status: $status, linked_entity_ids_json: $linked_entity_ids_json,
            linked_relationship_ids_json: $linked_relationship_ids_json,
            linked_timeline_event_ids_json: $linked_timeline_event_ids_json,
            check_history_json: $check_history_json,
            created_at: $created_at, updated_at: $updated_at
        })
        RETURN properties(d) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                draft_id=str(draft_id),
                title=data.title,
                body=data.body,
                status=data.status,
                linked_entity_ids_json=json.dumps([str(item) for item in data.linked_entity_ids]),
                linked_relationship_ids_json=json.dumps(
                    [str(item) for item in data.linked_relationship_ids]
                ),
                linked_timeline_event_ids_json=json.dumps(
                    [str(item) for item in data.linked_timeline_event_ids]
                ),
                check_history_json="[]",
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("World not found")
            return self._draft_from_record(record)

    def list_drafts(self, world_id: UUID) -> list[DraftRead] | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        MATCH (w)<-[belongs]-(d)
        WHERE type(belongs) = "BELONGS_TO" AND "DraftPassage" IN labels(d)
        RETURN properties(d) AS props
        ORDER BY props.updated_at DESC, props.created_at DESC
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id))
            return [self._draft_from_record(record) for record in result]

    def get_draft(self, world_id: UUID, draft_id: UUID) -> DraftRead | None:
        query = """
        MATCH (d)
        WHERE "DraftPassage" IN labels(d)
          AND properties(d).world_id = $w_id
          AND properties(d).id = $draft_id
        RETURN properties(d) AS props
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), draft_id=str(draft_id))
            record = result.single()
            return self._draft_from_record(record) if record else None

    def update_draft(self, world_id: UUID, draft_id: UUID, data: DraftUpdate) -> DraftRead | None:
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return self.get_draft(world_id, draft_id)
        now = datetime.now(UTC)
        query = """
        MATCH (d)
        WHERE "DraftPassage" IN labels(d)
          AND properties(d).world_id = $w_id
          AND properties(d).id = $draft_id
        SET d.title = coalesce($title, d.title),
            d.body = coalesce($body, d.body),
            d.status = coalesce($status, d.status),
            d.linked_entity_ids_json = coalesce($linked_entity_ids_json, d.linked_entity_ids_json),
            d.linked_relationship_ids_json = coalesce($linked_relationship_ids_json, d.linked_relationship_ids_json),
            d.linked_timeline_event_ids_json = coalesce($linked_timeline_event_ids_json, d.linked_timeline_event_ids_json),
            d.updated_at = $updated_at
        RETURN properties(d) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                draft_id=str(draft_id),
                title=updates.get("title"),
                body=updates.get("body"),
                status=updates.get("status"),
                linked_entity_ids_json=(
                    json.dumps([str(item) for item in updates["linked_entity_ids"]])
                    if "linked_entity_ids" in updates
                    else None
                ),
                linked_relationship_ids_json=(
                    json.dumps([str(item) for item in updates["linked_relationship_ids"]])
                    if "linked_relationship_ids" in updates
                    else None
                ),
                linked_timeline_event_ids_json=(
                    json.dumps([str(item) for item in updates["linked_timeline_event_ids"]])
                    if "linked_timeline_event_ids" in updates
                    else None
                ),
                updated_at=now.isoformat(),
            )
            record = result.single()
            return self._draft_from_record(record) if record else None

    def delete_draft(self, world_id: UUID, draft_id: UUID) -> bool | None:
        if not self._get_record(world_id):
            return None
        query = """
        MATCH (d)
        WHERE "DraftPassage" IN labels(d)
          AND properties(d).world_id = $w_id
          AND properties(d).id = $draft_id
        DETACH DELETE d
        RETURN count(d) AS deleted
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), draft_id=str(draft_id))
            record = result.single()
            return bool(record and record["deleted"])

    def check_draft(self, world_id: UUID, draft_id: UUID) -> PassageCheckResponse | None:
        draft = self.get_draft(world_id, draft_id)
        if not draft:
            return None
        report = self.passage_check(world_id, draft.body)
        if not report:
            return None
        history = [
            {
                "checked_at": item.checked_at.isoformat(),
                "summary": item.summary,
                "issues": [issue.model_dump(mode="json") for issue in item.issues],
            }
            for item in draft.check_history
        ]
        history.append(
            {
                "checked_at": datetime.now(UTC).isoformat(),
                "summary": report.summary,
                "issues": [issue.model_dump(mode="json") for issue in report.issues],
            }
        )
        query = """
        MATCH (d)
        WHERE "DraftPassage" IN labels(d)
          AND properties(d).world_id = $w_id
          AND properties(d).id = $draft_id
        SET d.check_history_json = $check_history_json,
            d.updated_at = $updated_at
        RETURN properties(d) AS props
        """
        with self._driver.session() as session:
            session.run(
                query,
                w_id=str(world_id),
                draft_id=str(draft_id),
                check_history_json=json.dumps(history),
                updated_at=datetime.now(UTC).isoformat(),
            )
        return report

    def _llm_extract_draft_candidates(
        self,
        world_id: UUID,
        draft_title: str,
        excerpt: str,
        instruction: str | None,
        max_candidates: int,
    ) -> list[dict[str, object]]:
        rec = self._get_record(world_id)
        if not rec or not self._llm or not self._llm.enabled():
            return []
        prompt = (
            "Extract canon candidates from this draft excerpt. Return only JSON with a "
            '"candidates" array. Each candidate must have candidate_kind '
            '("entity", "relationship", "timeline_event", or "lore_note"), '
            "suggested_name, content, optional suggested_type, and optional payload. "
            "Do not create canon directly. "
            f"Maximum candidates: {max_candidates}. Draft title: {draft_title}. "
            f"User instruction: {instruction or 'none'}.\n\nExcerpt:\n{excerpt}"
        )
        raw = self._llm.generate_agentic(self._to_read(rec), self.get_world_context(world_id), prompt)
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        raw_candidates = parsed.get("candidates") if isinstance(parsed, dict) else parsed
        if not isinstance(raw_candidates, list):
            return []
        candidates: list[dict[str, object]] = []
        for item in raw_candidates:
            candidate = self._normalize_draft_candidate(item)
            if candidate:
                candidates.append(candidate)
        return candidates

    def _fallback_extract_draft_candidates(
        self, world_id: UUID, excerpt: str
    ) -> list[dict[str, object]]:
        entities = self.list_entities(world_id) or []
        entity_by_name = {entity.name: entity for entity in entities}
        lower_existing = {entity.name.lower() for entity in entities}
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", excerpt)
            if sentence.strip()
        ] or [excerpt]
        candidates: list[dict[str, object]] = []

        for sentence in sentences:
            matched = [
                entity for name, entity in entity_by_name.items()
                if re.search(rf"\b{re.escape(name)}\b", sentence)
            ]
            if len(matched) >= 2:
                candidates.append({
                    "candidate_kind": "relationship",
                    "suggested_name": f"{matched[0].name} / {matched[1].name}",
                    "suggested_type": "related_to",
                    "content": sentence,
                    "payload": {
                        "source_entity_id": str(matched[0].id),
                        "target_entity_id": str(matched[1].id),
                        "relation_type": "related_to",
                        "notes": sentence,
                    },
                })
            if re.search(r"\b(before|after|during|year|season|night|day|month|century|era)\b", sentence, re.I):
                candidates.append({
                    "candidate_kind": "timeline_event",
                    "suggested_name": self._candidate_title(sentence),
                    "suggested_type": "event",
                    "content": sentence,
                    "payload": {
                        "title": self._candidate_title(sentence),
                        "description": sentence,
                        "participants": [str(entity.id) for entity in matched],
                    },
                })

        for name in re.findall(r"\b[A-Z][a-zA-Z'’-]+(?:\s+[A-Z][a-zA-Z'’-]+){0,3}\b", excerpt):
            clean_name = name.strip(" ,.;:!?")
            if len(clean_name) < 2 or clean_name.lower() in lower_existing:
                continue
            if clean_name in {"Before", "After", "During", "The", "A", "An"}:
                continue
            candidates.append({
                "candidate_kind": "entity",
                "suggested_name": clean_name,
                "suggested_type": "Concept",
                "content": excerpt,
                "payload": {
                    "name": clean_name,
                    "entity_type": "Concept",
                    "description": excerpt,
                },
            })

        if not candidates:
            candidates.append({
                "candidate_kind": "lore_note",
                "suggested_name": "Draft lore note",
                "suggested_type": "lore_note",
                "content": excerpt,
                "payload": {"title": "Draft lore note", "body": excerpt},
            })
        return candidates

    @staticmethod
    def _normalize_draft_candidate(item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        kind = item.get("candidate_kind") or item.get("kind")
        if kind not in {"entity", "relationship", "timeline_event", "lore_note"}:
            return None
        content = item.get("content") or item.get("description") or item.get("body")
        suggested_name = item.get("suggested_name") or item.get("name") or item.get("title")
        if not isinstance(content, str) or not content.strip():
            return None
        if not isinstance(suggested_name, str) or not suggested_name.strip():
            suggested_name = WorldService._candidate_title(content)
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        return {
            "candidate_kind": kind,
            "suggested_name": suggested_name.strip()[:200],
            "suggested_type": str(item.get("suggested_type") or kind)[:100],
            "content": content.strip(),
            "payload": payload,
        }

    @staticmethod
    def _dedupe_draft_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
        seen: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, object]] = []
        for candidate in candidates:
            key = (
                str(candidate.get("candidate_kind", "")).lower(),
                str(candidate.get("suggested_name", "")).strip().lower(),
                str(candidate.get("content", "")).strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    @staticmethod
    def _candidate_title(text: str) -> str:
        words = re.findall(r"[A-Za-z0-9'’-]+", text)
        title = " ".join(words[:8]).strip()
        return title[:200] or "Draft candidate"

    @staticmethod
    def _looks_like_uuid(value: str) -> bool:
        try:
            UUID(value)
        except ValueError:
            return False
        return True

    def _get_suggestion(
        self, world_id: UUID, suggestion_id: UUID
    ) -> GenerationSuggestionRead | None:
        query = """
        MATCH (s)
        WHERE "CanonSuggestion" IN labels(s)
          AND properties(s).world_id = $w_id
          AND properties(s).id = $s_id
        RETURN properties(s) AS props
        """
        with self._driver.session() as session:
            result = session.run(query, w_id=str(world_id), s_id=str(suggestion_id))
            record = result.single()
            return self._suggestion_from_record(record) if record else None

    def _set_suggestion_status(
        self, world_id: UUID, suggestion_id: UUID, status_value: str
    ) -> GenerationSuggestionRead:
        query = """
        MATCH (s)
        WHERE "CanonSuggestion" IN labels(s)
          AND properties(s).world_id = $w_id
          AND properties(s).id = $s_id
        SET s.status = $status
        RETURN properties(s) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query, w_id=str(world_id), s_id=str(suggestion_id), status=status_value
            )
            record = result.single()
            if not record:
                raise ValueError("Suggestion not found")
            return self._suggestion_from_record(record)

    def _record_revision(
        self,
        world_id: UUID,
        entity_id: UUID | None,
        subject_type: str,
        field_name: str,
        previous_value: str | None,
        new_value: str | None,
        source: str,
    ) -> RevisionVersionRead:
        revision_id = uuid4()
        now = datetime.now(UTC)
        query = """
        CREATE (r:RevisionVersion {
            id: $revision_id, world_id: $w_id, entity_id: $entity_id,
            subject_type: $subject_type, field_name: $field_name,
            previous_value: $previous_value, new_value: $new_value,
            source: $source, created_at: $created_at
        })
        RETURN properties(r) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                revision_id=str(revision_id),
                w_id=str(world_id),
                entity_id=str(entity_id) if entity_id else None,
                subject_type=subject_type,
                field_name=field_name,
                previous_value=previous_value,
                new_value=new_value,
                source=source,
                created_at=now.isoformat(),
            )
            return self._revision_from_record(result.single())

    def _get_campaign_session(self, world_id: UUID, session_id: UUID) -> CampaignSessionRead | None:
        query = """
        MATCH (cs)
        WHERE "CampaignSession" IN labels(cs)
          AND properties(cs).world_id = $w_id
          AND properties(cs).id = $session_id
        RETURN properties(cs) AS props
        """
        with self._driver.session() as session:
            record = session.run(query, w_id=str(world_id), session_id=str(session_id)).single()
            return self._campaign_session_from_record(record) if record else None

    def _get_lore_note(self, world_id: UUID, note_id: UUID) -> LoreNoteRead | None:
        query = """
        MATCH (ln)
        WHERE "LoreNote" IN labels(ln)
          AND properties(ln).world_id = $w_id
          AND properties(ln).id = $note_id
        RETURN properties(ln) AS props
        """
        with self._driver.session() as session:
            record = session.run(query, w_id=str(world_id), note_id=str(note_id)).single()
            return self._lore_note_from_record(record) if record else None

    def _get_faction_clock(self, world_id: UUID, clock_id: UUID) -> FactionClockRead | None:
        query = """
        MATCH (fc)
        WHERE "FactionClock" IN labels(fc)
          AND properties(fc).world_id = $w_id
          AND properties(fc).id = $clock_id
        RETURN properties(fc) AS props
        """
        with self._driver.session() as session:
            record = session.run(query, w_id=str(world_id), clock_id=str(clock_id)).single()
            return self._faction_clock_from_record(record) if record else None

    def _delete_campaign_node(self, world_id: UUID, node_id: UUID, label: str, alias: str) -> bool:
        query = f"""
        MATCH ({alias})
        WHERE "{label}" IN labels({alias})
          AND properties({alias}).world_id = $w_id
          AND properties({alias}).id = $node_id
        DETACH DELETE {alias}
        RETURN count({alias}) AS deleted
        """
        with self._driver.session() as session:
            record = session.run(query, w_id=str(world_id), node_id=str(node_id)).single()
            return bool(record and record["deleted"])

    def _validate_campaign_links(self, world_id: UUID, data: CampaignSessionCreate) -> None:
        self._require_entity_ids(world_id, data.linked_entity_ids)
        self._require_relationship_ids(world_id, data.linked_relationship_ids)
        self._require_timeline_event_ids(world_id, data.linked_timeline_event_ids)

    def _validate_clock_links(self, world_id: UUID, data: FactionClockCreate) -> None:
        if data.linked_entity_id:
            self._require_entity_ids(world_id, [data.linked_entity_id])
        self._require_session_ids(world_id, data.linked_session_ids)
        self._require_entity_ids(world_id, data.linked_entity_ids)
        self._require_relationship_ids(world_id, data.linked_relationship_ids)
        self._require_timeline_event_ids(world_id, data.linked_timeline_event_ids)
        if data.filled_segments > data.segments:
            raise ValueError("Filled segments cannot exceed segments")

    def _validate_lore_subject(
        self, world_id: UUID, subject_type: str, subject_id: UUID | None
    ) -> None:
        if subject_type == "world":
            return
        if not subject_id:
            raise ValueError("Subject id is required")
        if subject_type == "entity":
            self._require_entity_ids(world_id, [subject_id])
        elif subject_type == "relationship":
            self._require_relationship_ids(world_id, [subject_id])
        elif subject_type == "timeline_event":
            self._require_timeline_event_ids(world_id, [subject_id])
        elif subject_type == "session":
            self._require_session_ids(world_id, [subject_id])

    def _require_entity_ids(self, world_id: UUID, ids: list[UUID]) -> None:
        for item in ids:
            if not self.get_entity(world_id, item):
                raise ValueError("Invalid linked entity id")

    def _require_relationship_ids(self, world_id: UUID, ids: list[UUID]) -> None:
        existing = {relationship.id for relationship in (self.list_relationships(world_id) or [])}
        if any(item not in existing for item in ids):
            raise ValueError("Invalid linked relationship id")

    def _require_timeline_event_ids(self, world_id: UUID, ids: list[UUID]) -> None:
        existing = {event.id for event in (self.list_timeline_events(world_id) or [])}
        if any(item not in existing for item in ids):
            raise ValueError("Invalid linked timeline event id")

    def _require_session_ids(self, world_id: UUID, ids: list[UUID]) -> None:
        existing = {session.id for session in (self.list_campaign_sessions(world_id) or [])}
        if any(item not in existing for item in ids):
            raise ValueError("Invalid linked session id")

    @staticmethod
    def _entity_from_record(record) -> EntityRead:  # noqa: ANN001
        props = record.get("props", record)
        return EntityRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            name=props["name"],
            entity_type=props["entity_type"],
            description=props["description"],
            structured_fields=WorldService._decode_structured_fields(
                props.get("structured_fields_json")
            ),
            created_at=datetime.fromisoformat(props["created_at"]),
        )

    @staticmethod
    def _relationship_from_record(record) -> RelationshipRead:  # noqa: ANN001
        keys = set(record.keys()) if hasattr(record, "keys") else set(record)
        if "rel_props" in keys:
            rel_props = record["rel_props"]
            source_props = record["source_props"]
            target_props = record["target_props"]
            return RelationshipRead(
                id=UUID(rel_props["id"]),
                world_id=UUID(rel_props["world_id"]),
                source_entity_id=UUID(source_props["id"]),
                source_entity_name=source_props["name"],
                target_entity_id=UUID(target_props["id"]),
                target_entity_name=target_props["name"],
                relation_type=rel_props["relation_type"],
                notes=rel_props.get("notes"),
                category=rel_props.get("category"),
                strength=rel_props.get("strength"),
                history=rel_props.get("history"),
                stance=rel_props.get("stance"),
                color=rel_props.get("color"),
                display_priority=rel_props.get("display_priority"),
                created_at=datetime.fromisoformat(rel_props["created_at"]),
            )
        return RelationshipRead(
            id=UUID(record["id"]),
            world_id=UUID(record["world_id"]),
            source_entity_id=UUID(record["source_entity_id"]),
            source_entity_name=record["source_entity_name"],
            target_entity_id=UUID(record["target_entity_id"]),
            target_entity_name=record["target_entity_name"],
            relation_type=record["relation_type"],
            notes=record.get("notes"),
            category=record.get("category"),
            strength=record.get("strength"),
            history=record.get("history"),
            stance=record.get("stance"),
            color=record.get("color"),
            display_priority=record.get("display_priority"),
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    @staticmethod
    def _suggestion_from_record(record) -> GenerationSuggestionRead:  # noqa: ANN001
        props = record.get("props", record)
        return GenerationSuggestionRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            instruction=props["instruction"],
            content=props["content"],
            suggested_name=props.get("suggested_name"),
            suggested_type=props.get("suggested_type"),
            status=props.get("status", "pending"),
            created_at=datetime.fromisoformat(props["created_at"]),
            candidate_kind=props.get("candidate_kind"),
            source_type=props.get("source_type"),
            source_id=UUID(props["source_id"]) if props.get("source_id") else None,
            source_excerpt=props.get("source_excerpt"),
            payload=WorldService._decode_payload(props.get("payload_json")),
        )

    @staticmethod
    def _timeline_event_from_record(record) -> TimelineEventRead:  # noqa: ANN001
        props = record.get("props", record)
        return TimelineEventRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            title=props["title"],
            event_order=int(props["event_order"]),
            description=props.get("description") or "",
            participants=[
                UUID(item)
                for item in json.loads(props.get("participants_json") or "[]")
            ],
            causes=props.get("causes"),
            consequences=props.get("consequences"),
            date_label=props.get("date_label"),
            era_label=props.get("era_label"),
            depends_on=[
                UUID(item)
                for item in json.loads(props.get("depends_on_json") or "[]")
            ],
            created_at=datetime.fromisoformat(props["created_at"]),
        )

    @staticmethod
    def _graph_view_from_record(record) -> GraphViewRead:  # noqa: ANN001
        props = record.get("props", record)
        camera = json.loads(props.get("camera_json") or "{}")
        return GraphViewRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            name=props["name"],
            layout_mode=props.get("layout_mode", "manual"),
            filters=json.loads(props.get("filters_json") or "{}"),
            camera=camera,
            node_positions=json.loads(props.get("node_positions_json") or "{}"),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props.get("updated_at") or props["created_at"]),
        )

    @staticmethod
    def _planning_board_from_record(record) -> PlanningBoardRead:  # noqa: ANN001
        props = record.get("props", record)
        return PlanningBoardRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            name=props["name"],
            board_type=props.get("board_type", "plot_thread"),
            created_at=datetime.fromisoformat(props["created_at"]),
        )

    @staticmethod
    def _planning_card_from_record(record) -> PlanningCardRead:  # noqa: ANN001
        props = record.get("props", record)
        return PlanningCardRead(
            id=UUID(props["id"]),
            board_id=UUID(props["board_id"]),
            world_id=UUID(props["world_id"]),
            title=props["title"],
            description=props.get("description") or "",
            lane=props.get("lane") or "Backlog",
            position=int(props.get("position") or 0),
            entity_links=[UUID(item) for item in json.loads(props.get("entity_links_json") or "[]")],
            relationship_links=[
                UUID(item) for item in json.loads(props.get("relationship_links_json") or "[]")
            ],
            timeline_event_links=[
                UUID(item) for item in json.loads(props.get("timeline_event_links_json") or "[]")
            ],
            created_at=datetime.fromisoformat(props["created_at"]),
        )

    @staticmethod
    def _campaign_session_from_record(record) -> CampaignSessionRead:  # noqa: ANN001
        props = record.get("props", record)
        return CampaignSessionRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            session_number=int(props["session_number"]),
            title=props["title"],
            played_date=props.get("played_date"),
            in_world_date=props.get("in_world_date"),
            recap=props.get("recap") or "",
            player_actions=props.get("player_actions") or "",
            consequences=props.get("consequences") or "",
            linked_entity_ids=WorldService._decode_uuid_list(props.get("linked_entity_ids_json")),
            linked_relationship_ids=WorldService._decode_uuid_list(props.get("linked_relationship_ids_json")),
            linked_timeline_event_ids=WorldService._decode_uuid_list(props.get("linked_timeline_event_ids_json")),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props.get("updated_at") or props["created_at"]),
        )

    @staticmethod
    def _lore_note_from_record(record) -> LoreNoteRead:  # noqa: ANN001
        props = record.get("props", record)
        return LoreNoteRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            title=props["title"],
            body=props.get("body") or "",
            subject_type=props.get("subject_type", "world"),
            subject_id=UUID(props["subject_id"]) if props.get("subject_id") else None,
            visibility=props.get("visibility", "dm_only"),
            truth_state=props.get("truth_state", "unknown"),
            reveal_condition=props.get("reveal_condition"),
            handout_text=props.get("handout_text"),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props.get("updated_at") or props["created_at"]),
        )

    @staticmethod
    def _faction_clock_from_record(record) -> FactionClockRead:  # noqa: ANN001
        props = record.get("props", record)
        return FactionClockRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            title=props["title"],
            linked_entity_id=UUID(props["linked_entity_id"]) if props.get("linked_entity_id") else None,
            segments=int(props.get("segments") or 6),
            filled_segments=int(props.get("filled_segments") or 0),
            stakes=props.get("stakes") or "",
            status=props.get("status", "active"),
            linked_session_ids=WorldService._decode_uuid_list(props.get("linked_session_ids_json")),
            linked_entity_ids=WorldService._decode_uuid_list(props.get("linked_entity_ids_json")),
            linked_relationship_ids=WorldService._decode_uuid_list(props.get("linked_relationship_ids_json")),
            linked_timeline_event_ids=WorldService._decode_uuid_list(props.get("linked_timeline_event_ids_json")),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props.get("updated_at") or props["created_at"]),
        )

    @staticmethod
    def _revision_from_record(record) -> RevisionVersionRead:  # noqa: ANN001
        props = record.get("props", record)
        return RevisionVersionRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            entity_id=UUID(props["entity_id"]) if props.get("entity_id") else None,
            subject_type=props["subject_type"],
            field_name=props["field_name"],
            previous_value=props.get("previous_value"),
            new_value=props.get("new_value"),
            source=props.get("source", "manual"),
            created_at=datetime.fromisoformat(props["created_at"]),
        )

    @staticmethod
    def _draft_from_record(record) -> DraftRead:  # noqa: ANN001
        props = record.get("props", record)
        return DraftRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            title=props["title"],
            body=props["body"],
            status=props.get("status", "draft"),
            linked_entity_ids=[
                UUID(item) for item in json.loads(props.get("linked_entity_ids_json") or "[]")
            ],
            linked_relationship_ids=[
                UUID(item)
                for item in json.loads(props.get("linked_relationship_ids_json") or "[]")
            ],
            linked_timeline_event_ids=[
                UUID(item)
                for item in json.loads(props.get("linked_timeline_event_ids_json") or "[]")
            ],
            check_history=WorldService._decode_draft_check_history(
                props.get("check_history_json")
            ),
            created_at=datetime.fromisoformat(props["created_at"]),
            updated_at=datetime.fromisoformat(props.get("updated_at") or props["created_at"]),
        )

    @staticmethod
    def _world_from_props(props: dict[str, object]) -> _WorldRecord:
        return _WorldRecord(
            id=UUID(str(props["id"])),
            title=str(props["title"]),
            tone=str(props["tone"]) if props.get("tone") is not None else None,
            era_notes=str(props["era_notes"]) if props.get("era_notes") is not None else None,
            seed=str(props["seed"]) if props.get("seed") is not None else None,
            created_at=datetime.fromisoformat(str(props["created_at"])),
        )

    @staticmethod
    def _display_entity_type(entity_type: str) -> str:
        return display_entity_type(entity_type)

    @staticmethod
    def _decode_structured_fields(raw: object) -> dict[str, str]:
        if not raw:
            return {}
        if isinstance(raw, dict):
            return {str(key): str(value) for key, value in raw.items()}
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(key): str(value) for key, value in parsed.items()}

    @staticmethod
    def _uuid_list_json(items: list[UUID]) -> str:
        return json.dumps([str(item) for item in items])

    @staticmethod
    def _decode_uuid_list(raw: object) -> list[UUID]:
        if not raw:
            return []
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [UUID(str(item)) for item in parsed]

    @staticmethod
    def _decode_draft_check_history(raw: object) -> list[DraftCheckHistoryItem]:
        if not raw:
            return []
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        history: list[DraftCheckHistoryItem] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            issues = []
            for issue in item.get("issues", []):
                if isinstance(issue, dict):
                    issues.append(PassageCheckIssue(**issue))
            history.append(
                DraftCheckHistoryItem(
                    checked_at=datetime.fromisoformat(str(item["checked_at"])),
                    summary=str(item.get("summary", "")),
                    issues=issues,
                )
            )
        return history

    @staticmethod
    def _decode_payload(raw: object) -> dict[str, object] | None:
        if not raw:
            return None
        if isinstance(raw, dict):
            return raw
        if not isinstance(raw, str):
            return None
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None

    @staticmethod
    def _consistency_issue_state_from_record(record) -> ConsistencyIssueStateRead:  # noqa: ANN001
        props = record.get("props", record)
        return ConsistencyIssueStateRead(
            id=UUID(str(props["id"])),
            world_id=UUID(str(props["world_id"])),
            fingerprint=str(props["fingerprint"]),
            code=str(props["code"]),
            severity=props["severity"],
            message=str(props["message"]),
            target_type=props["target_type"],
            entity_id=UUID(str(props["entity_id"])) if props.get("entity_id") else None,
            relationship_id=UUID(str(props["relationship_id"])) if props.get("relationship_id") else None,
            status=props["status"],
            note=props.get("note"),
            first_seen=datetime.fromisoformat(str(props["first_seen"])),
            last_seen=datetime.fromisoformat(str(props["last_seen"])),
            updated_at=datetime.fromisoformat(str(props["updated_at"])),
        )
