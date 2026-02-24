import chromadb
import requests
import os

def ollama_embed(base_url: str, model: str, text: str) -> list[float]:
    r = requests.post(
        f"{base_url.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["embedding"]

client = chromadb.HttpClient(host='localhost', port=8000)
collection = client.get_collection(name='kb_lankovacka')

ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Query using Ollama embeddings (same as ingest)
query_text = 'E204 wire break procedure'
query_embedding = ollama_embed(ollama_base, embed_model, query_text)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=1
)

if results['documents'] and len(results['documents'][0]) > 0:
    doc = results['documents'][0][0]
    print("=" * 80)
    print(doc)
else:
    print('No results found')
