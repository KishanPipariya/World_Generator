# Literary World Generator

Literary World Generator is a FastAPI and React application for managing a
graph-first fiction world bible. It lets writers create worlds, save canon
entities and relationships, plan timelines, review generated lore, check draft
passages against canon, read a wiki-first canon view, and export world material
for writing tools. The default frontend world experience is the reader at
`/wiki/:worldId`; the editable canon workbench remains available at
`/worlds/:id`.

For longer-term product direction, see
[docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md).

## Current Features

- World CRUD with title, tone, era notes, and seed metadata.
- Wiki-first reader for browsing world overviews, canon entities,
  relationships, timelines, and visible lore notes.
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
- Optional LLM support through OpenRouter. When no OpenRouter credentials and
  model are configured, generation endpoints return deterministic stubs so the
  app remains usable.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm, for the React frontend

## Setup

Install backend dependencies:

```bash
uv sync
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

SQLite is used by default and initialized automatically at
`./data/world_generator.sqlite3`. Override the path with:

```text
WORLD_GENERATOR_SQLITE_PATH=./data/world_generator.sqlite3
```

Authentication uses open signup by default. Configure these before deploying:

```text
WORLD_GENERATOR_JWT_SECRET=<strong random secret>
WORLD_GENERATOR_JWT_EXPIRES_MINUTES=1440
WORLD_GENERATOR_ALLOW_SIGNUP=true
```

Set `WORLD_GENERATOR_ALLOW_SIGNUP=false` after provisioning users if public
signup should be closed.

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

After login, the dashboard, recent world links, world cards, demo creation, and
new world creation open the wiki reader by default. Use the Workbench/Edit Canon
links for canon maintenance, drafts, planning, graph views, and exports.

## LLM Configuration

LLM use is optional. The app supports OpenRouter or disabled mode through
`WORLD_GENERATOR_LLM_BACKEND`. OpenRouter calls are made through the OpenAI
Python SDK using OpenRouter's OpenAI-compatible `base_url`.

- `openrouter`: use the OpenRouter chat completions API when both an API key and
  model are configured. This is the default.
- `none`: disable LLM calls.

Useful variables:

```text
WORLD_GENERATOR_LLM_BACKEND=openrouter
WORLD_GENERATOR_OPENROUTER_API_KEY=sk-or-...
WORLD_GENERATOR_OPENROUTER_MODEL=deepseek/deepseek-v4-flash:free
WORLD_GENERATOR_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
WORLD_GENERATOR_OPENROUTER_HTTP_REFERER=https://your-app.example
WORLD_GENERATOR_OPENROUTER_APP_TITLE=Literary World Generator
WORLD_GENERATOR_LLM_MAX_TOKENS=768
WORLD_GENERATOR_LLM_TEMPERATURE=0.65
```

`WORLD_GENERATOR_OPENROUTER_BASE_URL` should normally stay at
`https://openrouter.ai/api/v1`; it is passed to `OpenAI(base_url=...)`.
`WORLD_GENERATOR_OPENROUTER_HTTP_REFERER` and
`WORLD_GENERATOR_OPENROUTER_APP_TITLE` are optional OpenRouter attribution
headers sent with each chat completion request.

`GET /api/v1/health` only reports public service status. LLM mode details are
not exposed publicly.

## API Examples

Health:

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

Register and login:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"writer","email":"writer@example.com","password":"replace-me-strongly"}'

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"writer","password":"replace-me-strongly"}' | jq -r .access_token)
```

Create a world:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "The Ember Archipelago", "tone": "mythic intrigue"}'
```

Create an entity:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/entities \
  -H "Authorization: Bearer $TOKEN" \
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
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"passage": "Mara entered Ithoros before the bells cracked."}'
```

Save a draft passage:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/drafts \
  -H "Authorization: Bearer $TOKEN" \
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
curl -s -X POST http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/drafts/DRAFT_ID/check \
  -H "Authorization: Bearer $TOKEN"
```

Export Markdown:

```bash
curl -s "http://127.0.0.1:8000/api/v1/worlds/WORLD_ID/export/markdown?preset=full_bible" \
  -H "Authorization: Bearer $TOKEN"
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

## Git Hooks

This repo includes Git hooks in `.githooks/`. Enable them for your checkout:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs backend and frontend linting. The pre-push hook runs
backend tests and the full frontend check. For urgent one-off bypasses, prefix
the Git command with `SKIP_HOOKS=1`.

## Project Layout

- `app/main.py` - FastAPI application and router setup.
- `app/api/routes/` - API routes for health checks and world resources.
- `app/schemas/world.py` - Pydantic request and response models.
- `app/services/world_service.py` - SQLite-backed world, canon, planning, draft,
  export, and consistency logic.
- `app/services/llm_service.py` - Optional OpenRouter integration using the
  OpenAI Python SDK.
- `frontend/` - React and Vite frontend.
  - `/wiki/:worldId` is the primary world reader route.
  - `/worlds/:id` is the editable canon workbench route.
  - `/worlds/:id/dm` is the DM workflow route.
- `tests/` - Pytest coverage for API, service, DB, and LLM behavior.
