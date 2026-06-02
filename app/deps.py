from app.config import load_settings
from app.services.auth_service import AuthService
from app.services.llm_service import LLMService, build_llm_service
from app.services.world import WorldService
from app.sqlite_driver import SQLiteDriver

_settings = load_settings()
_driver = SQLiteDriver(_settings.sqlite_path)
_llm_service = build_llm_service()
_world_service = WorldService(driver=_driver, llm=_llm_service)
_auth_service = AuthService(driver=_driver)
_schema_initialized = False
_auth_schema_initialized = False


def get_llm_service() -> LLMService:
    return _llm_service


def get_world_service() -> WorldService:
    global _schema_initialized
    if not _schema_initialized:
        _world_service.initialize_schema()
        _schema_initialized = True
    return _world_service


def get_auth_service() -> AuthService:
    global _auth_schema_initialized
    if not _auth_schema_initialized:
        _auth_service.initialize_schema()
        _auth_schema_initialized = True
    return _auth_service
