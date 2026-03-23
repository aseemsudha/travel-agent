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
from core.vector_db import save_memory
from core.vector_memory import search_memory_faiss
from core.vector_db import search_memory
from core.knowledge_rag import search_knowledge
from core.query_rewriter import rewrite_query
from core.retry import fix_tool_input

import json
import re


from core.observability import Observability as LGObs
from llmops.observability import Observability as LLMObs

from langsmith import traceable

from app_config import RECURSION_LIMIT


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
    obs.log("memory", {"query": state["query"]})

    session_id = state["session_id"]
    query = state["query"]

    history = get_memory(session_id)
    history_text = "\n".join(history) if history else "No history"

    relevant_memories = search_memory(query)
    memory_context = "\n".join(relevant_memories) if relevant_memories else "No memory"

    state["memory_context"] = f"{history_text}\n{memory_context}"
    return state


# =====================================================
# RAG NODE
# =====================================================
@traceable(name="rag_node")
def rag_node(state: AgentState):
    obs = state["trace"]
    obs.log("rag", {"query": state["query"]})

    query = state["query"]
    search_query = rewrite_query(query)
    knowledge_results = search_knowledge(search_query)

    knowledge_text = "\n".join(
        [k["text"] if isinstance(k, dict) else str(k) for k in knowledge_results]
    ) if knowledge_results else "No knowledge found"

    state["knowledge_context"] = knowledge_text
    return state


# =====================================================
# AGENT NODE
# =====================================================
@traceable(name="agent_node")
def agent_node(state: AgentState):
    print("Running AGENT node")
    state["retry_count"] = state.get("retry_count", 0) + 1

    print(
        f"AGENT STEP:",
        state["retry_count"]
    )
    obs = state["trace"]
    query = state["query"]
    memory = state.get("memory_context", "")
    knowledge = state.get("knowledge_context", "")
    tool_output = state.get("tool_output", {})

    json_instruction = {
        "answer": "<plain text answer>",
        "cards": [{"title": "...", "description": "..."}],
        "map": "<map link if applicable>",
        "tips": ["tip 1", "tip 2"]
    }

    prompt = f"""
        You are an AI travel assistant.

        You MUST consider the user's previous preferences and conversation history when generating the response.

        User Memory:
        {memory}

        Relevant Knowledge:
        {knowledge}

        User Query:
        {query}

        You MUST return ONLY valid JSON.

        Do NOT write explanations.
        Do NOT write markdown.
        Do NOT write text before or after JSON.

        Return exactly this format:

        {json.dumps(json_instruction, indent=4)}

        If information is missing, still generate a useful plan.
    """

    # LLMOps observability
    llm_obs = LLMObs()
    llm_obs.log_event("llm_call", {"prompt": prompt[:200]})

    response = call_llm(prompt, obs=obs)

    state["messages"].append({"role": "assistant", "content": response})

    # Parse JSON safely

    try:

        cleaned = re.sub(
            r"```json|```",
            "",
            response
        ).strip()

        structured = json.loads(cleaned)

    except Exception as e:

        print("JSON parse failed:", e)

        structured = {
            "answer": cleaned if "cleaned" in locals() else response,
            "cards": [],
            "map": None,
            "tips": []
        }

    state["tool_output"] = structured
    obs.log("agent", {"response": response[:200]})
    return state


# =====================================================
# TOOL NODE
# =====================================================
@traceable(name="tool_node")
def tool_node(state: AgentState):
    print("Running TOOL node")
    import re, json
    obs = state["trace"]
    last_message = state["messages"][-1]["content"]

    action_match = re.search(r"Action:\s*(.*)", last_message)
    input_match = re.search(r"Action Input:\s*(.*)", last_message)

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

    try:
        result = execute_tool(tool_name, tool_input)
        if isinstance(result, dict) and "error" in result:
            state["error"] = result["error"]
        else:
            state["tool_output"] = result
            state["error"] = ""
    except Exception as e:
        state["error"] = f"Tool execution failed: {str(e)}"
        return state

    state["messages"].append({"role": "system", "content": f"Observation: {result}"})
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
    return state


# =====================================================
# CRITIC NODE
# =====================================================
@traceable(name="critic_node")
def critic_node(state: AgentState):

    print("Running CRITIC node")

    obs = state["trace"]

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
    save_memory(
        f"user: {state['query']}",
        {
            "session_id": state["session_id"],
            "type": "conversation"
        }
    )

    save_memory(
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

    return state

# =====================================================
# ROUTER
# =====================================================
def router(state: AgentState):

    last_message = (
        state["messages"][-1]["content"]
        if state["messages"]
        else ""
    )

    retry_count = state.get("retry_count", 0)

    # If tool error → retry
    if state.get("error") and retry_count < 2:
        return "retry"

    # If LLM produced action
    if "Action:" in last_message:
        return "tool"

    # If structured answer exists → finish
    if state.get("tool_output"):
        return "critic"

    # Safety stop
    if retry_count >= 2:
        return "critic"

    return "critic"


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
        {"retry": "retry", "agent": "agent"}
    )

    graph.add_edge("retry", "tool")
    graph.add_edge("critic", END)

    return graph.compile()


# =====================================================
# RUN FUNCTION
# =====================================================
@traceable(name="run_langgraph_agent")
def run_langgraph_agent(query: str, session_id: str):
    graph = build_graph()
    obs = LGObs()  # LangGraph observability

    state = {
        "query": query,
        "session_id": session_id,
        "messages": [],
        "memory_context": "",
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

    return {
        "answer": state.get("tool_output", {}).get("answer", "No answer generated"),
        "structured_answer": state.get("tool_output", {}),
        "trace": obs.get_trace(),
        "summary": obs.summary()
    }