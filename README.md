# Literary World Generator

A full-stack application and API service for literary world-building. Create worlds (title, tone, era notes, optional seed), explore them through a web UI, and dynamically generate lore (glossary, timeline hints, entities) using an advanced agentic multi-model pipeline featuring Author and Critic models, with RAG-based consistency backed by a Neo4j graph database.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Docker](https://www.docker.com/) (for Neo4j Graph Database)
- [Node.js](https://nodejs.org/) & npm (for the web frontend)

## Setup

### Backend (FastAPI)

```bash
uv sync
```

For **local GGUF inference** (llama.cpp via `llama-cpp-python`), also install the optional extra:

```bash
uv sync --extra local-llm
```

### Graph Database (Neo4j)

A Neo4j container provides persistence and graph-based data retrieval across the world properties. Start it via Docker:

```bash
docker-compose up -d
```

### Frontend

To configure the modern web-based UI:

```bash
cd frontend
npm install
```

## Running the Application

### 1. Database
Make sure Neo4j is running in the background:
```bash
docker-compose up -d
```

### 2. Backend API
Preferred (reload on code changes):

```bash
uv run uvicorn app.main:app --reload
```

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Frontend UI
In a new terminal:
```bash
cd frontend
npm run dev
```

Visit the app in your browser at the specified local port (e.g., `http://localhost:5173`).

---

## Local LLM Integration (llama.cpp or vLLM)

- **llama.cpp (GGUF, low resource):** To use local model files, create a symlink or configure `WORLD_GENERATOR_GGUF_PATH` to point to the desired model weights (e.g. Qwen, Llama3). Tune CPU/GPU with `WORLD_GENERATOR_LLAMA_N_GPU_LAYERS` (default `0` = CPU only).
- **vLLM:** Run a vLLM OpenAI-compatible server, then set `WORLD_GENERATOR_VLLM_BASE_URL` (e.g. `http://127.0.0.1:8000/v1`) and `WORLD_GENERATOR_VLLM_MODEL` to the served model id. If no GGUF path is set, `auto` selects vLLM.

Other useful variables: `WORLD_GENERATOR_LLM_BACKEND` (`auto` | `none` | `llama` | `vllm`), `WORLD_GENERATOR_LLM_MAX_TOKENS`, `WORLD_GENERATOR_VLLM_API_KEY` (optional).

`GET /health` includes `llm.mode` (`none` | `llama` | `vllm`) and `llm.enabled`. When an LLM is enabled, `POST /worlds/{id}/generate` uses an agentic system containing **Author** and **Critic** capabilities in conjunction with the graph DB to orchestrate contextually aware generations.

## Example API Requests

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

List worlds:

```bash
curl -s http://127.0.0.1:8000/worlds
```

Agentic generation (e.g. glossary):

```bash
curl -s -X POST http://127.0.0.1:8000/worlds/WORLD_ID/generate \
  -H "Content-Type: application/json" \
  -d '{"section": "glossary"}'
```

## Project Layout

- `models/` — Directory for GGUF model paths/symlinks
- `app/main.py` — FastAPI app and router mounting
- `app/api/` — API Routes (`health`, `worlds`)
- `app/schemas/` — Pydantic models for Worlds, Properties, and Agentic Data
- `app/services/` — LLM (`llm_service.py`) and Graph DB integration (`world_service.py`) with Author/Critic generation flows
- `docker-compose.yml` — Container definitions for the persistence layer
- `frontend/` — The web-based React graphical user interface
- `tests/` — Pytest suite covering endpoints, LLM parsing, and graph-DB connectivity
