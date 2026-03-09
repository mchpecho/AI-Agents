import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import chromadb
import requests
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class LongTermMemoryTool:
    def __init__(
        self,
        chroma_host: str,
        chroma_port: int,
        ollama_base_url: str,
        embed_model: str,
        collection_name: str = "long_term_memory",
    ) -> None:
        self.ollama_base_url = ollama_base_url
        self.embed_model = embed_model
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.ollama_base_url.rstrip('/')}/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["embedding"]

    def save_memory(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        memory_id = str(uuid.uuid4())
        meta = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "agent",
        }
        if metadata:
            meta.update(metadata)

        embedding = self._embed(text)
        self.collection.add(
            ids=[memory_id],
            documents=[text],
            metadatas=[meta],
            embeddings=[embedding],
        )
        logger.info("[MEMORY] Stored memory id=%s metadata=%s", memory_id, json.dumps(meta))
        return memory_id

    def search_memories(self, query: str, n_results: int = 4) -> list[dict[str, Any]]:
        embedding = self._embed(query)
        res = self.collection.query(query_embeddings=[embedding], n_results=n_results)

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0]

        memories: list[dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            memories.append(
                {
                    "text": doc,
                    "metadata": metas[idx] if idx < len(metas) else {},
                    "distance": distances[idx] if idx < len(distances) else None,
                }
            )
        logger.info("[MEMORY] Retrieved %d memories for query='%s'", len(memories), query)
        return memories

