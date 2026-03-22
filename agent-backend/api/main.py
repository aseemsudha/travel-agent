###For creating virtual env######run command###### python -m venv venv
####activate venv###### source venv/bin/activate
# python -m uvicorn api.main:app --reload
# python -m uvicorn main:app --reload 
# touch apps/__init__.py 
# touch core/__init__.py
# touch api/__init__.py 
# streamlit run dashboard.py

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
    map_link = structured.get("map")
    tips = structured.get("tips", [])

    if answer:
        for word in answer.split():
            yield {"event": "message", "data": word + " "}
            await asyncio.sleep(0.05)

    for card in cards:
        yield {"event": "card", "data": json.dumps(card)}
        await asyncio.sleep(0.05)

    if map_link:
        yield {"event": "map", "data": map_link}
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

    try:

        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_langgraph_agent,
                query,
                session_id
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
