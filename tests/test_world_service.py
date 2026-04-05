from __future__ import annotations

from uuid import UUID

from app.schemas.world import WorldCreate
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



class _FakeLLM:
    def __init__(self, content: str | None = "from-llm") -> None:
        self._content = content
        self.calls: list[tuple[str, str]] = []

    def enabled(self) -> bool:
        return True

    def generate_section(self, world, section):  # noqa: ANN001
        self.calls.append((world.title, section))
        return self._content


def test_generate_stub_uses_llm_when_enabled_and_non_empty() -> None:
    llm = _FakeLLM("generated glossary")
    svc = WorldService(driver=_FakeDriver(), llm=llm)
    w = svc.create(WorldCreate(title="Realm"))
    out = svc.generate_stub(w.id, "glossary")
    assert out is not None
    sec, text = out
    assert sec == "glossary"
    assert text == "generated glossary"
    assert llm.calls == [("Realm", "glossary")]


def test_generate_stub_falls_back_when_llm_returns_empty() -> None:
    llm = _FakeLLM("")
    svc = WorldService(driver=_FakeDriver(), llm=llm)
    w = svc.create(WorldCreate(title="X"))
    out = svc.generate_stub(w.id, "glossary")
    assert out is not None
    _, text = out
    assert "[stub glossary" in text
    assert "X" in text


def test_generate_stub_falls_back_when_no_llm() -> None:
    svc = WorldService(driver=_FakeDriver(), llm=None)
    w = svc.create(WorldCreate(title="Y"))
    out = svc.generate_stub(w.id, "timeline_hint")
    assert out is not None
    sec, text = out
    assert sec == "timeline_hint"
    assert "[stub timeline hint" in text


def test_generate_stub_unknown_world_returns_none() -> None:
    svc = WorldService(driver=_FakeDriver(), llm=None)
    fake_id = UUID("00000000-0000-0000-0000-000000000001")
    assert svc.generate_stub(fake_id, "glossary") is None
