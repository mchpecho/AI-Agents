import json
import logging
import os
from typing import Any, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from tools.memory_tool import LongTermMemoryTool
from tools.rag_tool import RAGTool
from tools.search_tool import WebSearchTool
from tools.sql_tool import SQLPlannerExecutor

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    user_query: str
    memory_context: list[str]
    plan: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    final_answer: str
    trace: list[str]


def _safe_json_parse(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", maxsplit=1)[1].split("```", maxsplit=1)[0].strip()
    elif "```" in text:
        text = text.split("```", maxsplit=1)[1].split("```", maxsplit=1)[0].strip()
    try:
        return json.loads(text)
    except Exception:
        return None


def _looks_like_memory_intent(query: str) -> bool:
    lowered = query.lower()
    keywords = [
        "remember",
        "preference",
        "preferences",
        "i prefer",
        "my name is",
    ]
    return any(k in lowered for k in keywords)


def create_agent_graph(llm: BaseChatModel):
    sql_mode = os.getenv("SQL_BACKEND_MODE", "").strip().lower()
    if not sql_mode:
        # Backward compatibility with the previous flag
        sql_mode = "mcp" if os.getenv("USE_MCP_SQL", "true").lower() == "true" else "native"

    sql_tool = SQLPlannerExecutor(
        llm=llm,
        backend_mode=sql_mode,  # type: ignore[arg-type]
        mcp_server_path=os.getenv(
            "SQL_MCP_SERVER_PATH",
            os.getenv("MCP_SQL_SERVER_PATH", "mcp_server/mcp_postgres_server.py"),
        ),
        runtime_fallback=os.getenv("SQL_RUNTIME_FALLBACK", "true").lower() == "true",
    )
    rag_tool = RAGTool(
        chroma_host=os.getenv("CHROMA_HOST", "localhost"),
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
        collection_name=os.getenv("CHROMA_COLLECTION", "kb_lankovacka"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    )
    memory_tool = LongTermMemoryTool(
        chroma_host=os.getenv("CHROMA_HOST", "localhost"),
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        collection_name=os.getenv("LONG_TERM_MEMORY_COLLECTION", "long_term_memory"),
    )
    web_mode = os.getenv("WEB_BACKEND_MODE", "auto").strip().lower()
    try:
        web_search_tool: WebSearchTool | None = WebSearchTool(
            backend_mode=web_mode,  # type: ignore[arg-type]
            mcp_server_path=os.getenv("TAVILY_MCP_SERVER_PATH", "mcp_server/mcp_tavily_server.py"),
            max_results=int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5")),
            runtime_fallback=os.getenv("WEB_RUNTIME_FALLBACK", "true").lower() == "true",
        )
    except Exception as exc:
        logger.warning("[WEB] Web search tool disabled due to init error: %s", exc)
        web_search_tool = None

    def load_memory(state: AgentState) -> AgentState:
        query = state["user_query"]
        memories = memory_tool.search_memories(query=query, n_results=4)
        context = [m["text"] for m in memories]
        trace = state.get("trace", []) + [f"load_memory: retrieved={len(context)}"]
        logger.info("[TRACE] %s", trace[-1])
        return {"memory_context": context, "trace": trace}

    def _validate_plan(raw_plan: Any, fallback_instruction: str) -> list[dict[str, Any]]:
        """Ensure plan has a safe, minimal shape."""
        allowed_tools = {"sql_query", "rag_search", "memory_search", "memory_write", "web_search"}
        if not isinstance(raw_plan, list):
            return [{"step": 1, "tool": "rag_search", "instruction": fallback_instruction}]

        cleaned: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_plan, start=1):
            if not isinstance(item, dict):
                continue
            tool = str(item.get("tool", "")).strip()
            instruction = str(item.get("instruction", "")).strip() or fallback_instruction
            if tool not in allowed_tools:
                continue
            step_no = item.get("step")
            try:
                step_int = int(step_no)
            except Exception:
                step_int = idx
            cleaned.append(
                {
                    "step": step_int,
                    "tool": tool,
                    "instruction": instruction,
                }
            )

        if not cleaned:
            cleaned = [{"step": 1, "tool": "rag_search", "instruction": fallback_instruction}]
        if len(cleaned) > 4:
            cleaned = cleaned[:4]
        return cleaned

    def planner(state: AgentState) -> AgentState:
        query = state["user_query"]
        memory_context = state.get("memory_context", [])

        prompt = f"""
You are a planning agent. Build a short execution plan in **English** using these tools:
- sql_query: when telemetry/alarms data from PostgreSQL is needed.
- rag_search: when SOP/knowledge base content is needed.
- memory_search: when user preferences or prior facts may help.
- memory_write: when the user explicitly asks to remember something or store a preference.
- web_search: when the user asks for external product/vendor info (e.g., Siemens components) that is not in the local KB.

Return **only valid JSON**, with this exact schema and field names:
{{
  "plan": [
    {{"step": 1, "tool": "sql_query", "instruction": "..." }}
  ]
}}

Rules:
- Use 1–4 steps.
- Use only these tool values: "sql_query", "rag_search", "memory_search", "memory_write", "web_search".
- If the query asks about historical telemetry or alarms, include at least one sql_query step.
- If the query asks for SOP/procedure/knowledge, include at least one rag_search step.
- If memory_context is not empty and can help, include memory_search.
- If the user asks to remember something or mentions preferences, include memory_write.
- If the query asks about vendor documentation or components outside the local KB, include web_search.

Important SQL schema constraints for sql_query instructions:
- telemetry columns: ts, machine_id, tag, value, unit
- alarms columns: ts, machine_id, alarm_code, severity, message, state
- NEVER reference non-existent columns like temperature or timestamp.
- For temperature questions, use telemetry rows where tag is temperature-related and aggregate value over value.
- For time filters, always use ts and expressions like now() - interval '8 hours'.
- Prefer machine_id='LNK-01' when the machine is not specified.

Example for average temperature over the last 8 hours:
"Compute AVG(value) from telemetry where machine_id='LNK-01', ts >= now() - interval '8 hours', and tag IN ('TempGearbox_C','TempMotor_C')."

User query:
{query}

Memory context (can be empty):
{memory_context}
""".strip()

        raw = llm.invoke(prompt).content
        raw_text = raw if isinstance(raw, str) else str(raw)
        parsed = _safe_json_parse(raw_text) or {}
        raw_plan = parsed.get("plan")
        plan = _validate_plan(raw_plan, fallback_instruction=query)

        trace = state.get("trace", []) + [f"planner: steps={len(plan)}"]
        logger.info("[PLAN] %s", json.dumps(plan, ensure_ascii=False))
        logger.info("[TRACE] %s", trace[-1])
        return {"plan": plan, "trace": trace}

    def execute(state: AgentState) -> AgentState:
        plan = state.get("plan", [])
        query = state["user_query"]
        results: list[dict[str, Any]] = []
        trace = list(state.get("trace", []))

        for item in plan:
            tool = item.get("tool", "")
            instruction = item.get("instruction", query)
            step_no = item.get("step", "?")
            logger.info("[EXECUTE] step=%s tool=%s instruction=%s", step_no, tool, instruction)

            try:
                if tool == "sql_query":
                    tool_result = sql_tool.run(instruction)
                elif tool == "rag_search":
                    tool_result = rag_tool.search(instruction, n_results=3)
                elif tool == "memory_search":
                    tool_result = memory_tool.search_memories(instruction, n_results=4)
                elif tool == "memory_write":
                    memory_id = memory_tool.save_memory(
                        text=instruction,
                        metadata={"kind": "explicit_user_memory", "source_query": query},
                    )
                    tool_result = {"stored": True, "memory_id": memory_id}
                elif tool == "web_search":
                    if web_search_tool is None:
                        raise RuntimeError(
                            "Web search tool is disabled. Configure WEB_BACKEND_MODE and TAVILY_API_KEY."
                        )
                    lowered = instruction.lower()
                    vendor = "siemens" if "siemens" in lowered else None
                    tool_result = web_search_tool.search(instruction, vendor=vendor)
                else:
                    tool_result = {"warning": f"Unknown tool: {tool}"}

                results.append(
                    {
                        "step": step_no,
                        "tool": tool,
                        "instruction": instruction,
                        "result": tool_result,
                    }
                )
                trace_line = f"execute: step={step_no} tool={tool} ok"
                trace.append(trace_line)
                logger.info("[TRACE] %s", trace_line)
            except Exception as exc:
                err = {
                    "step": step_no,
                    "tool": tool,
                    "instruction": instruction,
                    "error": str(exc),
                }
                results.append(err)
                trace_line = f"execute: step={step_no} tool={tool} error"
                trace.append(trace_line)
                logger.exception("[EXECUTE] step failed: %s", trace_line)

        # Simple aggregate validation flag for respond node
        any_success = any("result" in r for r in results)
        all_errors = all("error" in r for r in results) if results else True
        state_status = {
            "has_results": any_success,
            "all_errors": all_errors,
            "num_steps": len(plan),
        }
        trace.append(f"execute: summary has_results={any_success} all_errors={all_errors}")
        logger.info("[TRACE] %s", trace[-1])
        return {"tool_results": results, "trace": trace, "execution_status": state_status}

    def respond(state: AgentState) -> AgentState:
        query = state["user_query"]
        memory_context = state.get("memory_context", [])
        tool_results = state.get("tool_results", [])
        execution_status = state.get("execution_status", {})

        prompt = f"""
You are a Maintenance AI assistant for production machines in the tire industry.
Typical users are line operators and maintenance technicians asking about:
- machine status and behavior,
- alarms and events,
- SOPs and troubleshooting steps,
- historical telemetry and trends.

You are running inside a Plan-Execute workflow and MUST base your answers only on:
- SQL results from telemetry/alarms (machine data),
- RAG results from the knowledge base (SOPs, docs),
- long-term memory snippets,
- web search outputs for external components.

Style and tone:
- Always answer in clear, concise English.
- Treat English as the default response language.
- Ignore any stored memory that asks for Slovak or another non-English default language unless the current user query explicitly requests that language.
- Be technically correct, but explain concepts so that a less experienced operator can understand.
- Prefer short paragraphs and ordered/bulleted lists for procedures.
- Where helpful, mention which sources you used (SQL / KB / memory / web), but do not dump raw JSON.

Grounding and safety:
- If data is missing or tools failed, say so explicitly and do NOT invent values, timestamps, or parameters.
- If execution_status.all_errors is true or execution_status.has_results is false, explain that tools did not return useful data and suggest what the operator could check manually.

User query:
{query}

Memory context:
{memory_context}

Execution status (for your reasoning, do not repeat verbatim):
{json.dumps(execution_status, ensure_ascii=False)}

Tool results:
{json.dumps(tool_results, ensure_ascii=False)}
""".strip()

        answer = llm.invoke(prompt).content
        final_answer = answer if isinstance(answer, str) else str(answer)
        trace = state.get("trace", []) + ["respond: done"]
        logger.info("[TRACE] %s", trace[-1])
        return {"final_answer": final_answer, "trace": trace}

    def persist_memory(state: AgentState) -> AgentState:
        query = state["user_query"]
        answer = state.get("final_answer", "")
        trace = list(state.get("trace", []))

        if _looks_like_memory_intent(query):
            memory_text = f"User memory: {query} | Agent answer: {answer[:300]}"
            memory_tool.save_memory(
                text=memory_text,
                metadata={"kind": "preference_or_fact", "source_query": query},
            )
            trace_line = "persist_memory: stored explicit preference/fact"
            trace.append(trace_line)
            logger.info("[TRACE] %s", trace_line)
            return {"trace": trace}

        # Generic compact episodic memory for future context
        summarize_prompt = f"""
Extract one concise reusable fact from this interaction.
If nothing useful should be stored, return JSON: {{"store": false, "memory": ""}}
Else return JSON: {{"store": true, "memory": "..."}}

Interaction:
User: {query}
Agent: {answer}
""".strip()
        raw = llm.invoke(summarize_prompt).content
        parsed = _safe_json_parse(raw if isinstance(raw, str) else str(raw))

        if parsed and parsed.get("store") and parsed.get("memory"):
            memory_tool.save_memory(
                text=str(parsed["memory"]),
                metadata={"kind": "episodic", "source_query": query},
            )
            trace_line = "persist_memory: stored episodic fact"
        else:
            trace_line = "persist_memory: skipped"

        trace.append(trace_line)
        logger.info("[TRACE] %s", trace_line)
        return {"trace": trace}

    graph = StateGraph(AgentState)
    graph.add_node("load_memory", load_memory)
    graph.add_node("planner", planner)
    graph.add_node("execute", execute)
    graph.add_node("respond", respond)
    graph.add_node("persist_memory", persist_memory)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "planner")
    graph.add_edge("planner", "execute")
    graph.add_edge("execute", "respond")
    graph.add_edge("respond", "persist_memory")
    graph.add_edge("persist_memory", END)

    return graph.compile()

