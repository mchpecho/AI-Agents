import logging
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _get_ollama_host() -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    parsed = urlparse(base_url)
    return parsed.hostname or "localhost"


def _should_bootstrap() -> bool:
    enabled = os.getenv("AUTO_BOOTSTRAP_Z2_STACK", "true").lower() == "true"
    if not enabled:
        return False

    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    ollama_host = _get_ollama_host()

    local_hosts = {"localhost", "127.0.0.1"}
    return (
        chroma_host in local_hosts
        and postgres_host in local_hosts
        and ollama_host in local_hosts
    )


def ensure_zadanie2_stack() -> None:
    """Auto-start local Zadanie_2 Docker dependencies used by Zadanie_3."""
    if not _should_bootstrap():
        logger.info("[BOOTSTRAP] Skipped (AUTO_BOOTSTRAP_Z2_STACK disabled or non-local hosts)")
        return

    if (
        _is_port_open("localhost", 5432)
        and _is_port_open("localhost", 8000)
        and _is_port_open("localhost", 11434)
    ):
        logger.info("[BOOTSTRAP] Dependencies already available (5432/8000/11434)")
        return

    if shutil.which("docker") is None:
        logger.warning("[BOOTSTRAP] Docker CLI not found. Cannot auto-start Zadanie_2 stack.")
        return

    z3_dir = Path(__file__).resolve().parent
    z2_dir = z3_dir.parent / "Zadanie_2"
    compose_file = z2_dir / "docker-compose.yml"

    if not compose_file.exists():
        logger.warning("[BOOTSTRAP] Missing compose file: %s", compose_file)
        return

    logger.info("[BOOTSTRAP] Starting Zadanie_2 dependencies via Docker Compose")
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "up",
        "-d",
        "--build",
        "postgres",
        "chromadb",
        "ollama",
        "ollama-init",
    ]

    result = subprocess.run(
        cmd,
        cwd=str(z2_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.error("[BOOTSTRAP] Docker compose failed: %s", result.stderr.strip())
        return

    deadline = time.time() + float(os.getenv("BOOTSTRAP_WAIT_SECONDS", "120"))
    while time.time() < deadline:
        if (
            _is_port_open("localhost", 5432)
            and _is_port_open("localhost", 8000)
            and _is_port_open("localhost", 11434)
        ):
            logger.info("[BOOTSTRAP] Dependencies are ready")
            return
        time.sleep(2)

    logger.warning("[BOOTSTRAP] Timeout waiting for dependencies to become ready")
