from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Database and LLM settings from the environment."""

    sqlite_path: str

    llm_backend: Literal["openrouter", "none"]
    openrouter_api_key: str | None
    openrouter_model: str | None
    openrouter_base_url: str
    openrouter_http_referer: str | None
    openrouter_app_title: str | None
    llm_max_tokens: int
    llm_temperature: float
    jwt_secret: str
    jwt_expires_minutes: int
    allow_signup: bool


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

    jwt_secret = os.environ.get("WORLD_GENERATOR_JWT_SECRET", "dev-insecure-change-me-at-least-32-bytes")

    return Settings(
        sqlite_path=os.environ.get("WORLD_GENERATOR_SQLITE_PATH", "./data/world_generator.sqlite3"),
        llm_backend=backend,
        openrouter_api_key=os.environ.get("WORLD_GENERATOR_OPENROUTER_API_KEY"),
        openrouter_model=os.environ.get("WORLD_GENERATOR_OPENROUTER_MODEL"),
        openrouter_base_url=openrouter_base_url,
        openrouter_http_referer=os.environ.get("WORLD_GENERATOR_OPENROUTER_HTTP_REFERER"),
        openrouter_app_title=os.environ.get("WORLD_GENERATOR_OPENROUTER_APP_TITLE"),
        llm_max_tokens=int(os.environ.get("WORLD_GENERATOR_LLM_MAX_TOKENS", "768")),
        llm_temperature=float(os.environ.get("WORLD_GENERATOR_LLM_TEMPERATURE", "0.65")),
        jwt_secret=jwt_secret,
        jwt_expires_minutes=int(os.environ.get("WORLD_GENERATOR_JWT_EXPIRES_MINUTES", "1440")),
        allow_signup=(os.environ.get("WORLD_GENERATOR_ALLOW_SIGNUP", "true").strip().lower() == "true"),
    )
