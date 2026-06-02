from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.deps import get_auth_service, get_llm_service, get_world_service
from app.main import app
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService
from app.services.world import WorldService
from app.sqlite_driver import SQLiteDriver

_active_driver: SQLiteDriver | None = None


def _driver() -> SQLiteDriver:
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    driver = SQLiteDriver(path)
    if _active_driver is not None:
        for user in _active_driver._all("SELECT * FROM users"):
            driver.create_user(user)
    return driver


class _HealthLLM:
    mode = "openrouter"

    def enabled(self) -> bool:
        return True

    def generate_section(self, world, section):  # noqa: ANN001
        return None

    def generate_agentic(self, world, context, instruction):  # noqa: ANN001
        return None


class _JsonLLM(_HealthLLM):
    def __init__(self, content: str) -> None:
        self.content = content

    def generate_agentic(self, world, context, instruction):  # noqa: ANN001
        return self.content


@pytest.fixture(autouse=True)
def _override_services():
    global _active_driver
    driver = _driver()
    _active_driver = driver
    fresh = WorldService(driver=driver, llm=_HealthLLM())
    app.dependency_overrides[get_world_service] = lambda: fresh
    app.dependency_overrides[get_auth_service] = lambda: AuthService(driver=driver)
    app.dependency_overrides[get_llm_service] = lambda: _HealthLLM()
    yield
    app.dependency_overrides.clear()
    _active_driver = None


def test_health_is_reduced_public_status(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data == {"status": "ok"}


def test_worlds_require_bearer_auth(client: TestClient) -> None:
    r = client.get("/worlds", headers={"Authorization": ""})
    assert r.status_code == 401


def test_register_hashes_password_and_enforces_unique_username_email() -> None:
    driver = _driver()
    auth = AuthService(driver=driver)
    user = auth.register(
        UserCreate(username="alice", email="alice@example.com", password="test-password")
    )
    stored = driver.get_user_by_id(str(user.id))
    assert stored is not None
    assert stored["password_hash"] != "test-password"
    assert auth.authenticate("alice", "test-password") is not None
    with pytest.raises(ValueError):
        auth.register(UserCreate(username="alice", email="other@example.com", password="test-password"))
    with pytest.raises(ValueError):
        auth.register(UserCreate(username="other", email="alice@example.com", password="test-password"))


def test_first_registered_user_claims_only_existing_legacy_worlds() -> None:
    driver = _driver()
    driver.create_world(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "title": "Legacy",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00+00:00",
            "owner_id": None,
        }
    )
    auth = AuthService(driver=driver)
    first = auth.register(UserCreate(username="first", email="first@example.com", password="test-password"))
    legacy = driver.get_world("00000000-0000-0000-0000-000000000001")
    assert legacy is not None
    assert legacy["owner_id"] == str(first.id)

    driver.create_world(
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "title": "New Legacy",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00+00:00",
            "owner_id": None,
        }
    )
    auth.register(UserCreate(username="second", email="second@example.com", password="test-password"))
    new_legacy = driver.get_world("00000000-0000-0000-0000-000000000002")
    assert new_legacy is not None
    assert new_legacy.get("owner_id") is None


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


def test_users_only_see_their_own_worlds(client: TestClient) -> None:
    first_world = client.post("/worlds", json={"title": "Private"}).json()

    second = TestClient(app, base_url="http://testserver/api/v1")
    second.post(
        "/auth/register",
        json={"username": "otheruser", "email": "other@example.com", "password": "test-password"},
    )
    token = second.post(
        "/auth/login",
        json={"username": "otheruser", "password": "test-password"},
    ).json()["access_token"]
    second.headers.update({"Authorization": f"Bearer {token}"})

    assert second.get("/worlds").json() == []
    assert second.get(f"/worlds/{first_world['id']}").status_code == 404


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
    fresh: WorldService = WorldService(driver=_driver(), llm=None)
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

    fresh = WorldService(driver=_driver(), llm=_SvcLLM())
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
    fresh: WorldService = WorldService(driver=_driver(), llm=None)
    app.dependency_overrides[get_world_service] = lambda: fresh
    r = client.post("/worlds", json={"title": "Z"})
    wid = r.json()["id"]
    g = client.post(f"/worlds/{wid}/agentic-generate", json={"instruction": "generate cities"})
    assert g.status_code == 200
    payload = g.json()
    assert payload["instruction"] == "generate cities"
    assert "[Stub agentic generation for Z]" in payload["content"]


