import json
import logging
import os
import sys
from typing import Any

from tavily import TavilyClient

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [MCP-TAVILY] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class TavilyServer:
    def __init__(self) -> None:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Missing TAVILY_API_KEY environment variable.")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        response = self.client.search(
            query=query,
            max_results=max_results,
            include_raw_content=False,
        )
        rows = response.get("results", [])
        return [
            {
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("content", ""),
            }
            for row in rows
        ]


def write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True) + "\n")
    sys.stdout.flush()


def main() -> None:
    server = TavilyServer()
    logger.info("Tavily MCP server started.")

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

            if method == "search":
                result = server.search(
                    query=str(params.get("query", "")),
                    max_results=int(params.get("max_results", 5)),
                )
                write_response({"id": req_id, "ok": True, "result": result})
                continue

            write_response({"id": req_id, "ok": False, "error": f"Unknown method: {method}"})
        except Exception as exc:
            logger.exception("Request handling failed")
            write_response({"id": request.get("id") if request else None, "ok": False, "error": str(exc)})


if __name__ == "__main__":
    main()

