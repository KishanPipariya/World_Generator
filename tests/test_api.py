from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.deps import get_llm_service, get_world_service
from app.main import app
from app.services.world_service import WorldService

class _FakeResult:
    def __init__(self, records):
        self._records = records
    
    def single(self):
        return self._records[0] if self._records else None
        
    def __iter__(self):
        return iter(self._records)

class _FakeSession:
    def __init__(self, db):
        self.db = db
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def run(self, query, **kwargs):
        if "CREATE (w:World" in query:
            self.db["worlds"][kwargs["id"]] = kwargs
            return _FakeResult([kwargs])
        if "CREATE (w)<-[:BELONGS_TO]-(e:Entity" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            record = {
                "id": kwargs["e_id"],
                "world_id": kwargs["w_id"],
                "name": kwargs["name"],
                "entity_type": kwargs["entity_type"],
                "description": kwargs["description"],
                "structured_fields_json": kwargs.get("structured_fields_json", "{}"),
                "created_at": kwargs["created_at"],
            }
            self.db["entities"][kwargs["e_id"]] = record
            return _FakeResult([record])
        if "CREATE (w)<-[:BELONGS_TO]-(s:CanonSuggestion" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            record = {
                "id": kwargs["s_id"],
                "world_id": kwargs["w_id"],
                "instruction": kwargs["instruction"],
                "content": kwargs["content"],
                "suggested_name": kwargs["suggested_name"],
                "suggested_type": kwargs["suggested_type"],
                "status": "pending",
                "created_at": kwargs["created_at"],
            }
            self.db["suggestions"][kwargs["s_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (w)<-[:BELONGS_TO]-(t:TimelineEvent" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            record = {
                "id": kwargs["event_id"],
                "world_id": kwargs["w_id"],
                "title": kwargs["title"],
                "event_order": kwargs["event_order"],
                "description": kwargs["description"],
                "participants_json": kwargs["participants_json"],
                "causes": kwargs["causes"],
                "consequences": kwargs["consequences"],
                "date_label": kwargs.get("date_label"),
                "era_label": kwargs.get("era_label"),
                "depends_on_json": kwargs.get("depends_on_json", "[]"),
                "created_at": kwargs["created_at"],
            }
            self.db["timeline"][kwargs["event_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (w)<-[:BELONGS_TO]-(v:GraphView" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            record = {
                "id": kwargs["view_id"],
                "world_id": kwargs["w_id"],
                "name": kwargs["name"],
                "layout_mode": kwargs["layout_mode"],
                "filters_json": kwargs["filters_json"],
                "camera_json": kwargs["camera_json"],
                "node_positions_json": kwargs["node_positions_json"],
                "created_at": kwargs["created_at"],
                "updated_at": kwargs["updated_at"],
            }
            self.db["graph_views"][kwargs["view_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (w)<-[:BELONGS_TO]-(b:PlanningBoard" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            record = {
                "id": kwargs["board_id"],
                "world_id": kwargs["w_id"],
                "name": kwargs["name"],
                "board_type": kwargs["board_type"],
                "created_at": kwargs["created_at"],
            }
            self.db["planning_boards"][kwargs["board_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (b)<-[:BELONGS_TO]-(c:PlanningCard" in query:
            if kwargs["board_id"] not in self.db["planning_boards"]:
                return _FakeResult([])
            record = {
                "id": kwargs["card_id"],
                "board_id": kwargs["board_id"],
                "world_id": kwargs["w_id"],
                "title": kwargs["title"],
                "description": kwargs["description"],
                "lane": kwargs["lane"],
                "position": kwargs["position"],
                "entity_links_json": kwargs["entity_links_json"],
                "relationship_links_json": kwargs["relationship_links_json"],
                "timeline_event_links_json": kwargs["timeline_event_links_json"],
                "created_at": kwargs["created_at"],
            }
            self.db["planning_cards"][kwargs["card_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (r:RevisionVersion" in query:
            record = {
                "id": kwargs["revision_id"],
                "world_id": kwargs["w_id"],
                "entity_id": kwargs["entity_id"],
                "subject_type": kwargs["subject_type"],
                "field_name": kwargs["field_name"],
                "previous_value": kwargs["previous_value"],
                "new_value": kwargs["new_value"],
                "source": kwargs["source"],
                "created_at": kwargs["created_at"],
            }
            self.db["revisions"][kwargs["revision_id"]] = record
            return _FakeResult([{"props": record}])
        if "CREATE (source)-[r:RELATED_TO" in query:
            source = self.db["entities"].get(kwargs["source_id"])
            target = self.db["entities"].get(kwargs["target_id"])
            if not source or not target or source["world_id"] != kwargs["w_id"] or target["world_id"] != kwargs["w_id"]:
                return _FakeResult([])
            rel = {
                "id": kwargs["r_id"],
                "world_id": kwargs["w_id"],
                "relation_type": kwargs["relation_type"],
                "notes": kwargs["notes"],
                "category": kwargs.get("category"),
                "strength": kwargs.get("strength"),
                "history": kwargs.get("history"),
                "stance": kwargs.get("stance"),
                "color": kwargs.get("color"),
                "display_priority": kwargs.get("display_priority"),
                "created_at": kwargs["created_at"],
            }
            record = {
                "rel_props": rel,
                "source_props": source,
                "target_props": target,
            }
            self.db["relationships"][kwargs["r_id"]] = record
            return _FakeResult([record])
        if "SET e.name" in query:
            record = self.db["entities"].get(kwargs["e_id"])
            if not record or record["world_id"] != kwargs["w_id"]:
                return _FakeResult([])
            for field in ("name", "entity_type", "description"):
                if kwargs[field] is not None:
                    record[field] = kwargs[field]
            if kwargs.get("structured_fields_json") is not None:
                record["structured_fields_json"] = kwargs["structured_fields_json"]
            return _FakeResult([record])
        if "SET s.status" in query:
            record = self.db["suggestions"].get(kwargs["s_id"])
            if record and record["world_id"] == kwargs["w_id"]:
                record["status"] = kwargs["status"]
                return _FakeResult([{"props": record}])
            return _FakeResult([])
        if "DETACH DELETE w" in query:
            world = self.db["worlds"].pop(kwargs["w_id"], None)
            if not world:
                return _FakeResult([])
            return _FakeResult([{"deleted": 1}])
        if "DETACH DELETE e" in query:
            entity_ids = {
                entity_id
                for entity_id, entity in self.db["entities"].items()
                if entity["world_id"] == kwargs["w_id"]
            }
            self.db["entities"] = {
                entity_id: entity
                for entity_id, entity in self.db["entities"].items()
                if entity_id not in entity_ids
            }
            self.db["relationships"] = {
                relationship_id: relationship
                for relationship_id, relationship in self.db["relationships"].items()
                if relationship["rel_props"]["world_id"] != kwargs["w_id"]
            }
            return _FakeResult([])
        if "DELETE linked, e" in query:
            record = self.db["entities"].pop(kwargs["e_id"], None)
            if not record or record["world_id"] != kwargs["w_id"]:
                return _FakeResult([{"deleted": 0}])
            self.db["relationships"] = {
                rid: rel
                for rid, rel in self.db["relationships"].items()
                if (
                    rel["source_props"]["id"] != kwargs["e_id"]
                    and rel["target_props"]["id"] != kwargs["e_id"]
                )
            }
            return _FakeResult([{"deleted": 1}])
        if "DELETE r" in query:
            record = self.db["relationships"].get(kwargs["r_id"])
            if record and record["rel_props"]["world_id"] == kwargs["w_id"]:
                del self.db["relationships"][kwargs["r_id"]]
                return _FakeResult([{"deleted": 1}])
            return _FakeResult([{"deleted": 0}])
        if "DETACH DELETE v" in query:
            record = self.db["graph_views"].get(kwargs["view_id"])
            if record and record["world_id"] == kwargs["w_id"]:
                del self.db["graph_views"][kwargs["view_id"]]
                return _FakeResult([{"deleted": 1}])
            return _FakeResult([{"deleted": 0}])
        if "id" in kwargs and "MATCH (w)<-[belongs]-(e)" in query:
            return _FakeResult(
                [v for v in self.db["entities"].values() if v["world_id"] == kwargs["id"]]
            )
        if "w_id" in kwargs and "MATCH (w)<-[belongs]-(e)" in query:
            if kwargs["w_id"] not in self.db["worlds"]:
                return _FakeResult([])
            if "e_id" in kwargs:
                rec = self.db["entities"].get(kwargs["e_id"])
                return _FakeResult([rec] if rec and rec["world_id"] == kwargs["w_id"] else [])
            return _FakeResult(
                [v for v in self.db["entities"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if "RELATED_TO {world_id: $w_id}" in query or 'type(r) = "RELATED_TO"' in query:
            return _FakeResult(
                [v for v in self.db["relationships"].values() if v["rel_props"]["world_id"] == kwargs["w_id"]]
            )
        if '"CanonSuggestion" IN labels' in query:
            if "s_id" in kwargs:
                record = self.db["suggestions"].get(kwargs["s_id"])
                return _FakeResult([{"props": record}] if record and record["world_id"] == kwargs["w_id"] else [])
            return _FakeResult(
                [{"props": v} for v in self.db["suggestions"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if '"TimelineEvent" IN labels' in query:
            return _FakeResult(
                [{"props": v} for v in self.db["timeline"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if '"GraphView" IN labels' in query:
            return _FakeResult(
                [{"props": v} for v in self.db["graph_views"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if '"PlanningBoard" IN labels' in query and '"PlanningCard" IN labels' not in query:
            return _FakeResult(
                [{"props": v} for v in self.db["planning_boards"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if '"PlanningCard" IN labels' in query:
            return _FakeResult(
                [
                    {"props": v}
                    for v in self.db["planning_cards"].values()
                    if v["world_id"] == kwargs["w_id"] and v["board_id"] == kwargs["board_id"]
                ]
            )
        if '"RevisionVersion" IN labels' in query:
            return _FakeResult(
                [
                    {"props": v}
                    for v in self.db["revisions"].values()
                    if v["world_id"] == kwargs["w_id"]
                    and (kwargs.get("entity_id") is None or v["entity_id"] == kwargs["entity_id"])
                ]
            )
        if "id: $id" in query or "properties(w).id = $id" in query:
            rec = self.db["worlds"].get(kwargs["id"])
            return _FakeResult([{"props": rec}] if rec else [])
        return _FakeResult([{"props": world} for world in self.db["worlds"].values()])

class _FakeDriver:
    def __init__(self):
        self.db = {
            "worlds": {},
            "entities": {},
            "relationships": {},
            "suggestions": {},
            "timeline": {},
            "revisions": {},
            "graph_views": {},
            "planning_boards": {},
            "planning_cards": {},
        }
        
    def session(self):
        return _FakeSession(self.db)



class _HealthLLM:
    mode = "vllm"

    def enabled(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def _override_services():
    fresh = WorldService(driver=_FakeDriver(), llm=_HealthLLM())
    app.dependency_overrides[get_world_service] = lambda: fresh
    app.dependency_overrides[get_llm_service] = lambda: _HealthLLM()
    yield
    app.dependency_overrides.clear()


def test_health_includes_llm_status(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["llm"] == {"mode": "vllm", "enabled": True}


def test_create_list_get_world(client: TestClient) -> None:
    r = client.post(
        "/worlds",
        json={"title": "API World", "tone": "somber", "era_notes": None, "seed": None},
    )
    assert r.status_code == 201
    body = r.json()
    wid = body["id"]
    assert body["title"] == "API World"

    r_list = client.get("/worlds")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    r_get = client.get(f"/worlds/{wid}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == wid


def test_delete_world_removes_world_and_children(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Delete Me"})
    wid = r.json()["id"]
    source = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Asha", "entity_type": "Character", "description": "A scout."},
    ).json()
    target = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Northgate", "entity_type": "Location", "description": "A city."},
    ).json()
    client.post(
        f"/worlds/{wid}/relationships",
        json={
            "source_entity_id": source["id"],
            "target_entity_id": target["id"],
            "relation_type": "guards",
        },
    )

    deleted = client.delete(f"/worlds/{wid}")
    assert deleted.status_code == 204
    assert client.get(f"/worlds/{wid}").status_code == 404
    assert client.get(f"/worlds/{wid}/entities").status_code == 404
    assert client.delete(f"/worlds/{wid}").status_code == 404


def test_create_demo_world_seeds_entities_and_relationships(client: TestClient) -> None:
    r = client.post("/worlds/demo")
    assert r.status_code == 201
    body = r.json()
    wid = body["world"]["id"]
    assert body["world"]["title"] == "The Ember Archipelago"
    assert len(body["entities"]) >= 6
    assert len(body["relationships"]) >= 5

    listed = client.get(f"/worlds/{wid}/entities")
    assert listed.status_code == 200
    assert len(listed.json()["entities"]) == len(body["entities"])


def test_generate_returns_404_for_unknown_world(client: TestClient) -> None:
    r = client.post(
        "/worlds/00000000-0000-0000-0000-000000000099/generate",
        json={},
    )
    assert r.status_code == 404


def test_generate_uses_stub_when_llm_disabled(client: TestClient) -> None:
    fresh: WorldService = WorldService(driver=_FakeDriver(), llm=None)
    app.dependency_overrides[get_world_service] = lambda: fresh
    r = client.post("/worlds", json={"title": "Z"})
    wid = r.json()["id"]
    g = client.post(f"/worlds/{wid}/generate", json={"section": "glossary"})
    assert g.status_code == 200
    payload = g.json()
    assert payload["section"] == "glossary"
    assert "[stub glossary" in payload["content"]


def test_generate_uses_llm_when_service_enabled(client: TestClient) -> None:
    class _SvcLLM:
        def enabled(self) -> bool:
            return True

        def generate_section(self, world, section):  # noqa: ANN001
            return f"LLM:{section}"

    fresh = WorldService(driver=_FakeDriver(), llm=_SvcLLM())
    app.dependency_overrides[get_world_service] = lambda: fresh
    r = client.post("/worlds", json={"title": "Q"})
    wid = r.json()["id"]
    g = client.post(f"/worlds/{wid}/generate", json={"section": "timeline_hint"})
    assert g.status_code == 200


def test_agentic_generate_returns_404_for_unknown_world(client: TestClient) -> None:
    r = client.post(
        "/worlds/00000000-0000-0000-0000-000000000099/agentic-generate",
        json={"instruction": "test"},
    )
    assert r.status_code == 404


def test_agentic_generate_uses_stub_when_llm_disabled(client: TestClient) -> None:
    fresh: WorldService = WorldService(driver=_FakeDriver(), llm=None)
    app.dependency_overrides[get_world_service] = lambda: fresh
    r = client.post("/worlds", json={"title": "Z"})
    wid = r.json()["id"]
    g = client.post(f"/worlds/{wid}/agentic-generate", json={"instruction": "generate cities"})
    assert g.status_code == 200
    payload = g.json()
    assert payload["instruction"] == "generate cities"
    assert "[Stub agentic generation for Z]" in payload["content"]


def test_agentic_generate_creates_entity_when_requested(client: TestClient) -> None:
    fresh: WorldService = WorldService(driver=_FakeDriver(), llm=None)
    app.dependency_overrides[get_world_service] = lambda: fresh
    r = client.post("/worlds", json={"title": "Z"})
    wid = r.json()["id"]
    g = client.post(
        f"/worlds/{wid}/agentic-generate", 
        json={
            "instruction": "generate cities",
            "save_as_entity_type": "City",
            "save_as_name": "Testopia"
        }
    )
    assert g.status_code == 200
    payload = g.json()
    assert payload["entity_id"] is not None

    entities = client.get(f"/worlds/{wid}/entities")
    assert entities.status_code == 200
    assert entities.json()["entities"][0]["name"] == "Testopia"


def test_entity_crud(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Z"})
    wid = r.json()["id"]

    created = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Northgate", "entity_type": "Location", "description": "A trade city."},
    )
    assert created.status_code == 201
    eid = created.json()["id"]

    listed = client.get(f"/worlds/{wid}/entities")
    assert listed.status_code == 200
    assert [entity["name"] for entity in listed.json()["entities"]] == ["Northgate"]

    updated = client.patch(
        f"/worlds/{wid}/entities/{eid}",
        json={"description": "A fortified trade city."},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "A fortified trade city."

    deleted = client.delete(f"/worlds/{wid}/entities/{eid}")
    assert deleted.status_code == 204
    listed_again = client.get(f"/worlds/{wid}/entities")
    assert listed_again.json()["entities"] == []


def test_relationship_crud_and_export(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Z", "tone": "bright"})
    wid = r.json()["id"]
    source = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Asha", "entity_type": "Character", "description": "A scout."},
    ).json()
    target = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Northgate", "entity_type": "Location", "description": "A city."},
    ).json()

    created = client.post(
        f"/worlds/{wid}/relationships",
        json={
            "source_entity_id": source["id"],
            "target_entity_id": target["id"],
            "relation_type": "protects",
            "notes": "Assigned after the winter treaty.",
        },
    )
    assert created.status_code == 201
    rid = created.json()["id"]

    listed = client.get(f"/worlds/{wid}/relationships")
    assert listed.status_code == 200
    assert listed.json()["relationships"][0]["relation_type"] == "protects"

    exported = client.get(f"/worlds/{wid}/export/markdown")
    assert exported.status_code == 200
    content = exported.json()["content"]
    assert "# Z" in content
    assert "## World Metadata" in content
    assert "- Entities: 2" in content
    assert "- Relationships: 1" in content
    assert "#### Asha" in content
    assert "[[Asha]] protects [[Northgate]]" in content

    deleted = client.delete(f"/worlds/{wid}/relationships/{rid}")
    assert deleted.status_code == 204


def test_generation_suggestion_inbox_and_apply(client: TestClient) -> None:
    fresh: WorldService = WorldService(driver=_FakeDriver(), llm=None)
    app.dependency_overrides[get_world_service] = lambda: fresh
    world = client.post("/worlds", json={"title": "Inbox"}).json()
    wid = world["id"]

    generated = client.post(
        f"/worlds/{wid}/agentic-generate",
        json={"instruction": "draft a lost library"},
    )
    assert generated.status_code == 200
    suggestion_id = generated.json()["suggestion_id"]
    assert suggestion_id is not None

    suggestions = client.get(f"/worlds/{wid}/suggestions")
    assert suggestions.status_code == 200
    assert suggestions.json()["suggestions"][0]["status"] == "pending"

    applied = client.post(
        f"/worlds/{wid}/suggestions/{suggestion_id}/apply",
        json={"mode": "create_entity", "name": "Lost Library", "entity_type": "Location"},
    )
    assert applied.status_code == 200
    assert applied.json()["suggestion"]["status"] == "accepted"
    assert applied.json()["entity"]["name"] == "Lost Library"


def test_timeline_revisions_passage_and_export_presets(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Roadmap", "tone": "noir"}).json()
    wid = world["id"]
    entity = client.post(
        f"/worlds/{wid}/entities",
        json={
            "name": "Asha",
            "entity_type": "Character",
            "description": "A detective with one impossible case.",
            "structured_fields": {"goal": "Solve the bell murder", "secret": "She hid evidence."},
        },
    ).json()

    timeline = client.post(
        f"/worlds/{wid}/timeline",
        json={
            "title": "Bell Murder",
            "event_order": 1,
            "description": "The first bell cracks.",
            "participants": [entity["id"]],
            "causes": "A forged confession",
            "consequences": "Asha reopens the case",
        },
    )
    assert timeline.status_code == 201
    assert client.get(f"/worlds/{wid}/timeline").json()["events"][0]["title"] == "Bell Murder"

    client.patch(
        f"/worlds/{wid}/entities/{entity['id']}",
        json={"description": "A noir detective with one impossible case."},
    )
    revisions = client.get(f"/worlds/{wid}/revisions", params={"entity_id": entity["id"]})
    assert revisions.status_code == 200
    revision_id = revisions.json()["versions"][0]["id"]
    restored = client.post(f"/worlds/{wid}/revisions/{revision_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["description"] == "A detective with one impossible case."

    passage = client.post(f"/worlds/{wid}/passage-check", json={"passage": "Asha entered the room."})
    assert passage.status_code == 200
    assert "issues" in passage.json()

    exported = client.get(f"/worlds/{wid}/export/markdown", params={"preset": "timeline_only"})
    assert exported.status_code == 200
    assert exported.json()["preset"] == "timeline_only"
    assert "# Roadmap Timeline" in exported.json()["content"]


def test_visual_planning_resources(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Visual Plan"}).json()
    wid = world["id"]
    entity = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Mara", "entity_type": "Character", "description": "A cartographer."},
    ).json()
    target = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "The Concord", "entity_type": "Faction", "description": "A council."},
    ).json()
    relationship = client.post(
        f"/worlds/{wid}/relationships",
        json={
            "source_entity_id": entity["id"],
            "target_entity_id": target["id"],
            "relation_type": "opposes",
            "stance": "conflict",
            "color": "#ef4444",
            "display_priority": 9,
        },
    )
    assert relationship.status_code == 201
    assert relationship.json()["stance"] == "conflict"
    assert relationship.json()["display_priority"] == 9

    first_event = client.post(
        f"/worlds/{wid}/timeline",
        json={
            "title": "First Oath",
            "event_order": 1,
            "date_label": "Year 12",
            "era_label": "Ashen Age",
        },
    ).json()
    second_event = client.post(
        f"/worlds/{wid}/timeline",
        json={
            "title": "Broken Oath",
            "event_order": 2,
            "depends_on": [first_event["id"]],
        },
    )
    assert second_event.status_code == 201
    assert second_event.json()["depends_on"] == [first_event["id"]]

    graph_view = client.post(
        f"/worlds/{wid}/graph-views",
        json={
            "name": "Political Map",
            "layout_mode": "type_columns",
            "filters": {"types": ["Character", "Faction"]},
            "camera": {"x": 10, "y": -20, "zoom": 0.8},
            "node_positions": {entity["id"]: {"x": 120, "y": 80}},
        },
    )
    assert graph_view.status_code == 201
    graph_view_id = graph_view.json()["id"]
    listed_views = client.get(f"/worlds/{wid}/graph-views")
    assert listed_views.status_code == 200
    assert listed_views.json()["views"][0]["name"] == "Political Map"
    assert listed_views.json()["views"][0]["node_positions"][entity["id"]]["x"] == 120

    board = client.post(
        f"/worlds/{wid}/planning-boards",
        json={"name": "Act 2 Conflict", "board_type": "arc"},
    )
    assert board.status_code == 201
    card = client.post(
        f"/worlds/{wid}/planning-boards/{board.json()['id']}/cards",
        json={
            "title": "Mara confronts the Concord",
            "lane": "Draft",
            "position": 1,
            "entity_links": [entity["id"]],
            "relationship_links": [relationship.json()["id"]],
            "timeline_event_links": [second_event.json()["id"]],
        },
    )
    assert card.status_code == 201
    boards = client.get(f"/worlds/{wid}/planning-boards")
    assert boards.status_code == 200
    assert boards.json()["boards"][0]["cards"][0]["title"] == "Mara confronts the Concord"

    deleted = client.delete(f"/worlds/{wid}/graph-views/{graph_view_id}")
    assert deleted.status_code == 204
    assert client.get(f"/worlds/{wid}/graph-views").json()["views"] == []


def test_entity_and_relationship_world_not_found(client: TestClient) -> None:
    wid = "00000000-0000-0000-0000-000000000099"
    assert client.get(f"/worlds/{wid}/entities").status_code == 404
    assert client.get(f"/worlds/{wid}/relationships").status_code == 404
    assert client.get(f"/worlds/{wid}/consistency").status_code == 404
    assert client.get(f"/worlds/{wid}/export/markdown").status_code == 404


def test_consistency_report_flags_demo_review_issues(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Sparse", "tone": "bright"})
    wid = r.json()["id"]
    entity = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "A", "entity_type": "Character", "description": ""},
    ).json()

    report = client.get(f"/worlds/{wid}/consistency")
    assert report.status_code == 200
    payload = report.json()
    assert payload["score"] < 100
    assert "Score" in payload["summary"]
    codes = {issue["code"] for issue in payload["issues"]}
    assert {"missing_description", "orphaned_entity"}.issubset(codes)
    assert any(issue["entity_id"] == entity["id"] for issue in payload["issues"])


def test_consistency_report_flags_canon_dashboard_issues(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Canon", "tone": "bright"})
    wid = r.json()["id"]
    character = client.post(
        f"/worlds/{wid}/entities",
        json={
            "name": "Asha",
            "entity_type": "Character",
            "description": "A scout from Northgate with a careful eye.",
        },
    ).json()
    faction = client.post(
        f"/worlds/{wid}/entities",
        json={
            "name": "The Bell Guard",
            "entity_type": "Faction",
            "description": "A city watch with polished armor.",
        },
    ).json()
    event = client.post(
        f"/worlds/{wid}/entities",
        json={
            "name": "The Gate Riot",
            "entity_type": "Event",
            "description": "Citizens clashed at Northgate over ration ledgers.",
        },
    ).json()

    first_relationship = client.post(
        f"/worlds/{wid}/relationships",
        json={
            "source_entity_id": character["id"],
            "target_entity_id": faction["id"],
            "relation_type": "protects",
        },
    ).json()
    second_relationship = client.post(
        f"/worlds/{wid}/relationships",
        json={
            "source_entity_id": faction["id"],
            "target_entity_id": character["id"],
            "relation_type": "hunts",
        },
    ).json()

    report = client.get(f"/worlds/{wid}/consistency")
    assert report.status_code == 200
    issues = report.json()["issues"]
    codes = {issue["code"] for issue in issues}
    assert {"thin_lore", "timeline_gap", "missing_relationship_context", "possible_contradiction"}.issubset(codes)
    assert any(issue["entity_id"] == event["id"] and issue["code"] == "timeline_gap" for issue in issues)
    assert any(
        issue["relationship_id"] in {first_relationship["id"], second_relationship["id"]}
        and issue["code"] == "missing_relationship_context"
        for issue in issues
    )


def test_cors_preflight_allowed_origin(client: TestClient) -> None:
    headers = {
        "Origin": "http://localhost:5174",
        "Access-Control-Request-Method": "POST",
    }
    r = client.options("/worlds", headers=headers)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_cors_preflight_disallowed_origin(client: TestClient) -> None:
    headers = {
        "Origin": "http://some-other-origin.com",
        "Access-Control-Request-Method": "POST",
    }
    r = client.options("/worlds", headers=headers)
    assert r.status_code == 400
    assert "Disallowed CORS origin" in r.text
