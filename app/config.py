from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Database and LLM settings from the environment."""

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    llm_backend: Literal["openrouter", "none"]
    openrouter_api_key: str | None
    openrouter_model: str | None
    openrouter_base_url: str
    openrouter_http_referer: str | None
    openrouter_app_title: str | None
    llm_max_tokens: int
    llm_temperature: float


def load_settings() -> Settings:
    load_dotenv()

    raw = (os.environ.get("WORLD_GENERATOR_LLM_BACKEND") or "openrouter").strip().lower()
    if raw not in ("openrouter", "none"):
        raw = "openrouter"
    backend: Literal["openrouter", "none"] = raw  # type: ignore[assignment]

    openrouter_base_url = os.environ.get(
        "WORLD_GENERATOR_OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    ).rstrip("/")

    return Settings(
        neo4j_uri=os.environ.get("WORLD_GENERATOR_NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.environ.get("WORLD_GENERATOR_NEO4J_USER", "neo4j"),
        neo4j_password=os.environ.get("WORLD_GENERATOR_NEO4J_PASSWORD", "password"),
        llm_backend=backend,
        openrouter_api_key=os.environ.get("WORLD_GENERATOR_OPENROUTER_API_KEY"),
        openrouter_model=os.environ.get("WORLD_GENERATOR_OPENROUTER_MODEL"),
        openrouter_base_url=openrouter_base_url,
        openrouter_http_referer=os.environ.get("WORLD_GENERATOR_OPENROUTER_HTTP_REFERER"),
        openrouter_app_title=os.environ.get("WORLD_GENERATOR_OPENROUTER_APP_TITLE"),
        llm_max_tokens=int(os.environ.get("WORLD_GENERATOR_LLM_MAX_TOKENS", "768")),
        llm_temperature=float(os.environ.get("WORLD_GENERATOR_LLM_TEMPERATURE", "0.65")),
    )
