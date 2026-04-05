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

    def generate_agentic(self, world: WorldRead, context: str, instruction: str) -> str | None:
        if not self.enabled() or self._backend is None:
            return None
        
        # 1. Author Agent
        author_system = (
            "You are a creative world-building Author. "
            "Generate detailed, rich lore based on the provided instruction and context."
        )
        author_user = (
            f"World Knowledge Base (Context):\n{context}\n\n"
            f"World Tone:\n{world.tone or 'Not specified'}\n\n"
            f"Era Notes:\n{world.era_notes or 'Not specified'}\n\n"
            f"Instruction: {instruction}\n\n"
            "Please generate the requested lore now."
        )
        try:
            author_text = self._backend.chat(
                [{"role": "system", "content": author_system}, {"role": "user", "content": author_user}]
            )
        except Exception:
            logger.exception("Author agent generation failed")
            return None

        if not author_text:
            return None

        # 2. Critic Agent
        critic_system = (
            "You are a critical world-building Editor. "
            "Review the provided generated content against the world's tone and era notes. "
            "If it fits well, output the original content mostly unchanged. If it contradicts "
            "the tone, era, or provided context, rewrite it to fit better while retaining the core ideas. "
            "Output ONLY the finalized prose, no prepended explanations or meta commentary."
        )
        critic_user = (
            f"World Tone: {world.tone or 'Not specified'}\n"
            f"Era Notes: {world.era_notes or 'Not specified'}\n\n"
            f"Generated Content to Review:\n{author_text}\n\n"
            "Review and output the finalized content."
        )
        try:
            critic_text = self._backend.chat(
                [{"role": "system", "content": critic_system}, {"role": "user", "content": critic_user}]
            )
        except Exception:
            logger.exception("Critic agent generation failed")
            return author_text  # Fallback to the author text if critic fails

        return critic_text if critic_text else author_text


def build_llm_service() -> LLMService:
    return LLMService(load_settings())
