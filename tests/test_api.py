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
                "created_at": kwargs["created_at"],
            }
            self.db["entities"][kwargs["e_id"]] = record
            return _FakeResult([record])
        if "CREATE (source)-[r:RELATED_TO" in query:
            source = self.db["entities"].get(kwargs["source_id"])
            target = self.db["entities"].get(kwargs["target_id"])
            if not source or not target or source["world_id"] != kwargs["w_id"] or target["world_id"] != kwargs["w_id"]:
                return _FakeResult([])
            record = {
                "id": kwargs["r_id"],
                "world_id": kwargs["w_id"],
                "source_entity_id": source["id"],
                "source_entity_name": source["name"],
                "target_entity_id": target["id"],
                "target_entity_name": target["name"],
                "relation_type": kwargs["relation_type"],
                "notes": kwargs["notes"],
                "created_at": kwargs["created_at"],
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
            return _FakeResult([record])
        if "DELETE linked, e" in query:
            record = self.db["entities"].pop(kwargs["e_id"], None)
            if not record or record["world_id"] != kwargs["w_id"]:
                return _FakeResult([{"deleted": 0}])
            self.db["relationships"] = {
                rid: rel
                for rid, rel in self.db["relationships"].items()
                if rel["source_entity_id"] != kwargs["e_id"] and rel["target_entity_id"] != kwargs["e_id"]
            }
            return _FakeResult([{"deleted": 1}])
        if "DELETE r" in query:
            record = self.db["relationships"].get(kwargs["r_id"])
            if record and record["world_id"] == kwargs["w_id"]:
                del self.db["relationships"][kwargs["r_id"]]
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
                [v for v in self.db["relationships"].values() if v["world_id"] == kwargs["w_id"]]
            )
        if "id: $id" in query or "properties(w).id = $id" in query:
            rec = self.db["worlds"].get(kwargs["id"])
            return _FakeResult([{"props": rec}] if rec else [])
        return _FakeResult([{"props": world} for world in self.db["worlds"].values()])

class _FakeDriver:
    def __init__(self):
        self.db = {"worlds": {}, "entities": {}, "relationships": {}}
        
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
    assert "#### Asha" in content
    assert "**Asha** protects **Northgate**" in content

    deleted = client.delete(f"/worlds/{wid}/relationships/{rid}")
    assert deleted.status_code == 204


def test_entity_and_relationship_world_not_found(client: TestClient) -> None:
    wid = "00000000-0000-0000-0000-000000000099"
    assert client.get(f"/worlds/{wid}/entities").status_code == 404
    assert client.get(f"/worlds/{wid}/relationships").status_code == 404
    assert client.get(f"/worlds/{wid}/export/markdown").status_code == 404


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
