from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.schemas.world import WorldRead
from app.services.llm_service import LLMService, _OpenRouterBackend, _world_context


def _base_settings(**overrides: Any) -> Settings:
    s = Settings(
        sqlite_path=":memory:",
        llm_backend="openrouter",
        openrouter_api_key="secret",
        openrouter_model="test-model",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_http_referer=None,
        openrouter_app_title=None,
        llm_max_tokens=128,
        llm_temperature=0.5,
        jwt_secret="test-secret",
        jwt_expires_minutes=60,
        allow_signup=True,
    )
    return replace(s, **overrides) if overrides else s


def _world() -> WorldRead:
    return WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My World",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )


def _completion(content: str | None = None, *, choices: list[Any] | None = None) -> SimpleNamespace:
    if choices is None:
        choices = [SimpleNamespace(message=SimpleNamespace(content=content))]
    return SimpleNamespace(choices=choices)


def _mock_openai_client(*completions: SimpleNamespace) -> tuple[MagicMock, MagicMock]:
    mock_client = MagicMock()
    create = mock_client.chat.completions.create
    create.side_effect = list(completions) if len(completions) > 1 else None
    if len(completions) == 1:
        create.return_value = completions[0]
    mock_openai = MagicMock(return_value=mock_client)
    return mock_openai, mock_client


def test_resolve_mode_none_when_backend_explicitly_none() -> None:
    svc = LLMService(_base_settings(llm_backend="none"))
    assert svc.mode == "none"
    assert not svc.enabled()


def test_resolve_mode_none_when_openrouter_key_missing() -> None:
    svc = LLMService(_base_settings(openrouter_api_key=None))
    assert svc.mode == "none"
    assert not svc.enabled()


def test_resolve_mode_none_when_openrouter_model_missing() -> None:
    svc = LLMService(_base_settings(openrouter_model=None))
    assert svc.mode == "none"
    assert not svc.enabled()


def test_resolve_mode_openrouter_when_key_and_model_present() -> None:
    svc = LLMService(_base_settings())
    assert svc.mode == "openrouter"
    assert svc.enabled()


def test_world_context_includes_optional_fields() -> None:
    w = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "T",
            "tone": "dark",
            "era_notes": "future",
            "seed": "s1",
            "created_at": "2020-01-01T00:00:00Z",
        }
    )
    ctx = _world_context(w)
    assert "Title: T" in ctx
    assert "Tone: dark" in ctx
    assert "Era / setting notes: future" in ctx
    assert "Seed / motif: s1" in ctx


def test_openrouter_backend_uses_openai_sdk_chat_completion_request() -> None:
    s = _base_settings(
        openrouter_model="m",
        openrouter_http_referer="https://example.test",
        openrouter_app_title="World Generator",
        llm_max_tokens=16,
        llm_temperature=0.1,
    )
    mock_openai, mock_client = _mock_openai_client(_completion("  answer  "))

    with patch("app.services.llm_service.OpenAI", mock_openai):
        out = _OpenRouterBackend(s).chat([{"role": "user", "content": "hi"}])

    assert out == "answer"
    mock_openai.assert_called_once_with(api_key="secret", base_url="https://openrouter.ai/api/v1")
    mock_client.chat.completions.create.assert_called_once_with(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=16,
        temperature=0.1,
        extra_headers={
            "HTTP-Referer": "https://example.test",
            "X-OpenRouter-Title": "World Generator",
        },
    )


def test_openrouter_backend_uses_configured_base_url() -> None:
    s = _base_settings(openrouter_base_url="http://example/v1")
    mock_openai, _mock_client = _mock_openai_client(_completion("x"))

    with patch("app.services.llm_service.OpenAI", mock_openai):
        _OpenRouterBackend(s).chat([])

    mock_openai.assert_called_once_with(api_key="secret", base_url="http://example/v1")


def test_openrouter_backend_returns_empty_string_for_empty_or_missing_choices() -> None:
    for completion in (_completion(choices=[]), SimpleNamespace()):
        mock_openai, _mock_client = _mock_openai_client(completion)
        with patch("app.services.llm_service.OpenAI", mock_openai):
            assert _OpenRouterBackend(_base_settings()).chat([]) == ""


def test_generate_section_returns_none_when_llm_disabled() -> None:
    svc = LLMService(_base_settings(llm_backend="none"))
    assert svc.generate_section(_world(), "glossary") is None


def test_generate_section_uses_openrouter_backend() -> None:
    mock_openai, mock_client = _mock_openai_client(_completion("glossary text"))

    with patch("app.services.llm_service.OpenAI", mock_openai):
        svc = LLMService(_base_settings())
        assert svc.mode == "openrouter"
        out = svc.generate_section(_world(), "glossary")

    assert out == "glossary text"
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_generate_section_returns_none_on_backend_exception() -> None:
    svc = LLMService(_base_settings())
    w = _world()
    with patch.object(svc._backend, "chat", side_effect=RuntimeError("inference failed")):
        assert svc.generate_section(w, "glossary") is None


def test_generate_agentic_uses_author_and_critic() -> None:
    mock_openai, mock_client = _mock_openai_client(
        _completion("author output"),
        _completion("critic output"),
    )

    w = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My World",
            "tone": "dark",
            "era_notes": "fantasy",
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )

    with patch("app.services.llm_service.OpenAI", mock_openai):
        out = LLMService(_base_settings()).generate_agentic(w, "context string", "instruction test")

    assert out == "critic output"
    assert mock_client.chat.completions.create.call_count == 2


def test_generate_agentic_returns_author_text_when_critic_fails() -> None:
    svc = LLMService(_base_settings())
    assert svc._backend is not None

    with patch.object(
        svc._backend,
        "chat",
        side_effect=["author output", RuntimeError("critic failed")],
    ):
        out = svc.generate_agentic(_world(), "context string", "instruction test")

    assert out == "author output"
