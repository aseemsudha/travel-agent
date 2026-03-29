# Your old system:
# while loop → LLM → tool → loop → final answer
# 👉 Hidden flow
# 👉 Hard to debug
# 👉 Hard to scale
# Your new system (LangGraph):
# Graph of nodes → controlled execution → state passed between nodes
# 👉 Explicit flow
# 👉 Each step is a node
# 👉 State moves through the graph
# 🔥 Core Idea
# 👉 Instead of looping manually
# 👉 You define nodes + transitions
# LangGraph executes it like a workflow engine.

# =====================================================
# LANGGRAPH AGENT (FULL FILE)
# =====================================================

# =====================================================
# LANGGRAPH AGENT WITH MEMORY + RAG
# =====================================================

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from core.llm import call_llm
from core.tool_registry import execute_tool
from core.critic import run_critic

from core.memory import get_memory
from core.vector_db import (
    store_memory,
    search_memory,
    get_memory_collection
)
from core.vector_memory import search_memory_faiss
from core.knowledge_rag import search_knowledge
from core.query_rewriter import rewrite_query
from core.retry import fix_tool_input

import json
import re


from core.observability import Observability as LGObs
from llmops.observability import Observability as LLMObs

from langsmith import traceable

from app_config import RECURSION_LIMIT, LLM_MODEL, RETRY_LIMIT
from core.tool_retry import safe_tool_call

from core.logger import logger
import time
from apps.travel_assistant.prompts.prompts import get_prompt
from apps.travel_assistant.prompts.prompt_selector import choose_prompt



# =====================================================
# STATE
# =====================================================
class AgentState(TypedDict):
    query: str
    session_id: str
    messages: List[dict]
    memory_context: str
    knowledge_context: str
    tool_output: dict
    final_answer: str
    retry_count: int
    error: str
    trace: LGObs  # LangGraph observability


# =====================================================
# MEMORY NODE
# =====================================================
@traceable(name="memory_node")
def memory_node(state: AgentState):

    obs = state["trace"]
    start = time.time()

    session_id = state["session_id"]
    query = state["query"]

    obs.log(
        "memory",
        {
            "query": query,
            "session_id": session_id
        }
    )

    # -------------------------
    # ALWAYS load session history
    # -------------------------

    history = get_memory(session_id)

    history_text = (
        "\n".join(history[-5:])
        if history
        else ""
    )

    # -------------------------
    # Semantic memory search
    # -------------------------

    collection = get_memory_collection()

    results = collection.get(
        where={
            "session_id": session_id
        },
        limit=5
    )

    documents = results.get("documents", [])

    memory_text = (
        "\n".join(documents)
        if documents
        else ""
    )

    # -------------------------
    # Combine both
    # -------------------------

    state["memory_context"] = f"""
        Recent Conversation:
        {history_text}

        Relevant Preferences:
        {memory_text}
    """

    latency = int((time.time() - start) * 1000)

    logger.log(
        event="memory_retrieval",
        session_id=session_id,
        node="memory",
        history_count=len(history),
        semantic_count=len(documents),
        latency_ms=latency
    )

    print("MEMORY CONTEXT:")
    print(state["memory_context"])

    print("SESSION:", session_id)
    print("MEMORY RETRIEVED:", documents)

    return state


# =====================================================
# RAG NODE
# =====================================================
@traceable(name="rag_node")
def rag_node(state: AgentState):
    obs = state["trace"]
    obs.log("rag", {"query": state["query"]})

    start = time.time()
    query = state["query"]
    search_query = rewrite_query(query)
    knowledge_results = search_knowledge(search_query)

    latency = int((time.time() - start) * 1000)

    knowledge_text = "\n".join(
        [k["text"] if isinstance(k, dict) else str(k) for k in knowledge_results]
    ) if knowledge_results else "No knowledge found"

    state["knowledge_context"] = knowledge_text

    logger.log(
        event="rag_retrieval",
        session_id=state["session_id"],
        node="rag",
        documents_found=len(knowledge_results),
        latency_ms=latency
    )
    return state


