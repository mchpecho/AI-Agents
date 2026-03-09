import atexit
import json
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Literal

from tavily import TavilyClient

logger = logging.getLogger(__name__)

WebBackendMode = Literal["native", "mcp", "auto"]


def _vendor_adjusted_query(query: str, vendor: str | None = None) -> str:
    if not vendor:
        return query
    if vendor.lower() == "siemens":
        return f"{query} site:siemens.com OR site:mall.industry.siemens.com"
    return f"{query} {vendor}"


class NativeTavilyTool:
    def __init__(self, max_results: int = 5) -> None:
        self.max_results = max_results
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Missing TAVILY_API_KEY environment variable for Tavily native search.")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, vendor: str | None = None) -> list[dict[str, Any]]:
        final_query = _vendor_adjusted_query(query, vendor)
        response = self.client.search(
            query=final_query,
            max_results=self.max_results,
            include_raw_content=False,
        )
        rows = response.get("results", [])
        normalized = [
            {
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("content", ""),
            }
            for row in rows
        ]
        logger.info("[WEB] Native query='%s' vendor='%s' -> %d results", query, vendor or "", len(normalized))
        return normalized


class MCPTavilyTool:
    def __init__(self, server_path: str, max_results: int = 5) -> None:
        self.max_results = max_results
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

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        if self._proc.poll() is not None:
            raise RuntimeError("MCP Tavily server process is not running.")

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
            raise RuntimeError("Empty response from MCP Tavily server.")

        response = json.loads(line)
        if not response.get("ok"):
            raise RuntimeError(response.get("error", "Unknown MCP Tavily error"))
        return response["result"]

    def search(self, query: str, vendor: str | None = None) -> list[dict[str, Any]]:
        final_query = _vendor_adjusted_query(query, vendor)
        result = self._request("search", {"query": final_query, "max_results": self.max_results})
        rows = result if isinstance(result, list) else []
        logger.info("[WEB] MCP query='%s' vendor='%s' -> %d results", query, vendor or "", len(rows))
        return rows


class WebSearchTool:
    def __init__(
        self,
        backend_mode: WebBackendMode,
        mcp_server_path: str,
        max_results: int = 5,
        runtime_fallback: bool = True,
    ) -> None:
        self.backend_mode = backend_mode
        self.runtime_fallback = runtime_fallback
        self.native_backend: NativeTavilyTool | None = None
        self.mcp_backend: MCPTavilyTool | None = None
        self.active_backend: Literal["native", "mcp"]

        if backend_mode == "native":
            self.native_backend = NativeTavilyTool(max_results=max_results)
            self.active_backend = "native"
            logger.info("[WEB] Mode=native")
            return

        if backend_mode == "mcp":
            self.mcp_backend = MCPTavilyTool(server_path=mcp_server_path, max_results=max_results)
            self.active_backend = "mcp"
            logger.info("[WEB] Mode=mcp")
            return

        # auto
        try:
            self.mcp_backend = MCPTavilyTool(server_path=mcp_server_path, max_results=max_results)
            self.active_backend = "mcp"
            logger.info("[WEB] Mode=auto -> using mcp")
        except Exception as exc:
            logger.warning("[WEB] Mode=auto -> MCP unavailable (%s), falling back to native", exc)
            self.native_backend = NativeTavilyTool(max_results=max_results)
            self.active_backend = "native"

    def _run_with_active_backend(self, query: str, vendor: str | None = None) -> list[dict[str, Any]]:
        if self.active_backend == "mcp":
            assert self.mcp_backend is not None
            return self.mcp_backend.search(query, vendor=vendor)

        assert self.native_backend is not None
        return self.native_backend.search(query, vendor=vendor)

    def _ensure_native_backend(self) -> None:
        if self.native_backend is None:
            max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
            self.native_backend = NativeTavilyTool(max_results=max_results)

    def search(self, query: str, vendor: str | None = None) -> list[dict[str, Any]]:
        try:
            result = self._run_with_active_backend(query, vendor=vendor)
            if result:
                result[0]["web_backend"] = self.active_backend
            return result
        except Exception as exc:
            can_fallback = self.runtime_fallback and self.active_backend == "mcp"
            if not can_fallback:
                raise

            logger.warning("[WEB] Runtime MCP failure (%s), switching to native fallback", exc)
            self._ensure_native_backend()
            self.active_backend = "native"
            result = self._run_with_active_backend(query, vendor=vendor)
            if result:
                result[0]["web_backend"] = self.active_backend
                result[0]["fallback_reason"] = str(exc)
            return result

