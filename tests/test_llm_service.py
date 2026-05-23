from __future__ import annotations

import os
import sys
from dataclasses import replace
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.schemas.world import WorldRead
from app.config import load_settings
from app.services.llm_service import LLMService, _LlamaCppBackend, _VllmBackend, _world_context


def _base_settings(**overrides: Any) -> Settings:
    s = Settings(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        llm_backend="auto",
        gguf_path=None,
        vllm_base_url=None,
        vllm_model="test-model",
        vllm_api_key=None,
        llama_n_ctx=4096,
        llama_n_gpu_layers=0,
        llama_max_tokens=128,
        llama_temperature=0.5,
    )
    return replace(s, **overrides) if overrides else s


def test_resolve_mode_none_when_backend_explicitly_none() -> None:
    s = _base_settings(llm_backend="none")
    svc = LLMService(s)
    assert svc.mode == "none"
    assert not svc.enabled()


def test_resolve_mode_vllm_when_auto_and_url_set() -> None:
    s = _base_settings(vllm_base_url="http://127.0.0.1:8000/v1")
    svc = LLMService(s)
    assert svc.mode == "vllm"
    assert svc.enabled()


def test_resolve_mode_llama_when_auto_and_gguf_file_exists(tmp_path) -> None:
    fake_gguf = tmp_path / "model.gguf"
    fake_gguf.write_bytes(b"gguf")
    s = _base_settings(gguf_path=str(fake_gguf))
    svc = LLMService(s)
    assert svc.mode == "llama"
    assert svc.enabled()


def test_resolve_mode_prefers_llama_over_vllm_when_both_available(tmp_path) -> None:
    fake_gguf = tmp_path / "model.gguf"
    fake_gguf.write_bytes(b"x")
    s = _base_settings(gguf_path=str(fake_gguf), vllm_base_url="http://127.0.0.1:1/v1")
    svc = LLMService(s)
    assert svc.mode == "llama"


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


def test_vllm_backend_chat_strips_message_content() -> None:
    s = _base_settings(
        llm_backend="vllm",
        vllm_base_url="http://example/v1",
        vllm_model="m",
    )

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "  answer  "}}]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    with patch("app.services.llm_service.httpx.Client", return_value=mock_client):
        backend = _VllmBackend(s)
        out = backend.chat([{"role": "user", "content": "hi"}])

    assert out == "answer"
    mock_client.post.assert_called_once()
    call_kw = mock_client.post.call_args
    assert call_kw[0][0] == "http://example/v1/chat/completions"
    payload = call_kw[1]["json"]
    assert payload["model"] == "m"
    assert payload["messages"] == [{"role": "user", "content": "hi"}]


def test_vllm_backend_sends_bearer_when_api_key_set() -> None:
    s = _base_settings(
        llm_backend="vllm",
        vllm_base_url="http://example/v1",
        vllm_api_key="secret",
    )
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "x"}}]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    with patch("app.services.llm_service.httpx.Client", return_value=mock_client):
        _VllmBackend(s).chat([])

    headers = mock_client.post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer secret"


def test_generate_section_returns_none_when_llm_disabled() -> None:
    s = _base_settings(llm_backend="none")
    svc = LLMService(s)
    w = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "T",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )
    assert svc.generate_section(w, "glossary") is None


def test_generate_section_uses_vllm_backend(tmp_path) -> None:
    fake_gguf = tmp_path / "unused.gguf"
    fake_gguf.write_bytes(b"x")
    s = _base_settings(
        llm_backend="vllm",
        gguf_path=str(fake_gguf),
        vllm_base_url="http://example/v1",
    )
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "glossary text"}}]}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

    w = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "My World",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )

    with patch("app.services.llm_service.httpx.Client", return_value=mock_client):
        svc = LLMService(s)
        assert svc.mode == "vllm"
        out = svc.generate_section(w, "glossary")

    assert out == "glossary text"


