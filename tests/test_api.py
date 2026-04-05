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
        if "CREATE" in query:
            # We need kwargs["created_at"] string to dict
            self.db[kwargs["id"]] = kwargs
            return _FakeResult([])
        elif "id: $id" in query:
            rec = self.db.get(kwargs["id"])
            return _FakeResult([rec] if rec else [])
        else:
            return _FakeResult(list(self.db.values()))

class _FakeDriver:
    def __init__(self):
        self.db = {}
        
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
    assert g.json()["content"] == "LLM:timeline_hint"

