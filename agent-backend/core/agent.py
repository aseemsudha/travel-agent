# agent.py

import re
import json
import time

from core.llm import call_llm
from core.tool_registry import TOOLS

from core.memory import get_memory, save_memory
from core.vector_memory import add_memory, search_memory

from core.knowledge_rag import search_knowledge

from core.query_rewriter import rewrite_query

from llmops.observability import Observability
from llmops.rag_evaluator import is_retrieval_weak
from llmops.query_retry import generate_retry_query

from apps.travel_assistant.prompts.prompts import get_prompt
from apps.travel_assistant.prompts.prompt_selector import choose_prompt

from core.critic import run_critic


# =====================================================
# SAFE JSON PARSER (ROBUST)
# =====================================================
def safe_json_parse(raw_input):
    try:
        return json.loads(raw_input)
    except:
        pass

    try:
        # Empty → {}
        if not raw_input.strip():
            return {}

        # Try fixing quotes
        fixed = raw_input.replace("'", '"')
        return json.loads(fixed)
    except:
        pass

    try:
        # fallback → treat as query
        return {"query": raw_input.strip()}
    except:
        return None


# =====================================================
# MAIN AGENT
# =====================================================
def run_agent(query, session_id):
    user_query = query
    start_time = time.time()

    try:
        # -------------------------------
        # MEMORY
        # -------------------------------
        history = get_memory(session_id)
        history_text = "\n".join(history) if history else "No previous conversation."

        relevant_memories = search_memory(user_query)
        memory_context = "\n".join(relevant_memories) if relevant_memories else "No relevant user memories."

        # -------------------------------
        # RAG
        # -------------------------------
        search_query = rewrite_query(user_query)
        knowledge_results = search_knowledge(search_query)

        if is_retrieval_weak(knowledge_results):
            retry_query = generate_retry_query(user_query)
            knowledge_results = search_knowledge(retry_query)

        knowledge_context = "\n".join(
            [k["text"] if isinstance(k, dict) else str(k) for k in knowledge_results]
        ) if knowledge_results else "No relevant travel knowledge found."

        # -------------------------------
        # AGENT LOOP
        # -------------------------------
        scratchpad = ""
        tool_history = []
        previous_response = ""

        for step in range(6):

            prompt, prompt_version = build_prompt(
                user_query,
                scratchpad,
                history_text,
                memory_context,
                knowledge_context
            )

            response = call_llm(prompt)

            print("\n🔍 LLM RESPONSE:\n", response)

            # Prevent infinite loop
            if response == previous_response:
                return "I'm stuck while processing this request. Please try rephrasing."

            previous_response = response

            # -------------------------------
            # FINAL ANSWER
            # -------------------------------
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()

                # 🔥 Reflection Layer (Critic)
                try:
                    from core.critic import run_critic
                    improved_answer = run_critic(user_query, final_answer)
                except Exception as e:
                    # fallback in case critic fails
                    improved_answer = final_answer

                # Save improved version
                save_memory(session_id, f"user: {user_query}")
                save_memory(session_id, f"agent: {improved_answer}")

                return improved_answer

            # -------------------------------
            # PARSE ACTION
            # -------------------------------
            action_match = re.search(r"Action:\s*(.*)", response)
            input_match = re.search(r"Action Input:\s*(\{.*\})", response, re.DOTALL)

            # -------------------------------
            # RETRY IF FORMAT INVALID
            # -------------------------------
            if not action_match:
                scratchpad += response + "\nObservation: Invalid format (missing Action)\n"
                continue

            tool_name = action_match.group(1).strip()
            raw_input = input_match.group(1).strip() if input_match else ""

            tool_input = safe_json_parse(raw_input)

            if tool_input is None:
                scratchpad += response + "\nObservation: Invalid JSON input\n"
                continue

            # Prevent repeated calls
            if (tool_name, str(tool_input)) in tool_history:
                return "Agent stopped: repeated tool call detected"

            tool_history.append((tool_name, str(tool_input)))

            # -------------------------------
            # TOOL EXECUTION
            # -------------------------------
            if tool_name not in TOOLS:
                scratchpad += response + "\nObservation: Invalid tool\n"
                continue

            try:
                result = TOOLS[tool_name](tool_input)
            except Exception as e:
                result = f"Tool error: {str(e)}"

            observation = f"\nObservation: {result}\n"
            scratchpad += response + observation

        return "Agent stopped: too many steps"

    except Exception as e:
        return f"Agent crashed: {str(e)}"


# =====================================================
# PROMPT BUILDER
# =====================================================
def build_prompt(user_query, scratchpad, history_text, memory_context, knowledge_context):
    prompt_version = choose_prompt()
    prompt_template = get_prompt(prompt_version)

    try:
        prompt = prompt_template.format(
            history=history_text,
            memory=memory_context,
            knowledge=knowledge_context,
            query=user_query,
            scratchpad=scratchpad
        )
    except KeyError as e:
        raise Exception(
            f"Prompt formatting error: {e}. Fix {{}} in prompt."
        )

    return prompt, prompt_version

    # return f"""
    #     You are an AI Travel Assistant.

    #     You can reason step-by-step and use tools to help answer the user's question.

    #     Available tools:

    #     google_maps_search(query)
    #     Search places using Google Maps.

    #     estimate_crowd(place)
    #     Estimate crowd level.

    #     festival_detector(city)
    #     Detect festivals happening in a city.

    #     suggest_travel_plan(city, interest)
    #     Generate a travel itinerary.

    #     retrieve_travel_knowledge(query)
    #     Use this tool when you need travel knowledge about temples, crowd patterns, visiting times, or travel tips.


    #     Conversation history:
    #     {history_text}

    #     Relevant user memories:
    #     {memory_context}

    #     Relevant travel knowledge:
    #     {knowledge_context}


    #     You must follow this format exactly:

    #     Thought: what you are thinking
    #     Action: tool name
    #     Action Input: input for the tool

    #     After the tool returns a result you will receive an Observation.

    #     Continue reasoning until you can answer the user.


    #     When you know the answer respond with:

    #     Final Answer: your response to the user


    #     User Question:  
    #     {user_query}


    #     Previous steps:
    #     {scratchpad}

    #     Respond with the next step.
    # """