# =====================================================
# AGENT NODE
# =====================================================
@traceable(name="agent_node")
def agent_node(state: AgentState):
    print("Running AGENT node")
    # state["retry_count"] = state.get("retry_count", 0) + 1
    state.setdefault("retry_count", 0)

    print(
        f"AGENT STEP:",
        state["retry_count"]
    )
    obs = state["trace"]
    query = state["query"]
    memory = state.get("memory_context", "")
    knowledge = state.get("knowledge_context", "")
    tool_output = state.get("tool_output", {})
    history = state.get("memory_context", "")
    scratchpad = "\n".join(
        msg["content"]
        for msg in state["messages"]
    )

    # json_instruction = {
    #     "answer": "<plain text answer>",
    #     "cards": [{"title": "...", "description": "..."}],
    #     "map": "<map link if applicable>",
    #     "tips": ["tip 1", "tip 2"]
    # }

    json_instruction = {
        "answer": "<plain text answer>",
        "cards": [{"title": "...", "description": "..."}],
        "map": [
            {
                "name": "...",
                "lat": 0.0,
                "lng": 0.0
            }
        ],
        "tips": ["tip 1", "tip 2"]
    }

    prompt_name = choose_prompt()
    obs.log(
        "prompt_selection",
        {
            "prompt": prompt_name
        }
    )
    prompt_template = get_prompt(prompt_name)

    prompt = prompt_template.format(
        history=history,
        memory=memory,
        knowledge=knowledge,
        query=query,
        scratchpad=scratchpad
    )

    # LLMOps observability
    llm_obs = LLMObs()
    llm_obs.log_event("llm_call", {"prompt": prompt[:200]})
    
    start = time.time()

    response = call_llm(prompt, obs=obs)

    latency = int((time.time() - start) * 1000)

    logger.log(
        event="llm_call",
        session_id=state["session_id"],
        node="agent",
        model=LLM_MODEL,
        latency_ms=latency
    )

    state["messages"].append({"role": "assistant", "content": response})

    print("LLM RESPONSE:")
    print(response)

    # Parse JSON safely

    cleaned = re.sub(r"```json|```", "", response).strip()

    # CASE 1 — Tool call
    if "Action:" in cleaned:
        structured = {}  # keep as is, tool will handle it

    # CASE 2 — Final answer text
    elif "Final Answer:" in cleaned:
        final_text = cleaned.split("Final Answer:", 1)[1].strip()
        structured = {
            "answer": final_text,
            "cards": [],
            "map": None,
            "tips": []
        }

    # CASE 3 — JSON response
    else:
        try:
            parsed_json = json.loads(cleaned)
            # Ensure we always have at least "answer" key
            if "answer" not in parsed_json:
                parsed_json["answer"] = cleaned
            structured = parsed_json
        except Exception:
            # fallback if JSON fails
            structured = {
                "answer": cleaned,
                "cards": [],
                "map": None,
                "tips": []
            }

    state["tool_output"] = structured
    obs.log("agent", {"response": response[:200]})

    if not state["tool_output"].get("answer"):
        last_msg = state["messages"][-1]["content"] if state["messages"] else ""
        state["tool_output"]["answer"] = last_msg.strip() or "No answer generated"

    return state


