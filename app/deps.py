from app.services.llm_service import LLMService, build_llm_service
from app.services.world_service import WorldService

_llm_service = build_llm_service()
_world_service = WorldService(llm=_llm_service)


def get_llm_service() -> LLMService:
    return _llm_service


def get_world_service() -> WorldService:
    return _world_service
