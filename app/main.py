from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.worlds import router as worlds_router

app = FastAPI(
    title="Literary World Generator",
    description="API for literary world-building and future generator features.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(worlds_router)
