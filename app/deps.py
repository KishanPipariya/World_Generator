from neo4j import GraphDatabase

from app.config import load_settings
from app.services.llm_service import LLMService, build_llm_service
from app.services.world_service import WorldService

_settings = load_settings()
_driver = GraphDatabase.driver(
    _settings.neo4j_uri, 
    auth=(_settings.neo4j_user, _settings.neo4j_password)
)
_llm_service = build_llm_service()
_world_service = WorldService(driver=_driver, llm=_llm_service)


def get_llm_service() -> LLMService:
    return _llm_service


def get_world_service() -> WorldService:
    return _world_service
