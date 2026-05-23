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
        if "id" in kwargs and "MATCH (w)<-[belongs]-(e)" in query:
            return _FakeResult(
                [v for v in self.db["entities"].values() if v["world_id"] == kwargs["id"]]
            )
        if "w_id" in kwargs and "MATCH (w)<-[belongs]-(e)" in query:
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



class _FakeLLM:
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


def test_agentic_generate_uses_llm_and_context() -> None:
    llm = _FakeLLM("agentic content")
    svc = WorldService(driver=_FakeDriver(), llm=llm)
    w = svc.create(WorldCreate(title="Realm"))
    text, eid = svc.agentic_generate(w.id, "some instruction", None, None)
    assert text == "agentic content"
    assert eid is None
    assert llm.calls == [("Realm", "agentic", "some instruction")]