def test_agentic_generate_creates_entity_when_requested(client: TestClient) -> None:
    fresh: WorldService = WorldService(driver=_driver(), llm=None)
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


def test_oversized_entity_description_is_rejected(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Limits"}).json()
    response = client.post(
        f"/worlds/{world['id']}/entities",
        json={"name": "Too Much", "entity_type": "Concept", "description": "x" * 20001},
    )
    assert response.status_code == 422


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
    fresh: WorldService = WorldService(driver=_driver(), llm=None)
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


def test_campaign_resources_exports_and_impact_review(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Campaign Desk"}).json()
    wid = world["id"]
    entity = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Red Abbey", "entity_type": "Location", "description": "A monastery under siege."},
    ).json()

    session = client.post(
        f"/worlds/{wid}/campaign-sessions",
        json={
            "session_number": 1,
            "title": "Ash at the Gate",
            "recap": "The party exposed the false prior.",
            "player_actions": "Spared a captured scout.",
            "consequences": "The abbey faction splinters.",
            "linked_entity_ids": [entity["id"]],
        },
    )
    assert session.status_code == 201
    sid = session.json()["id"]
    assert client.get(f"/worlds/{wid}/campaign-sessions").json()["sessions"][0]["title"] == "Ash at the Gate"

    note = client.post(
        f"/worlds/{wid}/lore-notes",
        json={
            "title": "Prior's Secret",
            "body": "The prior serves the buried bell.",
            "subject_type": "entity",
            "subject_id": entity["id"],
            "visibility": "dm_only",
            "truth_state": "true",
            "handout_text": "The prior is afraid of the old crypt.",
        },
    )
    assert note.status_code == 201
    visible_note = client.post(
        f"/worlds/{wid}/lore-notes",
        json={
            "title": "Abbey Rumor",
            "body": "Novices hear bells under the floor.",
            "visibility": "discovered",
            "truth_state": "partial",
        },
    )
    assert visible_note.status_code == 201

    clock = client.post(
        f"/worlds/{wid}/faction-clocks",
        json={
            "title": "Abbey Coup",
            "linked_entity_id": entity["id"],
            "segments": 6,
            "filled_segments": 2,
            "stakes": "The abbey changes hands.",
            "linked_session_ids": [sid],
        },
    )
    assert clock.status_code == 201
    assert client.get(f"/worlds/{wid}/faction-clocks").json()["clocks"][0]["filled_segments"] == 2

    player_export = client.get(f"/worlds/{wid}/export/markdown", params={"preset": "player_handout"})
    assert player_export.status_code == 200
    assert "Abbey Rumor" in player_export.json()["content"]
    assert "Prior's Secret" not in player_export.json()["content"]

    dm_export = client.get(f"/worlds/{wid}/export/markdown", params={"preset": "dm_campaign_brief"})
    assert dm_export.status_code == 200
    assert "Prior's Secret" in dm_export.json()["content"]
    assert "Abbey Coup" in dm_export.json()["content"]

    impact = client.post(f"/worlds/{wid}/campaign-sessions/{sid}/impact-review", json={})
    assert impact.status_code == 200
    assert impact.json()["suggestion"]["status"] == "pending"
    assert impact.json()["suggestion"]["source_type"] == "dm"
    assert impact.json()["suggestion"]["source_id"] == sid
    assert "false prior" in impact.json()["suggestion"]["content"]
    assert client.get(f"/worlds/{wid}/suggestions").json()["suggestions"] == []
    assert client.get(f"/worlds/{wid}/dm/suggestions").json()["suggestions"][0]["source_type"] == "dm"

    bad = client.post(
        f"/worlds/{wid}/campaign-sessions",
        json={
            "session_number": 2,
            "title": "Bad Link",
            "linked_entity_ids": ["00000000-0000-0000-0000-000000000099"],
        },
    )
    assert bad.status_code == 404


def test_dm_routes_use_campaign_resources_and_exports(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "DM Desk"}).json()
    wid = world["id"]

    session = client.post(
        f"/worlds/{wid}/dm/sessions",
        json={
            "session_number": 1,
            "title": "Lantern Bargain",
            "recap": "The party bargained with the lantern court.",
            "player_actions": "Promised safe passage.",
            "consequences": "A hidden faction clock advances.",
        },
    )
    assert session.status_code == 201
    sid = session.json()["id"]
    assert client.get(f"/worlds/{wid}/dm/sessions").json()["sessions"][0]["title"] == "Lantern Bargain"

    note = client.post(
        f"/worlds/{wid}/dm/lore-notes",
        json={
            "title": "Lantern Debt",
            "body": "The court collects debts in names.",
            "visibility": "dm_only",
        },
    )
    assert note.status_code == 201
    clock = client.post(
        f"/worlds/{wid}/dm/faction-clocks",
        json={"title": "Court Collection", "segments": 6, "filled_segments": 1, "linked_session_ids": [sid]},
    )
    assert clock.status_code == 201
    assert client.get(f"/worlds/{wid}/dm/faction-clocks").json()["clocks"][0]["title"] == "Court Collection"

    impact = client.post(f"/worlds/{wid}/dm/sessions/{sid}/impact-review", json={})
    assert impact.status_code == 200
    assert impact.json()["suggestion"]["source_type"] == "dm"
    assert impact.json()["suggestion"]["source_id"] == sid
    assert client.get(f"/worlds/{wid}/suggestions").json()["suggestions"] == []
    assert len(client.get(f"/worlds/{wid}/dm/suggestions").json()["suggestions"]) == 1

    exported = client.get(f"/worlds/{wid}/dm/export/markdown", params={"preset": "dm_campaign_brief"})
    assert exported.status_code == 200
    assert exported.json()["preset"] == "dm_campaign_brief"
    assert "Lantern Debt" in exported.json()["content"]


