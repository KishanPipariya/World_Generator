from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Settings:
    """LLM settings from the environment."""

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
    raw = (os.environ.get("WORLD_GENERATOR_LLM_BACKEND") or "auto").strip().lower()
    if raw not in ("auto", "none", "llama", "vllm"):
        raw = "auto"
    backend: Literal["auto", "none", "llama", "vllm"] = raw  # type: ignore[assignment]

    gguf = os.environ.get("WORLD_GENERATOR_GGUF_PATH")
    vllm_url = os.environ.get("WORLD_GENERATOR_VLLM_BASE_URL")
    vllm_model = os.environ.get("WORLD_GENERATOR_VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    vllm_key = os.environ.get("WORLD_GENERATOR_VLLM_API_KEY")

    return Settings(
        llm_backend=backend,
        gguf_path=gguf.strip() if gguf else None,
        vllm_base_url=vllm_url.rstrip("/") if vllm_url else None,
        vllm_model=vllm_model,
        vllm_api_key=vllm_key,
        llama_n_ctx=int(os.environ.get("WORLD_GENERATOR_LLAMA_N_CTX", "4096")),
        llama_n_gpu_layers=int(os.environ.get("WORLD_GENERATOR_LLAMA_N_GPU_LAYERS", "0")),
        llama_max_tokens=int(os.environ.get("WORLD_GENERATOR_LLM_MAX_TOKENS", "768")),
        llama_temperature=float(os.environ.get("WORLD_GENERATOR_LLM_TEMPERATURE", "0.65")),
    )
