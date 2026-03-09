import logging
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from bootstrap_stack import ensure_zadanie2_stack
from graph import create_agent_graph


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    load_dotenv()
    configure_logging()
    ensure_zadanie2_stack()

    if os.getenv("LANGSMITH_TRACING", "false").lower() == "true":
        logging.getLogger(__name__).info("LangSmith tracing enabled via environment variables.")
    else:
        logging.getLogger(__name__).info("LangSmith tracing disabled; using console traces.")

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
    )

    app = create_agent_graph(llm)

    print("LangGraph Plan-Execute agent is running. Type 'exit' to stop.")
    while True:
        user_query = input("\nYou> ").strip()
        if not user_query:
            continue
        if user_query.lower() in {"exit", "quit", "q"}:
            print("Bye.")
            break

        state = app.invoke({"user_query": user_query})
        print(f"\nAgent> {state.get('final_answer', '(no answer)')}")


if __name__ == "__main__":
    main()

