# Literary World Generator

FastAPI service for literary world-building: create worlds (title, tone, era notes, optional seed), list and fetch them, and call stub generators for glossary and timeline hints. Data is stored in memory until you add persistence.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
uv sync
```

For **local GGUF inference** (llama.cpp via `llama-cpp-python`), also install the optional extra:

```bash
uv sync --extra local-llm
```

### Local LLM (llama.cpp or vLLM)

- **llama.cpp (GGUF, low resource):** this repo includes `models/qwen2.5-14b-instruct-q5_k_m.gguf` as a **symlink** to `/Users/kishan/CYOA_TUI/qwen2.5-14b-instruct-q5_k_m.gguf` (stored as `../../CYOA_TUI/...` relative to `models/`). If that target exists, `WORLD_GENERATOR_GGUF_PATH` defaults to this path (no env needed). Override with `WORLD_GENERATOR_GGUF_PATH` if you use another file. With `WORLD_GENERATOR_LLM_BACKEND=auto` (default), the API uses GGUF when the resolved path exists. Tune CPU/GPU with `WORLD_GENERATOR_LLAMA_N_GPU_LAYERS` (default `0` = CPU only).
- **vLLM:** run a vLLM OpenAI-compatible server, then set `WORLD_GENERATOR_VLLM_BASE_URL` (e.g. `http://127.0.0.1:8000/v1`) and `WORLD_GENERATOR_VLLM_MODEL` to the served model id. If no GGUF path is set, `auto` selects vLLM.

Other useful variables: `WORLD_GENERATOR_LLM_BACKEND` (`auto` \| `none` \| `llama` \| `vllm`), `WORLD_GENERATOR_LLM_MAX_TOKENS`, `WORLD_GENERATOR_VLLM_API_KEY` (optional).

`GET /health` includes `llm.mode` (`none` \| `llama` \| `vllm`) and `llm.enabled`. When an LLM is enabled, `POST /worlds/{id}/generate` uses it for glossary and timeline sections; otherwise the previous stubs are returned.

## Run the API

Preferred (reload on code changes):

```bash
uv run uvicorn app.main:app --reload
```

Or:

```bash
uv run python main.py
```

- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Example requests

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

Create a world:

```bash
curl -s -X POST http://127.0.0.1:8000/worlds \
  -H "Content-Type: application/json" \
  -d '{"title": "The Northern Reach","tone": "lyrical melancholy","era_notes": "Decades after the last trade fleet.","seed": "salt-1842"}'
```

List worlds:

```bash
curl -s http://127.0.0.1:8000/worlds
```

Fetch one world (replace `WORLD_ID` with the `id` from create or list):

```bash
curl -s http://127.0.0.1:8000/worlds/WORLD_ID
```

Stub generate (default section is `glossary`):

```bash
curl -s -X POST http://127.0.0.1:8000/worlds/WORLD_ID/generate \
  -H "Content-Type: application/json" \
  -d '{}'
```

Timeline hint stub:

```bash
curl -s -X POST http://127.0.0.1:8000/worlds/WORLD_ID/generate \
  -H "Content-Type: application/json" \
  -d '{"section": "timeline_hint"}'
```

## Project layout

- `models/qwen2.5-14b-instruct-q5_k_m.gguf` — symlink to the GGUF in `CYOA_TUI` (see Local LLM above)
- `app/main.py` — FastAPI app and router mounting
- `app/api/routes/` — HTTP routes (`health`, `worlds`)
- `app/schemas/` — Pydantic models
- `app/services/` — In-memory world storage and stub generation
