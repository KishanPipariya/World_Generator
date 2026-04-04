from __future__ import annotations

import logging
import os
import threading
from typing import TYPE_CHECKING, Any, Literal

import httpx

from app.config import Settings, load_settings

if TYPE_CHECKING:
    from app.schemas.world import WorldRead

logger = logging.getLogger(__name__)

Section = Literal["glossary", "timeline_hint"]


def _world_context(world: WorldRead) -> str:
    parts = [f"Title: {world.title}"]
    if world.tone:
        parts.append(f"Tone: {world.tone}")
    if world.era_notes:
        parts.append(f"Era / setting notes: {world.era_notes}")
    if world.seed:
        parts.append(f"Seed / motif: {world.seed}")
    return "\n".join(parts)


def _messages_for_section(world: WorldRead, section: Section) -> list[dict[str, str]]:
    ctx = _world_context(world)
    system = (
        "You are a concise literary world-building assistant. "
        "Reply with readable prose only — no preambles or meta commentary."
    )
    if section == "glossary":
        user = (
            f"{ctx}\n\n"
            "Write a short glossary for this world: 6–10 invented or repurposed terms, "
            "each with a one-line gloss. Use a clear list format (term — gloss)."
        )
    else:
        user = (
            f"{ctx}\n\n"
            "Outline a brief narrative timeline hint: 4–6 beats (no full plot), "
            "showing how pressure builds from inciting change toward a possible resolution."
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _resolve_mode(settings: Settings) -> Literal["none", "llama", "vllm"]:
    b = settings.llm_backend
    if b == "none":
        return "none"
    if b == "llama":
        path = settings.gguf_path
        return "llama" if path and os.path.isfile(path) else "none"
    if b == "vllm":
        return "vllm" if settings.vllm_base_url else "none"
    # auto
    if settings.gguf_path and os.path.isfile(settings.gguf_path):
        return "llama"
    if settings.vllm_base_url:
        return "vllm"
    return "none"


class _LlamaCppBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._llm: Any = None

    def _ensure(self) -> Any:
        if self._llm is not None:
            return self._llm
        from llama_cpp import Llama

        path = self._settings.gguf_path
        assert path is not None
        self._llm = Llama(
            model_path=path,
            n_ctx=self._settings.llama_n_ctx,
            n_gpu_layers=self._settings.llama_n_gpu_layers,
            verbose=False,
        )
        return self._llm

    def chat(self, messages: list[dict[str, str]]) -> str:
        llm = self._ensure()
        with self._lock:
            out = llm.create_chat_completion(
                messages=messages,
                max_tokens=self._settings.llama_max_tokens,
                temperature=self._settings.llama_temperature,
            )
        choice = out["choices"][0]
        msg = choice.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        # Some builds return text in a different shape
        text = choice.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
        return ""


class _VllmBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        base = settings.vllm_base_url
        assert base is not None
        self._url = f"{base}/chat/completions"

    def chat(self, messages: list[dict[str, str]]) -> str:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        key = self._settings.vllm_api_key
        if key:
            headers["Authorization"] = f"Bearer {key}"
        payload = {
            "model": self._settings.vllm_model,
            "messages": messages,
            "max_tokens": self._settings.llama_max_tokens,
            "temperature": self._settings.llama_temperature,
        }
        with httpx.Client(timeout=120.0) as client:
            r = client.post(self._url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        return ""


class LLMService:
    """Local llama.cpp (GGUF) or remote vLLM (OpenAI-compatible HTTP)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._mode = _resolve_mode(settings)
        self._backend: _LlamaCppBackend | _VllmBackend | None = None
        if self._mode == "llama":
            self._backend = _LlamaCppBackend(settings)
        elif self._mode == "vllm":
            self._backend = _VllmBackend(settings)

    @property
    def mode(self) -> Literal["none", "llama", "vllm"]:
        return self._mode

    def enabled(self) -> bool:
        return self._mode != "none" and self._backend is not None

    def generate_section(self, world: WorldRead, section: Section) -> str | None:
        if not self.enabled() or self._backend is None:
            return None
        messages = _messages_for_section(world, section)
        try:
            text = self._backend.chat(messages)
        except ImportError:
            logger.warning(
                "LLM dependency missing; for GGUF models install with: uv sync --extra local-llm"
            )
            return None
        except Exception:
            logger.exception("LLM generation failed for section %s", section)
            return None
        return text if text else None


def build_llm_service() -> LLMService:
    return LLMService(load_settings())
