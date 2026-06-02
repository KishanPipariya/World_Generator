from fastapi import APIRouter

from app.api.routes.world_routes import (
    campaign_dm,
    canon,
    consistency,
    core,
    drafts,
    exports,
    generation,
    graph,
    lore,
    planning,
    suggestions,
    timeline,
)

router = APIRouter()

for domain_router in (
    core.router,
    generation.router,
    canon.router,
    consistency.router,
    suggestions.router,
    timeline.router,
    graph.router,
    planning.router,
    campaign_dm.router,
    lore.router,
    drafts.router,
    exports.router,
):
    router.include_router(domain_router)
