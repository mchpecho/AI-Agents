import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from bootstrap_stack import ensure_zadanie2_stack
from graph import create_agent_graph


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


def _cors_origins_from_env() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8001,http://127.0.0.1:8001")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://localhost:8001", "http://127.0.0.1:8001"]


@lru_cache(maxsize=1)
def get_app_graph():
    """Create LangGraph app once per process."""
    load_dotenv()

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

    ensure_zadanie2_stack()

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
    )

    logger.info("Initializing LangGraph agent for web_app.")
    return create_agent_graph(llm)


app = FastAPI(title="Task 3 - LangGraph Maintenance Assistant API")

cors_origins = _cors_origins_from_env()
allow_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    app_graph = get_app_graph()
    state = app_graph.invoke({"user_query": req.message})
    answer = state.get("final_answer", "(no answer)")
    return ChatResponse(answer=answer)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=int(os.getenv("WEB_APP_PORT", "8001")),
        reload=True,
    )

