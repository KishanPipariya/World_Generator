from __future__ import annotations

import os
import tempfile
from uuid import UUID

from app.schemas.world import ConsistencyIssueUpdate, WorldCreate
from app.services.world_service import WorldService
from app.sqlite_driver import SQLiteDriver


def _driver() -> SQLiteDriver:
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    driver = SQLiteDriver(path)
    return driver


class _StubLLM:
    def __init__(self, content: str | None = "from-llm") -> None:
        self._content = content
        self.calls: list[tuple[str, str]] = []

    def enabled(self) -> bool:
        return True

    def generate_section(self, world, section):  # noqa: ANN001
        self.calls.append((world.title, section))
        return self._content

    def generate_agentic(self, world, context, instruction): # noqa: ANN001
        self.calls.append((world.title, "agentic", instruction))
        return self._content



def test_generate_stub_uses_llm_when_enabled_and_non_empty() -> None:
    llm = _StubLLM("generated glossary")
    svc = WorldService(driver=_driver(), llm=llm)
    w = svc.create(WorldCreate(title="Realm"))
    out = svc.generate_stub(w.id, "glossary")
    assert out is not None
    sec, text = out
    assert sec == "glossary"
    assert text == "generated glossary"
    assert llm.calls == [("Realm", "glossary")]


def test_generate_stub_falls_back_when_llm_returns_empty() -> None:
    llm = _StubLLM("")
    svc = WorldService(driver=_driver(), llm=llm)
    w = svc.create(WorldCreate(title="X"))
    out = svc.generate_stub(w.id, "glossary")
    assert out is not None
    _, text = out
    assert "[stub glossary" in text
    assert "X" in text


def test_generate_stub_falls_back_when_no_llm() -> None:
    svc = WorldService(driver=_driver(), llm=None)
    w = svc.create(WorldCreate(title="Y"))
    out = svc.generate_stub(w.id, "timeline_hint")
    assert out is not None
    sec, text = out
    assert sec == "timeline_hint"
    assert "[stub timeline hint" in text


def test_generate_stub_unknown_world_returns_none() -> None:
    svc = WorldService(driver=_driver(), llm=None)
    fake_id = UUID("00000000-0000-0000-0000-000000000001")
    assert svc.generate_stub(fake_id, "glossary") is None


def test_agentic_generate_uses_llm_and_context() -> None:
    llm = _StubLLM("agentic content")
    svc = WorldService(driver=_driver(), llm=llm)
    w = svc.create(WorldCreate(title="Realm"))
    text, eid = svc.agentic_generate(w.id, "some instruction", None, None)
    assert text == "agentic content"
    assert eid is None
    assert llm.calls == [("Realm", "agentic", "some instruction")]


def test_consistency_report_persists_and_updates_issue_state() -> None:
    svc = WorldService(driver=_driver(), llm=None)
    world = svc.create(WorldCreate(title="Sparse", tone="bright"))
    entity = svc.create_entity(world.id, "A", "Character", "", {})

    first_report = svc.consistency_report(world.id)
    assert first_report is not None
    missing_description = next(
        issue for issue in first_report.issues if issue.code == "missing_description"
    )
    assert missing_description.issue_id is not None
    assert missing_description.status == "open"
    assert missing_description.entity_id == entity.id

    second_report = svc.consistency_report(world.id)
    assert second_report is not None
    repeated = next(issue for issue in second_report.issues if issue.code == "missing_description")
    assert repeated.issue_id == missing_description.issue_id
    assert repeated.last_seen is not None
    assert missing_description.first_seen is not None
    assert repeated.last_seen >= missing_description.first_seen


def test_consistency_report_hides_ignored_and_reopens_resolved_issues() -> None:
    svc = WorldService(driver=_driver(), llm=None)
    world = svc.create(WorldCreate(title="Sparse", tone="bright"))
    svc.create_entity(world.id, "A", "Character", "", {})
    report = svc.consistency_report(world.id)
    assert report is not None
    issue = next(item for item in report.issues if item.code == "missing_description")
    assert issue.issue_id is not None

    ignored = svc.update_consistency_issue_state(
        world.id,
        issue.issue_id,
        ConsistencyIssueUpdate(status="ignored", note="Handled elsewhere"),
    )
    assert ignored is not None
    ignored_report = svc.consistency_report(world.id)
    assert ignored_report is not None
    assert all(item.issue_id != issue.issue_id for item in ignored_report.issues)
    assert ignored_report.score > report.score

    resolved = svc.update_consistency_issue_state(
        world.id,
        issue.issue_id,
        ConsistencyIssueUpdate(status="resolved"),
    )
    assert resolved is not None
    reopened_report = svc.consistency_report(world.id)
    assert reopened_report is not None
    reopened = next(item for item in reopened_report.issues if item.issue_id == issue.issue_id)
    assert reopened.status == "reopened"
    assert reopened.note == "Handled elsewhere"
