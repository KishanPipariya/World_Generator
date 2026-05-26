# Literary World Generator

Literary World Generator is a FastAPI and React application for managing a
graph-first fiction world bible. It lets writers create worlds, save canon
entities and relationships, plan timelines, review generated lore, check draft
passages against canon, and export world material for writing tools.

For longer-term product direction, see
[docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md).

## Current Features

- World CRUD with title, tone, era notes, and seed metadata.
- Entity CRUD with structured fields for searchable canon details.
- Relationship CRUD with category, stance, strength, history, color, and display
  priority metadata.
- Canon consistency reports for duplicate names, thin lore, orphaned entities,
  weak relationships, possible contradictions, and timeline gaps.
- Generation suggestion inbox with accept, append, replace, and discard flows.
- Timeline events with ordering, date or era labels, participants, dependencies,
  causes, and consequences.
- Saved graph views with layout mode, filters, camera, and node positions.
- Planning boards and cards linked to entities, relationships, and timeline
  events.
- Revision history for entity description edits and restore flows.
- Saved draft passages/scenes with linked canon and stored passage-check history.
- Markdown exports for full world bibles, dossiers, briefs, gazetteers, timelines,
  and Obsidian-style output.
- Optional local LLM support through llama.cpp GGUF models or a vLLM
  OpenAI-compatible server. When no LLM is configured, generation endpoints return
  deterministic stubs so the app remains usable.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker, for Neo4j
- Node.js and npm, for the React frontend

## Setup

Install backend dependencies:

```bash
uv sync
```

Install the optional llama.cpp dependency only if you want local GGUF inference:

```bash
uv sync --extra local-llm
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start Neo4j:

```bash
docker-compose up -d
```

The default database connection is:

- URI: `bolt://localhost:7687`
- User: `neo4j`
- Password: `password`

Override these with `WORLD_GENERATOR_NEO4J_URI`,
`WORLD_GENERATOR_NEO4J_USER`, and `WORLD_GENERATOR_NEO4J_PASSWORD`.

## Running Locally

Start the backend from the repo root:

```bash
uv run uvicorn app.main:app --reload
```

The API docs are available at:

```text
http://127.0.0.1:8000/docs
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Vite will print the local app URL, usually `http://localhost:5173`.

## LLM Configuration

LLM use is optional. The app chooses a backend with
`WORLD_GENERATOR_LLM_BACKEND`:

- `auto`: use a configured GGUF model if present, otherwise use vLLM if
  configured, otherwise disable LLM calls.
- `none`: disable LLM calls.
- `llama`: use llama.cpp through `llama-cpp-python`.
- `vllm`: use an OpenAI-compatible vLLM server.

Useful variables:

```text
WORLD_GENERATOR_GGUF_PATH=/path/to/model.gguf
WORLD_GENERATOR_LLAMA_N_CTX=4096
WORLD_GENERATOR_LLAMA_N_GPU_LAYERS=0
WORLD_GENERATOR_LLM_MAX_TOKENS=768
WORLD_GENERATOR_LLM_TEMPERATURE=0.65

WORLD_GENERATOR_VLLM_BASE_URL=http://127.0.0.1:8000/v1
WORLD_GENERATOR_VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
WORLD_GENERATOR_VLLM_API_KEY=optional-key
```

`GET /api/v1/health` reports the selected LLM mode and whether generation is
enabled.

## API Examples

Health:

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

Create a world:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds \
  -H "Content-Type: application/json" \
  -d '{"title": "The Ember Archipelago", "tone": "mythic intrigue"}'
```

Create an entity:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mara Vey",
    "entity_type": "Character",
    "description": "A lighthouse cartographer chasing falsified sea charts.",
    "structured_fields": {"goal": "Expose the chart forgery"}
  }'
```

Run a passage check:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/passage-check \
  -H "Content-Type: application/json" \
  -d '{"passage": "Mara entered Ithoros before the bells cracked."}'
```

Save a draft passage:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/drafts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Opening Scene",
    "body": "Mara entered Ithoros before the bells cracked.",
    "status": "draft",
    "linked_entity_ids": ["ENTITY_ID"]
  }'
```

Check a saved draft and append the result to its check history:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/drafts/DRAFT_ID/check
```

Export Markdown:

```bash
curl -s "http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/export/markdown?preset=full_bible"
```

Supported export presets are `full_bible`, `character_dossier`,
`faction_brief`, `location_gazetteer`, `timeline_only`, and `obsidian`.

## Development

Run backend tests:

```bash
uv run pytest
```

Run backend lint:

```bash
uv run ruff check
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Project Layout

- `app/main.py` - FastAPI application and router setup.
- `app/api/routes/` - API routes for health checks and world resources.
- `app/schemas/world.py` - Pydantic request and response models.
- `app/services/world_service.py` - Neo4j-backed world, canon, planning, draft,
  export, and consistency logic.
- `app/services/llm_service.py` - Optional llama.cpp and vLLM integration.
- `frontend/` - React and Vite frontend.
- `tests/` - Pytest coverage for API, service, DB, and LLM behavior.
- `docker-compose.yml` - Local Neo4j service.
