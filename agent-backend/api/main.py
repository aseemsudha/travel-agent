###For creating virtual env######run command###### python -m venv venv
####activate venv###### source venv/bin/activate
# python -m uvicorn api.main:app --reload
# python -m uvicorn main:app --reload 
# touch apps/__init__.py 
# touch core/__init__.py
# touch api/__init__.py 
# touch apps/travel_assistant/prompts/__init__.py
# streamlit run dashboard.py


###prompt selection integration
#####graph.py langgraph mapping### no maps in tolls used
#### weird response smart toll has alreeady answered
### product improvements

####changes for Vertex AI####
# .env changes
# config.py file
# llm.py file

# -------------------------------
# Setup & Imports
# -------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import logging

from core.langgraph_agent import run_langgraph_agent
from core.knowledge_rag import load_knowledge

from api.memory_deletion import router as memory_router
from api.session import router as session_router
from core.intent_validator import validate_product_intent
from core.vector_db import store_memory, retrieve_memory
from utils.parser import extract_preference




######to test vertex AI is working or not######
# from core.llm import call_llm

# print("\n--- Vertex Health Check ---")

# try:
#     response = call_llm("Respond with: Vertex test successful")
#     print("LLM Response:", response)
# except Exception as e:
#     print("Vertex Test Failed:", e)

# import os

# print("LangSmith tracing:", os.getenv("LANGCHAIN_TRACING_V2"))

app = FastAPI()
logging.basicConfig(level=logging.INFO)
app.include_router(memory_router, prefix="/api")
app.include_router(session_router, prefix="/api")

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Load knowledge on startup
# -------------------------------
@app.on_event("startup")
def startup_event():
    load_knowledge()


# -------------------------------
# SSE Generator
# -------------------------------
async def event_generator(result: dict):
    """
    Stream LangGraph node traces first, then final answer word by word,
    plus cards/maps/tips.
    """
    trace = result.get("trace", [])
    for t in trace:
        yield {"event": "node", "data": json.dumps(t)}
        await asyncio.sleep(0.05)

    structured = result.get("structured_answer", {})
    answer = structured.get("answer", "")
    cards = structured.get("cards", [])
    # map_link = structured.get("map")
    map_places = structured.get("map")
    tips = structured.get("tips", [])

    if answer:
        for word in answer.split():
            yield {"event": "message", "data": word + " "}
            await asyncio.sleep(0.05)

    for card in cards:
        yield {"event": "card", "data": json.dumps(card)}
        await asyncio.sleep(0.05)

    # if map_link:
    #     yield {"event": "map", "data": map_link}
    #     await asyncio.sleep(0.05)

    if map_places:
        yield {"event": "map","data": json.dumps(map_places)}
        await asyncio.sleep(0.05)

    for tip in tips:
        yield {"event": "tip", "data": tip}
        await asyncio.sleep(0.05)

    yield {"event": "end", "data": "[DONE]"}


# -------------------------------
# SSE Chat Endpoint
# -------------------------------
@app.get("/chat-stream")
async def chat_stream(query: str, session_id: str):

    logging.info(f"Received query: {query}")

    memory_keywords = [
        "remember",
        "save",
        "set",
        "store",
        "update"
    ]

    is_memory_update = any(
        word in query.lower()
        for word in memory_keywords
    )

    # ----------------------------------
    # STORE PREFERENCE
    # ----------------------------------

    if is_memory_update:

        key, value = extract_preference(query)

        # -----------------------------
        # Fallback if parser fails
        # -----------------------------
        if not key:

            key = "general"
            value = query

        text = f"{key}: {value}"

        metadata = {
            "session_id": session_id,
            "type": "preference",
            "key": key
        }

        store_memory(text, metadata)

        print("Preference stored:", text)

        async def memory_saved():

            yield {
                "event": "message",
                "data": f"Saved preference: {text}"
            }

            yield {
                "event": "end",
                "data": "[DONE]"
            }

        return EventSourceResponse(memory_saved())

    # ----------------------------------
    # READ PREFERENCE
    # ----------------------------------

    preference_query_keywords = [
        "what is my preference",
        "show my preference",
        "my saved preference",
        "my budget",
        "my location"
    ]

    is_preference_query = any(
        phrase in query.lower()
        for phrase in preference_query_keywords
    )

    if is_preference_query:

        memories = retrieve_memory(session_id)

        if not memories:

            async def no_pref():

                yield {
                    "event": "message",
                    "data": "No preferences saved yet."
                }

                yield {
                    "event": "end",
                    "data": "[DONE]"
                }

            return EventSourceResponse(no_pref())

        pref_text = "Your saved preferences:\n"

        for m in memories:
            pref_text += f"- {m['key']}: {m['value']}\n"

        async def show_pref():

            yield {
                "event": "message",
                "data": pref_text
            }

            yield {
                "event": "end",
                "data": "[DONE]"
            }

        return EventSourceResponse(show_pref())

    try:

        # ----------------------------------
        # INTENT VALIDATION
        # ----------------------------------

        is_travel, intent = validate_product_intent(query)

        print("INTENT:", intent)
        print("SESSION ID:", session_id)

        if not is_travel:

            async def non_travel():

                message = (
                    "I specialize in travel-related assistance only. "
                    "Please ask about flights, hotels, destinations, "
                    "or trip planning."
                )

                yield {
                    "event": "message",
                    "data": message
                }

                yield {
                    "event": "end",
                    "data": "[DONE]"
                }

            return EventSourceResponse(non_travel())

        # ----------------------------------
        # LOAD MEMORY
        # ----------------------------------

        memories = retrieve_memory(session_id)

        # ----------------------------------
        # RUN LANGGRAPH
        # ----------------------------------

        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_langgraph_agent,
                query,
                session_id,
                memory=memories
            ),
            timeout=60
        )

        return EventSourceResponse(
            event_generator(result)
        )

    except Exception as e:

        import traceback

        error_text = str(e) or "Unknown error"

        logging.error(
            f"Error in chat_stream: {error_text}"
        )

        traceback.print_exc()

        async def error():

            yield {
                "event": "message",
                "data": f"Error: {error_text}"
            }

            yield {
                "event": "end",
                "data": "[DONE]"
            }

        return EventSourceResponse(error())