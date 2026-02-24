# LangFlow wiring (manual setup) – minimal agent

This is written to be robust across LangFlow versions.

## Goal
Agent that:
- queries Postgres telemetry + alarms with **SQL tool**
- retrieves Slovak KB snippets from **ChromaDB HTTP**
- uses **Ollama** LLM (no cloud keys)
- answers in Slovak with a structured template

## Required environment (already in docker-compose.yml)
- POSTGRES_HOST=postgres
- POSTGRES_PORT=5432
- POSTGRES_DB=lankovacka
- POSTGRES_USER=langflow
- POSTGRES_PASSWORD=langflow
- CHROMA_HOST=chromadb
- CHROMA_PORT=8000
- CHROMA_COLLECTION=kb_lankovacka
- OLLAMA_BASE_URL=http://ollama:11434
- OLLAMA_MODEL=qwen2.5:7b-instruct

## Components (names may vary slightly by LangFlow version)
1) **Chat Model → Ollama**
   - Base URL: `${OLLAMA_BASE_URL}`
   - Model: `${OLLAMA_MODEL}`
   - Temperature: 0.2 (optional)
   - (If there's a "JSON mode" option, leave OFF.)

2) **SQL Database / SQL Tool**
   - Connection string (SQLAlchemy):
     `postgresql+psycopg2://langflow:langflow@postgres:5432/lankovacka`
   - Expose as a Tool to the Agent.
   - IMPORTANT: set any “read-only” toggle if present.

3) **Ollama Embeddings**
  - Base URL: `${OLLAMA_BASE_URL}`
  - Model: `nomic-embed-text`
  - Connect output to Chroma **Embedding** input

4) **Chroma Retriever**
   - If there is a **Chroma (Server/HTTP)** component:
     - Host: `chromadb`
     - Port: `8000`
     - Collection: `kb_lankovacka`
   - Configure it as a Retriever Tool.
   - Search k=3 (or 4).

   If your LangFlow build only supports local Chroma:
   - Use a **Generic HTTP Retriever** (if available) or
   - Run the flow manually in Python. (This MVP keeps ingestion via HTTP server.)

5) **Prompt**
   - System prompt: `app/langflow/prompts/system_prompt_sk.txt`
   - Include user question
   - Include retriever results (context)
   - Include the answer template (answer_template_sk.md)
   - Keep tool instructions in the system prompt.

6) **Agent**
   - Use a tool-calling agent (ReAct-style / Tool Agent / OpenAI Functions style—whatever is available).
   - Tools attached:
     - SQL tool
     - Retriever tool
   - Output: final answer in Slovak using the template.

## Suggested SQL snippets (copy/paste)
**Telemetry (last 2 hours)**
```sql
SELECT ts, tag, value, unit
FROM telemetry
WHERE machine_id = 'LNK-01'
  AND ts >= (now() at time zone 'utc') - interval '2 hours'
ORDER BY ts DESC
LIMIT 2000;
```

**Alarms (last 24 hours)**
```sql
SELECT ts, alarm_code, severity, message, state
FROM alarms
WHERE machine_id = 'LNK-01'
  AND ts >= (now() at time zone 'utc') - interval '24 hours'
ORDER BY ts DESC
LIMIT 200;
```

## flow_export.json
Included as **best-effort** (LangFlow versions differ). If import fails, use this document.

For organized multi-version management, see `versions/` directory:
- `versions/flow_export_v1.7.3.json` ← **Recommended for LangFlow 1.7.3**
- `versions/README.md` ← Version guide and troubleshooting

All components described below are configured in the 1.7.3 export.
