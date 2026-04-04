# Literary World Generator

FastAPI service for literary world-building: create worlds (title, tone, era notes, optional seed), list and fetch them, and call stub generators for glossary and timeline hints. Data is stored in memory until you add persistence.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

```bash
uv sync
```

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

- `app/main.py` — FastAPI app and router mounting
- `app/api/routes/` — HTTP routes (`health`, `worlds`)
- `app/schemas/` — Pydantic models
- `app/services/` — In-memory world storage and stub generation