# =====================================================
# TOOL NODE
# =====================================================
@traceable(name="tool_node")
def tool_node(state: AgentState):
    print("Running TOOL node")
    import re, json
    obs = state["trace"]
    last_message = (
        state["messages"][-1]["content"]
        if state["messages"]
        else ""
    )

    action_match = re.search(r"Action:\s*(.*)", last_message)
    input_match = re.search(r"Action Input:\s*(\{.*\})", last_message, re.DOTALL)

    if not action_match:
        state["error"] = "No action found in LLM response"
        return state

    tool_name = action_match.group(1).strip()
    raw_input = input_match.group(1).strip() if input_match else ""

    try:
        tool_input = json.loads(raw_input) if raw_input else {}
    except Exception as e:
        state["error"] = f"Invalid JSON input: {str(e)}"
        return state

    start = time.time()
    result = safe_tool_call(
        execute_tool,
        tool_name,
        tool_input
    )

    latency = int((time.time() - start) * 1000)

    status = (
        "failed"
        if isinstance(result, dict) and "error" in result
        else "success"
    )

    
    logger.log(
        event="tool_execution",
        session_id=state["session_id"],
        node="tool",
        tool=tool_name,
        status = status,
        latency_ms=latency,
        error=result.get("error") if isinstance(result, dict) else None
    )

    if isinstance(result, dict) and "error" in result:

        state["error"] = result["error"]

    else:

        state["tool_output"] = result
        state["error"] = ""

    state["messages"].append({"role": "system", "content": f"Observation: {result}"})
    if isinstance(result, dict) and "error" in result:
        state["error"] = result["error"]
    else:
        state["tool_output"] = result
        state["error"] = ""
    obs.log("tool", {"tool": tool_name, "input": tool_input, "output": result, "error": state.get("error")})
    return state


# =====================================================
# RETRY NODE
# =====================================================
@traceable(name="retry_node")
def retry_node(state: AgentState):
    import re
    obs = state["trace"]
    obs.log("retry", {"retry_count": state.get("retry_count", 0)})
    start = time.time()
    

    if state.get("retry_count", 0) >= 2:
        return state

    last_message = state["messages"][-1]["content"]
    query = state["query"]

    fixed_input = fix_tool_input(query, last_message, obs)
    action_match = re.search(r"Action:\s*(.*)", last_message)
    tool_name = action_match.group(1).strip() if action_match else ""

    state["messages"].append({
        "role": "assistant",
        "content": f"Action: {tool_name}\nAction Input: {fixed_input}"
    })

    state["retry_count"] += 1
    state["error"] = ""

    latency = int((time.time() - start) * 1000)
    logger.log(
        event="retry_attempt",
        session_id=state["session_id"],
        node="retry",
        retry_count=state["retry_count"],
        error=state.get("error"),
        latency_ms=latency
    )

    return state


# =====================================================
# CRITIC NODE
# =====================================================
@traceable(name="critic_node")
def critic_node(state: AgentState):

    print("Running CRITIC node")

    obs = state["trace"]

    start_time = time.time()

    structured = state.get("tool_output", {})
    answer = structured.get("answer")

    if not answer:
        return state

    improved = run_critic(
        state["query"],
        answer,
        obs
    )

    state["final_answer"] = improved

    # Save memory
    store_memory(
        f"user: {state['query']}",
        {
            "session_id": state["session_id"],
            "type": "conversation"
        }
    )

    store_memory(
        f"agent: {improved}",
        {
            "session_id": state["session_id"],
            "type": "conversation"
        }
    )

    obs.log(
        "critic",
        {
            "final": improved[:200]
        }
    )

    latency = int((time.time() - start_time) * 1000)
    logger.log(
        event="final_response",
        session_id=state["session_id"],
        node="critic",
        status="success",
        latency_ms=latency,
        response_length=len(state.get("final_answer", ""))
    )
    return state