def test_saved_draft_crud_and_check_history(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Draft Desk", "tone": "noir"}).json()
    wid = world["id"]
    entity = client.post(
        f"/worlds/{wid}/entities",
        json={
            "name": "Asha",
            "entity_type": "Character",
            "description": "Asha is the only detective who knows the bell code.",
        },
    ).json()

    created = client.post(
        f"/worlds/{wid}/drafts",
        json={
            "title": "Chapter 1",
            "body": "Asha entered the station. She was the only one listening.",
            "linked_entity_ids": [entity["id"]],
        },
    )
    assert created.status_code == 201
    draft = created.json()
    assert draft["status"] == "draft"
    assert draft["linked_entity_ids"] == [entity["id"]]
    assert draft["check_history"] == []

    updated = client.patch(
        f"/worlds/{wid}/drafts/{draft['id']}",
        json={"status": "revising", "title": "Opening Scene"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Opening Scene"
    assert updated.json()["status"] == "revising"

    checked = client.post(f"/worlds/{wid}/drafts/{draft['id']}/check")
    assert checked.status_code == 200
    assert checked.json()["summary"] == "Passage check found 2 item(s) to review."

    fetched = client.get(f"/worlds/{wid}/drafts/{draft['id']}")
    assert fetched.status_code == 200
    history = fetched.json()["check_history"]
    assert len(history) == 1
    assert history[0]["summary"] == checked.json()["summary"]
    assert {issue["code"] for issue in history[0]["issues"]} == {"tone_drift", "canon_absolute"}

    listed = client.get(f"/worlds/{wid}/drafts")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["drafts"]] == [draft["id"]]

    deleted = client.delete(f"/worlds/{wid}/drafts/{draft['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/worlds/{wid}/drafts").json()["drafts"] == []


def test_draft_extract_fallback_creates_pending_suggestions_and_applies_new_kinds(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Extraction Desk"}).json()
    wid = world["id"]
    asha = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Asha", "entity_type": "Character", "description": "A detective."},
    ).json()
    bell = client.post(
        f"/worlds/{wid}/entities",
        json={"name": "Bell Tower", "entity_type": "Location", "description": "A landmark."},
    ).json()
    excerpt = "During the ash season, Asha met Bell Tower before dawn. Mira Voss carried the blue writ."
    draft = client.post(
        f"/worlds/{wid}/drafts",
        json={"title": "Marked Scene", "body": f"Opening.\n{excerpt}\nClosing."},
    ).json()

    extracted = client.post(
        f"/worlds/{wid}/drafts/{draft['id']}/extract",
        json={"excerpt": excerpt, "max_candidates": 6},
    )
    assert extracted.status_code == 200
    suggestions = extracted.json()["suggestions"]
    assert suggestions
    assert {item["source_type"] for item in suggestions} == {"draft"}
    assert {item["source_id"] for item in suggestions} == {draft["id"]}
    kinds = {item["candidate_kind"] for item in suggestions}
    assert {"relationship", "timeline_event", "entity"}.issubset(kinds)

    relationship = next(item for item in suggestions if item["candidate_kind"] == "relationship")
    applied_relationship = client.post(
        f"/worlds/{wid}/suggestions/{relationship['id']}/apply",
        json={"mode": "create_relationship"},
    )
    assert applied_relationship.status_code == 200
    assert applied_relationship.json()["suggestion"]["status"] == "accepted"
    assert applied_relationship.json()["relationship"]["source_entity_id"] == asha["id"]
    assert applied_relationship.json()["relationship"]["target_entity_id"] == bell["id"]

    event = next(item for item in suggestions if item["candidate_kind"] == "timeline_event")
    applied_event = client.post(
        f"/worlds/{wid}/suggestions/{event['id']}/apply",
        json={"mode": "create_timeline_event"},
    )
    assert applied_event.status_code == 200
    assert applied_event.json()["timeline_event"]["title"]


def test_draft_extract_preview_returns_candidates_without_creating_suggestions(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Preview Desk"}).json()
    excerpt = "During the ash season, Mira Voss carried the blue writ."
    draft = client.post(
        f"/worlds/{world['id']}/drafts",
        json={"title": "Marked Scene", "body": f"Opening.\n{excerpt}\nClosing."},
    ).json()

    preview = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/preview",
        json={"excerpt": excerpt, "max_candidates": 6},
    )

    assert preview.status_code == 200
    body = preview.json()
    assert body["excerpt"] == excerpt
    assert body["candidates"]
    assert client.get(f"/worlds/{world['id']}/suggestions").json()["suggestions"] == []


def test_draft_extract_queue_creates_suggestions_from_edited_candidates(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Queue Desk"}).json()
    excerpt = "The blue writ opens sealed roads."
    draft = client.post(
        f"/worlds/{world['id']}/drafts",
        json={"title": "Scene", "body": excerpt},
    ).json()

    queued = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/queue",
        json={
            "excerpt": excerpt,
            "instruction": "Queue edited lore",
            "candidates": [
                {
                    "candidate_kind": "lore_note",
                    "suggested_name": "Edited Blue Writ",
                    "suggested_type": "artifact_lore",
                    "content": "Edited content for sealed roads.",
                    "payload": {"title": "Edited payload title", "body": "Payload body"},
                }
            ],
        },
    )

    assert queued.status_code == 200
    suggestion = queued.json()["suggestions"][0]
    assert suggestion["candidate_kind"] == "lore_note"
    assert suggestion["source_type"] == "draft"
    assert suggestion["source_id"] == draft["id"]
    assert suggestion["source_excerpt"] == excerpt
    assert suggestion["suggested_name"] == "Edited Blue Writ"
    assert suggestion["suggested_type"] == "artifact_lore"
    assert suggestion["content"] == "Edited content for sealed roads."
    assert suggestion["payload"] == {"title": "Edited payload title", "body": "Payload body"}


def test_draft_extract_rejects_excerpt_not_in_saved_body(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Extraction Errors"}).json()
    draft = client.post(
        f"/worlds/{world['id']}/drafts",
        json={"title": "Scene", "body": "Only this text is saved."},
    ).json()

    missing = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract",
        json={"excerpt": "Unsaved text"},
    )
    assert missing.status_code == 400

    unknown = client.post(
        f"/worlds/{world['id']}/drafts/00000000-0000-0000-0000-000000000001/extract",
        json={"excerpt": "Only this text is saved."},
    )
    assert unknown.status_code == 404


def test_draft_extract_preview_and_queue_reject_invalid_requests(client: TestClient) -> None:
    world = client.post("/worlds", json={"title": "Extraction Errors"}).json()
    draft = client.post(
        f"/worlds/{world['id']}/drafts",
        json={"title": "Scene", "body": "Only this text is saved."},
    ).json()

    preview_missing = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/preview",
        json={"excerpt": "Unsaved text"},
    )
    assert preview_missing.status_code == 400

    queue_missing = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/queue",
        json={
            "excerpt": "Unsaved text",
            "candidates": [
                {
                    "candidate_kind": "entity",
                    "suggested_name": "Only",
                    "content": "Only this text is saved.",
                }
            ],
        },
    )
    assert queue_missing.status_code == 400

    empty_candidates = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/queue",
        json={"excerpt": "Only this text is saved.", "candidates": []},
    )
    assert empty_candidates.status_code == 422

    invalid_kind = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract/queue",
        json={
            "excerpt": "Only this text is saved.",
            "candidates": [
                {
                    "candidate_kind": "place",
                    "suggested_name": "Only",
                    "content": "Only this text is saved.",
                }
            ],
        },
    )
    assert invalid_kind.status_code == 422


