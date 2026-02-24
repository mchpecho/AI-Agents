import os
import json
import glob
import time
import requests
import chromadb
from chromadb.config import Settings

def ollama_embed(base_url: str, model: str, text: str) -> list[float]:
    # Ollama embeddings endpoint
    r = requests.post(
        f"{base_url.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "embedding" not in data:
        raise RuntimeError(f"Unexpected Ollama embeddings response keys: {list(data.keys())}")
    return data["embedding"]

def build_doc_text(obj: dict) -> str:
    # Keep it simple: concatenate key fields
    parts = []
    for k in ["title", "summary", "body", "steps", "tags", "alarm_codes", "thresholds"]:
        if k in obj and obj[k] is not None:
            parts.append(f"{k}: {json.dumps(obj[k], ensure_ascii=False)}")
    # fallback: whole json
    if not parts:
        parts.append(json.dumps(obj, ensure_ascii=False))
    return "\n".join(parts)

def main():
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    collection_name = os.getenv("CHROMA_COLLECTION", "kb_lankovacka")

    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    kb_root = os.getenv("KB_ROOT", "kb")

    # Connect to Chroma server (HTTP)
    client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port,
        settings=Settings(anonymized_telemetry=False),
    )

    # Recreate collection for deterministic demos
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    files = sorted(glob.glob(os.path.join(kb_root, "**", "*.json"), recursive=True))
    if not files:
        raise SystemExit(f"No KB JSON files found under: {kb_root}")

    ids, docs, metas, embeds = [], [], [], []

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            obj = json.load(f)

        doc_text = build_doc_text(obj)
        meta = {
            "source_path": fp.replace("\\", "/"),
            "type": obj.get("type", "kb"),
            "alarm_codes": ",".join(obj.get("alarm_codes", [])) if isinstance(obj.get("alarm_codes"), list) else str(obj.get("alarm_codes", "")),
            "related_tags": ",".join(obj.get("related_tags", [])) if isinstance(obj.get("related_tags"), list) else str(obj.get("related_tags", "")),
        }
        # Provide stable id
        doc_id = os.path.relpath(fp, kb_root).replace("\\", "/")

        emb = ollama_embed(ollama_base, embed_model, doc_text)

        ids.append(doc_id)
        docs.append(doc_text)
        metas.append(meta)
        embeds.append(emb)

    collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)

    print(f"[OK] Ingested {len(ids)} KB docs into Chroma collection '{collection_name}' on {chroma_host}:{chroma_port}")
    # Simple sanity query
    q = "čo robiť pri poruche drôtu"
    q_emb = ollama_embed(ollama_base, embed_model, q)
    res = collection.query(query_embeddings=[q_emb], n_results=min(3, len(ids)))
    top_ids = res.get("ids", [[]])[0]
    print(f"[Sanity] Query='{q}' -> top ids: {top_ids}")

if __name__ == "__main__":
    main()