# =====================================================
# ROUTER
# =====================================================
def router(state: AgentState):
    """
    Routing logic for LangGraph agent.
    Decides next node based on state:
      - tool → call tool
      - retry → retry tool input
      - critic → finalize answer
      - fallback → critic to prevent infinite loops
    """
    import re
    start = time.time()

    last_message = (
        state["messages"][-1]["content"]
        if state["messages"]
        else ""
    )
    retry_count = state.get("retry_count", 0)
    tool_output = state.get("tool_output", {})

    # ---------------------------------
    # Safety stop: max retries
    # ---------------------------------
    if retry_count >= RETRY_LIMIT:
        decision = "critic"
        logger.log(
            event="routing_decision",
            session_id=state["session_id"],
            node="router",
            decision=decision,
            reason="retry_limit_reached",
            retry_count=retry_count
        )
        return decision

    # ---------------------------------
    # Tool error → retry
    # ---------------------------------
    if state.get("error"):
        decision = "retry"
        logger.log(
            event="routing_decision",
            session_id=state["session_id"],
            node="router",
            decision=decision,
            reason="tool_error",
            retry_count=retry_count
        )
        return decision

    # ---------------------------------
    # LLM produced action → call tool
    # ---------------------------------
    if "Action:" in last_message:
        decision = "tool"
        logger.log(
            event="routing_decision",
            session_id=state["session_id"],
            node="router",
            decision=decision,
            reason="action_detected",
            retry_count=retry_count
        )
        return decision

    # ---------------------------------
    # Final answer detected: in text, JSON, or tool_output
    # ---------------------------------
    if (
        "Final Answer:" in last_message
        or re.search(r'"answer"\s*:', last_message)
        or tool_output.get("answer")
    ):
        decision = "critic"
        logger.log(
            event="routing_decision",
            session_id=state["session_id"],
            node="router",
            decision=decision,
            reason="final_answer_detected",
            retry_count=retry_count
        )
        return decision

    # ---------------------------------
    # Fallback: go to critic to prevent infinite loops
    # ---------------------------------
    decision = "agent"
    logger.log(
        event="routing_decision",
        session_id=state["session_id"],
        node="router",
        decision=decision,
        reason="fallback_to_critic",
        retry_count=retry_count
    )

    latency = int((time.time() - start) * 1000)
    logger.log(
        event="routing_latency",
        session_id=state["session_id"],
        node="router",
        latency_ms=latency
    )

    return decision


# =====================================================
# BUILD GRAPH
# =====================================================
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("memory", memory_node)
    graph.add_node("rag", rag_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tool", tool_node)
    graph.add_node("retry", retry_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("memory")
    graph.add_edge("memory", "rag")
    graph.add_edge("rag", "agent")

    graph.add_conditional_edges(
        "agent",
        router,
        {"tool": "tool", "critic": "critic", "agent": "agent"}
    )

    graph.add_conditional_edges(
        "tool",
        lambda state: "retry" if state.get("error") else "agent",
        {"retry": "retry", "agent": "agent", "critic": "critic"}
    )

    graph.add_edge("retry", "tool")
    graph.add_edge("critic", END)

    return graph.compile()


# =====================================================
# RUN FUNCTION
# =====================================================
@traceable(name="run_langgraph_agent")
def run_langgraph_agent(query: str, session_id: str, memory=None):
    start_time = time.time()
    graph = build_graph()
    obs = LGObs()  # LangGraph observability

    # -----------------------------
    # LOAD USER MEMORY
    # -----------------------------

    memories = memory

    memory_context = ""

    if memories:

        memory_context = "User preferences:\n"

        for m in memories:

            memory_context += f"{m['key']}: {m['value']}\n"

    print("MEMORY CONTEXT:", memory_context)

    state = {
        "query": query,
        "session_id": session_id,
        "messages": [],
        "memory_context": memory_context,
        "knowledge_context": "",
        "tool_output": {},
        "retry_count": 0,
        "error": "",
        "final_answer": "",
        "trace": obs
    }

    state = graph.invoke(
        state,
        config={
            "recursion_limit": RECURSION_LIMIT,
            "metadata": {
                "session_id": session_id,
                "query": query
            }
        }
    )

    print("FINAL TOOL OUTPUT:", state.get("tool_output"))

    total_latency = int((time.time() - start_time) * 1000)

    logger.log(
        event="request_completed",
        session_id=session_id,
        total_latency_ms=total_latency,
        recursion_limit=RECURSION_LIMIT
    )

    final_answer = (
        state.get("final_answer")
        or state.get("tool_output", {}).get("answer")
        or "No answer generated"
    )

    return {
        "answer": final_answer,
        "structured_answer": state.get("tool_output", {}),
        "trace": obs.get_trace(),
        "summary": obs.summary()
    }