from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from openai import OpenAI

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


def _resolve_mode(settings: Settings) -> Literal["none", "openrouter"]:
    if settings.llm_backend == "none":
        return "none"
    if settings.openrouter_api_key and settings.openrouter_model:
        return "openrouter"
    return "none"


class _OpenRouterBackend:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        key = settings.openrouter_api_key
        assert key is not None
        self._client = OpenAI(api_key=key, base_url=settings.openrouter_base_url)

    def chat(self, messages: list[dict[str, str]]) -> str:
        key = self._settings.openrouter_api_key
        model = self._settings.openrouter_model
        assert key is not None
        assert model is not None

        headers: dict[str, str] = {}
        if self._settings.openrouter_http_referer:
            headers["HTTP-Referer"] = self._settings.openrouter_http_referer
        if self._settings.openrouter_app_title:
            headers["X-OpenRouter-Title"] = self._settings.openrouter_app_title

        completion = self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
            extra_headers=headers or None,
        )
        choices = getattr(completion, "choices", None) or []
        if not choices:
            return ""
        msg = getattr(choices[0], "message", None)
        content = getattr(msg, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
        return ""


class LLMService:
    """Optional OpenRouter chat completion integration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._mode = _resolve_mode(settings)
        self._backend: _OpenRouterBackend | None = None
        if self._mode == "openrouter":
            self._backend = _OpenRouterBackend(settings)

    @property
    def mode(self) -> Literal["none", "openrouter"]:
        return self._mode

    def enabled(self) -> bool:
        return self._mode != "none" and self._backend is not None

    def generate_section(self, world: WorldRead, section: Section) -> str | None:
        if not self.enabled() or self._backend is None:
            return None
        messages = _messages_for_section(world, section)
        try:
            text = self._backend.chat(messages)
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