def test_draft_extract_accepts_valid_llm_json(client: TestClient) -> None:
    llm = _JsonLLM(
        '{"candidates":[{"candidate_kind":"lore_note","suggested_name":"Blue Writ",'
        '"content":"The blue writ opens sealed roads.","payload":{"title":"Blue Writ",'
        '"body":"The blue writ opens sealed roads."}}]}'
    )
    fresh = WorldService(driver=_driver(), llm=llm)
    app.dependency_overrides[get_world_service] = lambda: fresh
    world = client.post("/worlds", json={"title": "LLM Extraction"}).json()
    draft = client.post(
        f"/worlds/{world['id']}/drafts",
        json={"title": "Scene", "body": "The blue writ opens sealed roads."},
    ).json()

    extracted = client.post(
        f"/worlds/{world['id']}/drafts/{draft['id']}/extract",
        json={"excerpt": "The blue writ opens sealed roads."},
    )
    assert extracted.status_code == 200
    suggestion = extracted.json()["suggestions"][0]
    assert suggestion["candidate_kind"] == "lore_note"
    assert suggestion["suggested_name"] == "Blue Writ"

    applied = client.post(
        f"/worlds/{world['id']}/suggestions/{suggestion['id']}/apply",
        json={"mode": "create_lore_note"},
    )
    assert applied.status_code == 200
    assert applied.json()["lore_note"]["title"] == "Blue Writ"


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


