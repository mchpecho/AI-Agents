import json
import logging
import os
import re
import sys
from typing import Any

import psycopg

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [MCP-POSTGRES] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

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

    # Reject statement chaining and SQL comments that can hide write operations.
    if ";" in stripped.rstrip(";") or "--" in stripped or "/*" in stripped or "*/" in stripped:
        return False

    normalized = stripped.lower().strip(";")
    if not normalized.startswith(READ_ONLY_PREFIXES):
        return False
    for kw in BLOCKED_SQL_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", normalized):
            return False
    return True


class PostgresServer:
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

        limited_query = f"SELECT * FROM ({query.rstrip(';')}) AS q LIMIT {int(limit)}"
        with self.conn.cursor() as cur:
            cur.execute(limited_query)
            rows = cur.fetchall()
            columns = [c.name for c in cur.description]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}


def write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True) + "\n")
    sys.stdout.flush()


def main() -> None:
    server = PostgresServer()
    logger.info("Postgres MCP server started.")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request: dict[str, Any] | None = None
        try:
            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "ping":
                write_response({"id": req_id, "ok": True, "result": "pong"})
                continue

            if method == "run_select":
                result = server.run_select(
                    query=str(params.get("query", "")),
                    limit=int(params.get("limit", 100)),
                )
                write_response({"id": req_id, "ok": True, "result": result})
                continue

            write_response({"id": req_id, "ok": False, "error": f"Unknown method: {method}"})
        except Exception as exc:
            logger.exception("Request handling failed")
            write_response({"id": request.get("id") if request else None, "ok": False, "error": str(exc)})


if __name__ == "__main__":
    main()

