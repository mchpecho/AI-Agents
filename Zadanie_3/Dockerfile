FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/Zadanie_3

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY Zadanie_3/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY Zadanie_3 ./

ENV OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=qwen2.5:7b-instruct \
    OLLAMA_TEMPERATURE=0.1 \
    CHROMA_HOST=chromadb \
    CHROMA_PORT=8000 \
    CHROMA_COLLECTION=kb_lankovacka \
    SQL_BACKEND_MODE=auto \
    SQL_RUNTIME_FALLBACK=true \
    WEB_BACKEND_MODE=auto \
    WEB_RUNTIME_FALLBACK=true \
    WEB_SEARCH_MAX_RESULTS=5

EXPOSE 8001

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8001"]