def test_consistency_issue_lifecycle_api(client: TestClient) -> None:
    r = client.post("/worlds", json={"title": "Sparse", "tone": "bright"})
    wid = r.json()["id"]
    client.post(
        f"/worlds/{wid}/entities",
        json={"name": "A", "entity_type": "Character", "description": ""},
    )

    report = client.get(f"/worlds/{wid}/consistency")
    assert report.status_code == 200
    payload = report.json()
    missing_description = next(
        issue for issue in payload["issues"] if issue["code"] == "missing_description"
    )
    issue_id = missing_description["issue_id"]
    assert missing_description["status"] == "open"

    listed = client.get(f"/worlds/{wid}/consistency/issues")
    assert listed.status_code == 200
    assert any(issue["id"] == issue_id for issue in listed.json()["issues"])

    ignored = client.patch(
        f"/worlds/{wid}/consistency/issues/{issue_id}",
        json={"status": "ignored", "note": "Not relevant"},
    )
    assert ignored.status_code == 200
    assert ignored.json()["status"] == "ignored"
    assert ignored.json()["note"] == "Not relevant"

    filtered_report = client.get(f"/worlds/{wid}/consistency").json()
    assert all(issue["issue_id"] != issue_id for issue in filtered_report["issues"])
    assert filtered_report["score"] > payload["score"]

    resolved = client.patch(
        f"/worlds/{wid}/consistency/issues/{issue_id}",
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200
    reopened_report = client.get(f"/worlds/{wid}/consistency").json()
    reopened = next(issue for issue in reopened_report["issues"] if issue["issue_id"] == issue_id)
    assert reopened["status"] == "reopened"
    assert reopened["note"] == "Not relevant"


def test_consistency_issue_api_404s(client: TestClient) -> None:
    wid = "00000000-0000-0000-0000-000000000099"
    issue_id = "00000000-0000-0000-0000-000000000088"
    assert client.get(f"/worlds/{wid}/consistency/issues").status_code == 404
    assert (
        client.patch(
            f"/worlds/{wid}/consistency/issues/{issue_id}",
            json={"status": "ignored"},
        ).status_code
        == 404
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
