# Task 3 - LangGraph Plan-Execute Agent

Standalone Python agent built with LangGraph that answers user questions using local tools:
- SQL over PostgreSQL (`telemetry`, `alarms`)
- RAG over Chroma collection `kb_lankovacka`
- Long-term memory in Chroma collection `long_term_memory`
- Web search for external product/component information (for example Siemens)
- Optional MCP backends for SQL and Tavily search

## Architecture
This project uses a Plan-Execute workflow:
1. `load_memory` - retrieves relevant long-term memories.
2. `planner` - creates a short plan and selects tools (`sql_query`, `rag_search`, `memory_search`, `memory_write`, `web_search`).
3. `execute` - runs each plan step using the selected tool.
4. `respond` - composes the final user answer from tool outputs.
5. `persist_memory` - stores useful facts/preferences for future turns.

## Project Structure
- `main.py` - interactive CLI loop.
- `graph.py` - LangGraph state and workflow definition.
- `tools/sql_tool.py` - SQL planning/execution with `native|mcp|auto` modes.
- `tools/rag_tool.py` - Chroma retrieval over local KB.
- `tools/memory_tool.py` - long-term memory storage/retrieval.
- `tools/search_tool.py` - Tavily web search with `native|mcp|auto` modes.
- `mcp_server/mcp_postgres_server.py` - Postgres MCP server.
- `mcp_server/mcp_tavily_server.py` - Tavily MCP server.
- `mcp_server/mcp_sql_server.py` - legacy alias that forwards to Postgres MCP server.
- `.env.example` - environment variables.
- `requirements.txt` - Python dependencies.

## Relationship to Zadanie 2

This agent is a **LangGraph-based replacement/extension** of the LangFlow setup from `Zadanie_2`:
- Reuses the same **PostgreSQL** telemetry/alarms DB.
- Reuses the same **Chroma** KB (`kb_lankovacka`).
- Reuses the same **Ollama** LLM (`qwen2.5:7b-instruct`) and embedding model.
- Adds a **Plan-Execute agent** with:
  - tool-aware planning,
  - long‑term memory,
  - web search via Tavily,
  - its own lightweight web UI.

LangFlow remains available as a reference/demo UI, but for this task the main entrypoint is the **LangGraph agent + web UI**.

## Local End-to-End Setup (CLI or Web)

### 1. Clone repository and move to project root
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Start the local data/LLM stack from `Zadanie_2`
```bash
cd Zadanie_2
cp .env.example .env
docker compose up -d
```

Windows PowerShell:
```powershell
Copy-Item .env.example .env
docker compose up -d
```

Quick Docker commands (from `Zadanie_2`):
```bash
# start
docker compose up -d

# verify status
docker compose ps

# optional: inspect model pull/init logs
docker compose logs ollama-init

# stop
docker compose down
```

### 3. Ensure KB is ingested into Chroma
Run from `Zadanie_2`:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r app/ingest/requirements.txt
python app/ingest/ingest_kb_to_chroma.py
```

### 4. Configure and run this agent (`Zadanie_3`)
```bash
cd ../Zadanie_3
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
```

Set at least:
- `TAVILY_API_KEY` (required for `web_search`)
- optionally: `SQL_BACKEND_MODE=auto`, `WEB_BACKEND_MODE=auto`

Then run **either**:

CLI mode:
```bash
python main.py
```

or the **local web API + UI**:

```bash
python web_app.py
```

When running `main.py` or `web_app.py` directly from `Zadanie_3`, the app now auto-checks local dependency ports (`5432`, `8000`, `11434`).
If dependencies are missing, it automatically runs Docker Compose from `../Zadanie_2/docker-compose.yml` and starts:
- `postgres`
- `chromadb`
- `ollama`
- `ollama-init`

Optional bootstrap controls:
- `AUTO_BOOTSTRAP_Z2_STACK=true|false` (default `true`)
- `BOOTSTRAP_WAIT_SECONDS` (default `120`)

The web app exposes:
- API: `POST /chat` with JSON body `{"message": "<your question>"}`.
- Health check: `GET /health`.
- Static UI: `GET /static/index.html` (chat UI with predefined buttons).

You can open `http://localhost:8001/static/index.html` in your browser and chat with the agent without using the CLI.

