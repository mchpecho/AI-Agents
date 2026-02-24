# LangFlow Lankovačka – MVP LOCAL Demo Stack (Postgres + Chroma + Ollama)

Minimal local (no cloud keys) Docker Compose stack that demonstrates:
- **SQL tool** over **PostgreSQL** with synthetic machine telemetry + alarms
- **RAG tool** over **ChromaDB (HTTP server)** with JSON knowledge base
- **LLM** via **Ollama** (local)

## 0) Prerequisites
- Docker + Docker Compose
- Python 3.10+
- Enough RAM for local LLMs (for the recommended models, ~8GB is usually sufficient)

## 0.1) After git clone
```bash
cd Zadanie_2
cp .env.example .env
```

## 1) Start stack
```bash
docker compose up -d
```

On first startup, the `ollama-init` service automatically runs and downloads the models:
- `qwen2.5:3b-instruct`
- `llama3.2:3b`
- `nomic-embed-text`

Verification:
```bash
docker compose logs ollama-init
docker exec -it lf_ollama ollama list
```

## 2) Pull Ollama models (manual fallback)
If `ollama-init` fails or is skipped, run manually:
```bash
ollama pull qwen2.5:3b-instruct
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

> Default chat model is `qwen2.5:3b-instruct` (configurable via `OLLAMA_MODEL` in `.env`).

## 3) Ingest KB into Chroma
Run on your host (Windows or Linux/macOS):
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r app/ingest/requirements.txt
python app/ingest/ingest_kb_to_chroma.py
```

Quick sanity check of telemetry for the last 2 hours:
```bash
python app/ingest/sanity_check_2h.py --machine-id LNK-01 --hours 2
```

### 3.1) Demo data generator (for alternative environments)
Standalone script for generating CSV data without dependency on `_local_demo_generator`:
```bash
python app/ingest/generate_demo_data.py --output-dir ./demo_data
```

Optional parameters:
```bash
python app/ingest/generate_demo_data.py --output-dir ./demo_data --hours 24 --step-seconds 10 --machine-id LNK-01 --seed 42
```

Output:
- `telemetry.csv` (columns: `ts,machine_id,tag,value,unit`)
- `alarms.csv` (columns: `ts,machine_id,alarm_code,severity,message,state`)

Defaults (override with environment variables if needed):
- CHROMA_HOST=localhost
- CHROMA_PORT=8000
- CHROMA_COLLECTION=kb_lankovacka
- OLLAMA_BASE_URL=http://localhost:11434
- OLLAMA_EMBED_MODEL=nomic-embed-text
- KB_ROOT=kb

Tip: if the ingest fails, ensure the embeddings model is pulled:
```bash
ollama pull nomic-embed-text
```

## 4) Open LangFlow
- UI: http://localhost:7860

### Import flow (best-effort)
In LangFlow:
- **Flows → Import** and select `app/langflow/flow_export.json`
- If import fails (versions differ), follow `app/langflow/setup_notes.md`
  - `app/langflow/flow_export.json` mirrors `app/langflow/versions/flow_export_v1.7.3.json`

Note: This `README.md` is the primary setup source. Documents in `app/langflow/versions/` are supplementary/archival only.

## 5) Demo questions
1. "Summarize the last 2 hours of machine LNK-01 operation: speed, tension, temperatures, and vibrations."
2. "Were alarms E204 or E221 triggered in the last 24 hours? When and how many times?"
3. "Provide the SOP for E204 and verify if the telemetry shows changes in spool RPM or tension at the time of the alarm."
4. "Find the last E221 event and explain possible causes + recommended steps."
5. "Suggest 3 preventive measures that reduce the risk of E204 and E221 (use the KB)."

## 6) Workflow overview
1. Docker Compose starts PostgreSQL, ChromaDB, Ollama, and LangFlow.
2. The ingest script reads JSON files under KB_ROOT, builds embeddings via Ollama,
   and writes documents + metadata into the Chroma collection.
3. LangFlow uses SQL tools to query Postgres and RAG tools to query Chroma.

## 7) Troubleshooting
- Empty agent response: ensure you imported `app/langflow/flow_export.json` (not the empty wrapper) and that Chat Output is connected.
- Empty KB context: ensure an **Ollama Embeddings** component is connected to the Chroma **Embedding** input (model `nomic-embed-text`).
- Ollama model missing: run `ollama pull qwen2.5:3b-instruct`, `ollama pull llama3.2:3b`, and `ollama pull nomic-embed-text`.
- Flow returns only tool calls/JSON: in the Agent node, disable `Enable Structured Output`, leave the schema empty, and reimport the flow.
- Flow returns repeated tool calls (`run`, `get_last_event`) or stale timestamps: create a new chat/session in LangFlow, reimport the flow, and set `n_messages` to a low value (e.g., 5).
- Flow returns response in wrong language or generic text like "Based on the tool response": reimport `app/langflow/flow_export.json`, create a new chat/session, and verify that the Agent `system_prompt` contains the rule "always answer in English".

## 8) Notes
- Time is generated as **UTC** for the last 24 hours.
- The telemetry tag list in the course prompt contains **11 items** even though it says "10 tags".
  This demo uses the **exact list as written** to avoid dropping any required signal.

## 9) Stop / wipe
```bash
docker compose down
# wipe persisted data
rm -rf .data
```
