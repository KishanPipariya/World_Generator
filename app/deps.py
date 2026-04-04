from app.services.world_service import WorldService

_world_service = WorldService()


def get_world_service() -> WorldService:
    return _world_service