## Docker Deployment (integrated with Zadanie 2 stack)

The recommended way to run this agent in the course stack is via **Docker Compose** from `Zadanie_2`:

1. In `Zadanie_2/.env` ensure you have:
   - DB/LLM/Chroma variables (already present from Zadanie 2)
   - `TAVILY_API_KEY=...`
   - optional tuning:
     - `SQL_BACKEND_MODE=auto`
     - `SQL_RUNTIME_FALLBACK=true`
     - `WEB_BACKEND_MODE=auto`
     - `WEB_RUNTIME_FALLBACK=true`
     - `WEB_SEARCH_MAX_RESULTS=5`
2. From `Zadanie_2` run:
   ```bash
   docker compose up -d --build
   ```
3. After all services are healthy you should see:
   - `lf_postgres` (PostgreSQL)
   - `lf_chromadb` (Chroma)
   - `lf_ollama` (Ollama)
   - `lf_plan_execute_agent` (this LangGraph agent)
4. Open the agent UI:
   - `http://localhost:8001/static/index.html`
5. Optional: LangFlow UI from Zadanie 2 is still available at:
   - `http://localhost:7860`

## Backend Modes and Fallback

### SQL backend
Controlled by `SQL_BACKEND_MODE`:
- `native` -> direct `psycopg`
- `mcp` -> `mcp_server/mcp_postgres_server.py`
- `auto` -> prefer MCP, fallback to native

Runtime fallback is controlled by `SQL_RUNTIME_FALLBACK=true|false`.

### Web backend (Tavily)
Controlled by `WEB_BACKEND_MODE`:
- `native` -> direct Tavily API (`tavily-python`)
- `mcp` -> `mcp_server/mcp_tavily_server.py`
- `auto` -> prefer MCP, fallback to native

Runtime fallback is controlled by `WEB_RUNTIME_FALLBACK=true|false`.

## Web Search Notes
- `web_search` is intended for external vendor/product questions, datasheets, and compatibility checks.
- Example: `Find technical information about Siemens component 6SL3210 and summarize compatibility.`
- Required settings in `.env`:
	- `WEB_SEARCH_MAX_RESULTS`
	- `TAVILY_API_KEY` (required)

## Observability
Console logs include:
- planner output (generated plan)
- tool selected per step
- tool result or error per step
- trace lines for each workflow node (`load_memory`, `planner`, `execute`, `respond`, `persist_memory`)

Optional LangSmith tracing:
- set `LANGSMITH_TRACING=true`
- set `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` (and optional endpoint)

## Suggested Test Questions
1. `What was the average machine temperature for LNK-01 in the last 8 hours?`
2. `What does the SOP say about alarm E204?`
3. `What does the SOP say about alarm E221?`
4. `Was alarm E204 associated with a change in spindle speed? If yes, when was it last observed?`
5. `Remember that I prefer concise answers.`
6. `What did I tell you about my preferences?`
 7. `Find technical information about Siemens component 6SL3210 and summarize compatibility.`

Expected behavior:
- telemetry/alarm questions use SQL
- SOP/knowledge questions use RAG
- explicit memory requests are stored in `long_term_memory`
- preference recall uses stored memory
- external vendor/product questions can use `web_search`

## Assignment Coverage
- Framework: `LangGraph`
- Agent type: `Plan-Execute`
- Tools: SQL, vector RAG, long-term memory, web search
- LLM answers are grounded in tool outputs
- MCP: optional Postgres MCP + Tavily MCP with switchable modes and fallback
- Submission: source code is ready; final delivery should include GitHub repository link

