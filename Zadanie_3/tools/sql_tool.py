import atexit
import json
import logging
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Any, Literal

import psycopg
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

SQLBackendMode = Literal["native", "mcp", "auto"]

READ_ONLY_PREFIXES = ("select", "with", "explain")
BLOCKED_SQL_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "create",
    "grant",
    "revoke",
)


def is_read_only_sql(query: str) -> bool:
    stripped = query.strip()
    if not stripped:
        return False

    # Reject obvious statement chaining and SQL comments to reduce bypass tricks.
    if ";" in stripped.rstrip(";") or "--" in stripped or "/*" in stripped or "*/" in stripped:
        return False

    normalized = stripped.lower().strip(";")
    if not normalized.startswith(READ_ONLY_PREFIXES):
        return False
    for kw in BLOCKED_SQL_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", normalized):
            return False
    return True


def extract_sql(text: str) -> str:
    if "```sql" in text:
        return text.split("```sql", maxsplit=1)[1].split("```", maxsplit=1)[0].strip()
    if "```" in text:
        return text.split("```", maxsplit=1)[1].split("```", maxsplit=1)[0].strip()
    return text.strip()


class NativeSQLTool:
    def __init__(self) -> None:
        self.conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "lankovacka"),
            user=os.getenv("POSTGRES_USER", "langflow"),
            password=os.getenv("POSTGRES_PASSWORD", "langflow"),
            autocommit=True,
        )

    def run_select(self, query: str, limit: int = 100) -> dict[str, Any]:
        if not is_read_only_sql(query):
            raise ValueError("Only read-only SELECT/WITH/EXPLAIN queries are allowed.")
        normalized = query.strip().lower()
        # EXPLAIN is a top-level statement and cannot be wrapped as a subquery.
        if normalized.startswith("explain"):
            statement = query.rstrip(";")
        else:
            statement = f"SELECT * FROM ({query.rstrip(';')}) AS q LIMIT {int(limit)}"
        with self.conn.cursor() as cur:
            cur.execute(statement)
            rows = cur.fetchall()
            columns = [c.name for c in cur.description]
        result = {"columns": columns, "rows": rows, "row_count": len(rows)}
        logger.info("[SQL] Native query returned %d rows", len(rows))
        return result


class MCPSQLTool:
    def __init__(self, server_path: str) -> None:
        self._counter = 0
        self._lock = threading.Lock()
        self._proc = subprocess.Popen(
            [os.getenv("PYTHON_BIN", "python"), "-u", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(server_path).resolve().parents[1]),
        )
        atexit.register(self.close)

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._proc.poll() is not None:
            raise RuntimeError("MCP Postgres server process is not running.")

        with self._lock:
            self._counter += 1
            req_id = self._counter
            payload = {"id": req_id, "method": method, "params": params}
            assert self._proc.stdin is not None
            assert self._proc.stdout is not None
            self._proc.stdin.write(json.dumps(payload, ensure_ascii=True) + "\n")
            self._proc.stdin.flush()
            line = self._proc.stdout.readline().strip()

        if not line:
            raise RuntimeError("Empty response from MCP Postgres server.")

        response = json.loads(line)
        if not response.get("ok"):
            raise RuntimeError(response.get("error", "Unknown MCP Postgres error"))
        return response["result"]

    def run_select(self, query: str, limit: int = 100) -> dict[str, Any]:
        result = self._request("run_select", {"query": query, "limit": limit})
        logger.info("[SQL] MCP query returned %d rows", result.get("row_count", -1))
        return result


class SQLPlannerExecutor:
    def __init__(
        self,
        llm: BaseChatModel,
        backend_mode: SQLBackendMode,
        mcp_server_path: str,
        runtime_fallback: bool = True,
    ) -> None:
        self.llm = llm
        self.backend_mode = backend_mode
        self.runtime_fallback = runtime_fallback
        self.native_backend: NativeSQLTool | None = None
        self.mcp_backend: MCPSQLTool | None = None
        self.active_backend: Literal["native", "mcp"]

        if backend_mode == "native":
            self.native_backend = NativeSQLTool()
            self.active_backend = "native"
            logger.info("[SQL] Mode=native")
            return

        if backend_mode == "mcp":
            self.mcp_backend = MCPSQLTool(server_path=mcp_server_path)
            self.active_backend = "mcp"
            logger.info("[SQL] Mode=mcp")
            return

        # auto
        try:
            self.mcp_backend = MCPSQLTool(server_path=mcp_server_path)
            self.active_backend = "mcp"
            logger.info("[SQL] Mode=auto -> using mcp")
        except Exception as exc:
            logger.warning("[SQL] Mode=auto -> MCP unavailable (%s), falling back to native", exc)
            self.native_backend = NativeSQLTool()
            self.active_backend = "native"

    def _nl_to_sql(self, instruction: str) -> str:
        if instruction.strip().lower().startswith(("select", "with", "explain")):
            return instruction.strip().rstrip(";")

        prompt = f"""
You generate safe PostgreSQL read-only SQL for this schema:
- telemetry(ts timestamptz, machine_id text, tag text, value double precision, unit text)
- alarms(ts timestamptz, machine_id text, alarm_code text, severity text, message text, state text)

Rules:
- Output SQL only.
- Use SELECT/WITH/EXPLAIN only.
- Never modify data.
- Prefer machine_id='LNK-01' if not explicitly stated.
- For "last X hours", use now() - interval syntax.

Instruction:
{instruction}
""".strip()
        raw = self.llm.invoke(prompt).content
        sql = extract_sql(raw if isinstance(raw, str) else str(raw))
        if not is_read_only_sql(sql):
            raise ValueError(f"Planner produced non read-only SQL: {sql}")
        return sql.rstrip(";")

    def _run_with_active_backend(self, sql: str) -> dict[str, Any]:
        if self.active_backend == "mcp":
            assert self.mcp_backend is not None
            return self.mcp_backend.run_select(sql)

        assert self.native_backend is not None
        return self.native_backend.run_select(sql)

    def _ensure_native_backend(self) -> None:
        if self.native_backend is None:
            self.native_backend = NativeSQLTool()

    def run(self, instruction: str) -> dict[str, Any]:
        sql = self._nl_to_sql(instruction)

        try:
            result = self._run_with_active_backend(sql)
            result["generated_sql"] = sql
            result["sql_backend"] = self.active_backend
            return result
        except Exception as exc:
            can_fallback = self.runtime_fallback and self.active_backend == "mcp"
            if not can_fallback:
                raise

            logger.warning("[SQL] Runtime MCP failure (%s), switching to native fallback", exc)
            self._ensure_native_backend()
            self.active_backend = "native"
            result = self._run_with_active_backend(sql)
            result["generated_sql"] = sql
            result["sql_backend"] = self.active_backend
            result["fallback_reason"] = str(exc)
            return result