@patch("app.services.llm_service._LlamaCppBackend.chat")
def test_generate_section_returns_none_on_llama_exception(mock_chat, tmp_path) -> None:
    fake_gguf = tmp_path / "model.gguf"
    fake_gguf.write_bytes(b"x")
    s = _base_settings(llm_backend="llama", gguf_path=str(fake_gguf))
    mock_chat.side_effect = RuntimeError("inference failed")

    svc = LLMService(s)
    w = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "T",
            "tone": None,
            "era_notes": None,
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )
    assert svc.generate_section(w, "glossary") is None


def test_llama_backend_loads_configured_model_and_generates_text(monkeypatch, tmp_path) -> None:
    fake_gguf = tmp_path / "model.gguf"
    fake_gguf.write_bytes(b"GGUF")
    captured: dict[str, Any] = {}

    class _FakeLlama:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def create_chat_completion(self, **kwargs: Any) -> dict[str, Any]:
            captured["completion"] = kwargs
            return {"choices": [{"message": {"content": "  local text  "}}]}

    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=_FakeLlama))
    s = _base_settings(
        llm_backend="llama",
        gguf_path=str(fake_gguf),
        llama_n_ctx=512,
        llama_n_gpu_layers=0,
        llama_max_tokens=16,
        llama_temperature=0.1,
    )

    backend = _LlamaCppBackend(s)
    out = backend.chat([{"role": "user", "content": "Say one short sentence."}])

    assert out == "local text"
    assert captured["model_path"] == str(fake_gguf)
    assert captured["n_ctx"] == 512
    assert captured["n_gpu_layers"] == 0
    assert captured["completion"]["max_tokens"] == 16
    assert captured["completion"]["messages"] == [
        {"role": "user", "content": "Say one short sentence."}
    ]


@pytest.mark.local_llm
def test_local_llm_loads_and_generates_text() -> None:
    if os.environ.get("WORLD_GENERATOR_RUN_LOCAL_LLM_TESTS") != "1":
        pytest.skip("Set WORLD_GENERATOR_RUN_LOCAL_LLM_TESTS=1 to load the local GGUF model.")
    pytest.importorskip("llama_cpp")

    settings = replace(
        load_settings(),
        llm_backend="llama",
        llama_n_ctx=int(os.environ.get("WORLD_GENERATOR_TEST_LLAMA_N_CTX", "512")),
        llama_max_tokens=int(os.environ.get("WORLD_GENERATOR_TEST_LLM_MAX_TOKENS", "24")),
        llama_temperature=0.1,
    )
    if not settings.gguf_path or not os.path.isfile(settings.gguf_path):
        pytest.fail("Local GGUF model path is not configured or does not exist.")

    svc = LLMService(settings)
    assert svc.mode == "llama"
    assert svc.enabled()

    world = WorldRead.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test Lantern",
            "tone": "clear and concise",
            "era_notes": "A small test world used only to verify local inference.",
            "seed": None,
            "created_at": "2020-01-01T00:00:00Z",
        }
    )

    text = svc.generate_section(world, "glossary")

    assert text is not None
    assert text.strip()


def test_generate_agentic_uses_author_and_critic(tmp_path) -> None:
    fake_gguf = tmp_path / "unused.gguf"
    fake_gguf.write_bytes(b"x")
    s = _base_settings(
        llm_backend="vllm",
        gguf_path=str(fake_gguf),
        vllm_base_url="http://example/v1",
    )
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = {"choices": [{"message": {"content": "author output"}}]}
    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = {"choices": [{"message": {"content": "critic output"}}]}
    
    mock_client = MagicMock()
    mock_client.post.side_effect = [mock_response_1, mock_response_2]
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None

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

    with patch("app.services.llm_service.httpx.Client", return_value=mock_client):
        svc = LLMService(s)
        out = svc.generate_agentic(w, "context string", "instruction test")

    assert out == "critic output"
