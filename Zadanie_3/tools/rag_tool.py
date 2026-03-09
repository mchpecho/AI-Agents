import logging
from typing import Any

import chromadb
import requests
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class RAGTool:
    def __init__(
        self,
        chroma_host: str,
        chroma_port: int,
        collection_name: str,
        ollama_base_url: str,
        embed_model: str,
    ) -> None:
        self.ollama_base_url = ollama_base_url
        self.embed_model = embed_model
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_collection(name=collection_name)

    def _embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.ollama_base_url.rstrip('/')}/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["embedding"]

    def search(self, query: str, n_results: int = 3) -> list[dict[str, Any]]:
        query_embedding = self._embed(query)
        results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches: list[dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            matches.append(
                {
                    "document": doc,
                    "metadata": metas[idx] if idx < len(metas) else {},
                    "distance": distances[idx] if idx < len(distances) else None,
                }
            )
        logger.info("[RAG] Query='%s' returned %d docs", query, len(matches))
        return matches

