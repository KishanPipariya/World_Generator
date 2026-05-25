from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import UUID, uuid4

from neo4j import Driver

from app.schemas.world import (
    ConsistencyIssue,
    ConsistencyReportResponse,
    DemoWorldResponse,
    EntityRead,
    EntityUpdate,
    RelationshipRead,
    WorldCreate,
    WorldRead,
)


class WorldLLM(Protocol):
    """Minimal surface used by :class:`WorldService` for generation."""

    def enabled(self) -> bool: ...

    def generate_section(
        self, world: WorldRead, section: Literal["glossary", "timeline_hint"]
    ) -> str | None: ...

    def generate_agentic(
        self, world: WorldRead, context: str, instruction: str
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
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $id
        RETURN properties(w) AS props
        """
        with self._driver.session() as session:
            result = session.run(query, id=str(world_id))
            record = result.single()
            if not record:
                return None
            return self._world_from_props(record.get("props", record))

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
                worlds.append(self._to_read(self._world_from_props(record.get("props", record))))
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
        delete_world_query = """
        MATCH (w)
        WHERE "World" IN labels(w) AND properties(w).id = $w_id
        WITH w
        DETACH DELETE w
        RETURN 1 AS deleted
        """
        with self._driver.session() as session:
            session.run(delete_entities_query, w_id=str(world_id))
            result = session.run(delete_world_query, w_id=str(world_id))
            record = result.single()
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
        self, world_id: UUID, name: str, entity_type: str, description: str
    ) -> EntityRead:
        eid = uuid4()
        now = datetime.now(UTC)
        query = """
        MATCH (w:World {id: $w_id})
        CREATE (w)<-[:BELONGS_TO]-(e:Entity {
            id: $e_id, world_id: $w_id, name: $name, 
            entity_type: $entity_type, description: $description,
            created_at: $created_at
        })
        RETURN e.id AS id, e.world_id AS world_id, e.name AS name,
               e.entity_type AS entity_type, e.description AS description, 
               e.created_at AS created_at
        """
        with self._driver.session() as session:
            result = session.run(query, 
                                 w_id=str(world_id), 
                                 e_id=str(eid),
                                 name=name,
                                 entity_type=entity_type,
                                 description=description,
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
            e.description = coalesce($description, e.description)
        RETURN properties(e) AS props
        """
        with self._driver.session() as session:
            result = session.run(
                query,
                w_id=str(world_id),
                e_id=str(entity_id),
                name=updates.get("name"),
                entity_type=updates.get("entity_type"),
                description=updates.get("description"),
            )
            record = result.single()
            return self._entity_from_record(record) if record else None

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
            notes: $notes, created_at: $created_at
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

    def export_markdown(self, world_id: UUID) -> str | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        entities = self.list_entities(world_id) or []
        relationships = self.list_relationships(world_id) or []

        lines = [
            f"# {rec.title}",
            "",
            "> Demo-ready world bible export.",
            "",
            "## World Metadata",
            "",
            f"- Created: {rec.created_at.date().isoformat()}",
            f"- Entities: {len(entities)}",
            f"- Relationships: {len(relationships)}",
        ]
        if rec.tone:
            lines.append(f"- Tone: {rec.tone}")
        if rec.seed:
            lines.append(f"- Seed: {rec.seed}")
        lines.append("")
        if rec.era_notes:
            lines.extend(["## Era Notes", "", rec.era_notes, ""])

        lines.extend(["## Entities", ""])
        if not entities:
            lines.extend(["No saved entities yet.", ""])
        else:
            for entity_type in ("Character", "Location", "Faction", "Concept", "Event", "Other"):
                grouped = [
                    entity
                    for entity in entities
                    if self._display_entity_type(entity.entity_type) == entity_type
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

        lines.extend(["## Relationships", ""])
        if not relationships:
            lines.extend(["No relationships yet.", ""])
        else:
            for relationship in relationships:
                lines.append(
                    f"- [[{relationship.source_entity_name}]] "
                    f"{relationship.relation_type} "
                    f"[[{relationship.target_entity_name}]]"
                )
                if relationship.notes:
                    lines.append(f"  - {relationship.notes}")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    def consistency_report(self, world_id: UUID) -> ConsistencyReportResponse | None:
        rec = self._get_record(world_id)
        if not rec:
            return None
        entities = self.list_entities(world_id) or []
        relationships = self.list_relationships(world_id) or []
        issues: list[ConsistencyIssue] = []
        relationship_counts: dict[UUID, int] = {}
        for relationship in relationships:
            relationship_counts[relationship.source_entity_id] = (
                relationship_counts.get(relationship.source_entity_id, 0) + 1
            )
            relationship_counts[relationship.target_entity_id] = (
                relationship_counts.get(relationship.target_entity_id, 0) + 1
            )

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
            if rec.tone and rec.tone.lower() not in entity.description.lower():
                issues.append(
                    ConsistencyIssue(
                        code="tone_check",
                        severity="info",
                        message=f"{entity.name} may need a pass for the world's tone.",
                        entity_id=entity.id,
                    )
                )
            displayed_type = self._display_entity_type(entity.entity_type)
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
            if entity.id not in relationship_counts:
                issues.append(
                    ConsistencyIssue(
                        code="orphaned_entity",
                        severity="warning",
                        message=f"{entity.name} has no relationships.",
                        entity_id=entity.id,
                    )
                )
            elif (
                self._display_entity_type(entity.entity_type) in {"Character", "Faction", "Event"}
                and relationship_counts[entity.id] == 1
            ):
                issues.append(
                    ConsistencyIssue(
                        code="missing_relationship_context",
                        severity="info",
                        message=f"{entity.name} has limited relationship context for canon review.",
                        entity_id=entity.id,
                    )
                )

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
            stance = self._relationship_stance(relation_text)
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

        severity_cost = {"info": 2, "warning": 8, "error": 18}
        score = max(0, 100 - sum(severity_cost[issue.severity] for issue in issues))
        summary = self._consistency_summary(score, issues)
        return ConsistencyReportResponse(
            world_id=world_id,
            score=score,
            summary=summary,
            issues=issues,
        )

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

    @staticmethod
    def _entity_from_record(record) -> EntityRead:  # noqa: ANN001
        props = record.get("props", record)
        return EntityRead(
            id=UUID(props["id"]),
            world_id=UUID(props["world_id"]),
            name=props["name"],
            entity_type=props["entity_type"],
            description=props["description"],
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
            created_at=datetime.fromisoformat(record["created_at"]),
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

    @staticmethod
    def _relationship_stance(relation_type: str) -> str | None:
        ally_cues = {"ally", "allied", "protect", "supports", "serves", "trusts", "loves"}
        conflict_cues = {"enemy", "rival", "hunts", "opposes", "betrays", "hates", "fights"}
        if any(cue in relation_type for cue in ally_cues):
            return "alliance"
        if any(cue in relation_type for cue in conflict_cues):
            return "conflict"
        return None

    @staticmethod
    def _consistency_summary(score: int, issues: list[ConsistencyIssue]) -> str:
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
