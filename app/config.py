from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
# Symlink checked into the repo: models/qwen2.5-14b-instruct-q5_k_m.gguf → ../../CYOA_TUI/...
_DEFAULT_GGUF = _REPO_ROOT / "models" / "qwen2.5-14b-instruct-q5_k_m.gguf"


def _resolved_gguf_path() -> str | None:
    env = os.environ.get("WORLD_GENERATOR_GGUF_PATH")
    if env and env.strip():
        return env.strip()
    if _DEFAULT_GGUF.is_file():
        return str(_DEFAULT_GGUF)
    return None


@dataclass(frozen=True)
class Settings:
    """Database and LLM settings from the environment."""

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    llm_backend: Literal["auto", "none", "llama", "vllm"]
    gguf_path: str | None
    vllm_base_url: str | None
    vllm_model: str
    vllm_api_key: str | None
    llama_n_ctx: int
    llama_n_gpu_layers: int
    llama_max_tokens: int
    llama_temperature: float


def load_settings() -> Settings:
    load_dotenv()
    
    raw = (os.environ.get("WORLD_GENERATOR_LLM_BACKEND") or "auto").strip().lower()
    if raw not in ("auto", "none", "llama", "vllm"):
        raw = "auto"
    backend: Literal["auto", "none", "llama", "vllm"] = raw  # type: ignore[assignment]

    gguf = _resolved_gguf_path()
    vllm_url = os.environ.get("WORLD_GENERATOR_VLLM_BASE_URL")
    vllm_model = os.environ.get("WORLD_GENERATOR_VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    vllm_key = os.environ.get("WORLD_GENERATOR_VLLM_API_KEY")

    return Settings(
        neo4j_uri=os.environ.get("WORLD_GENERATOR_NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.environ.get("WORLD_GENERATOR_NEO4J_USER", "neo4j"),
        neo4j_password=os.environ.get("WORLD_GENERATOR_NEO4J_PASSWORD", "password"),
        llm_backend=backend,
        gguf_path=gguf,
        vllm_base_url=vllm_url.rstrip("/") if vllm_url else None,
        vllm_model=vllm_model,
        vllm_api_key=vllm_key,
        llama_n_ctx=int(os.environ.get("WORLD_GENERATOR_LLAMA_N_CTX", "4096")),
        llama_n_gpu_layers=int(os.environ.get("WORLD_GENERATOR_LLAMA_N_GPU_LAYERS", "0")),
        llama_max_tokens=int(os.environ.get("WORLD_GENERATOR_LLM_MAX_TOKENS", "768")),
        llama_temperature=float(os.environ.get("WORLD_GENERATOR_LLM_TEMPERATURE", "0.65")),
    )
