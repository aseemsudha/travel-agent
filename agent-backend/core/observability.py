# core/observability.py
import os
import time

from app_config import (
    ENABLE_OBSERVABILITY_LOGGING,
    ENABLE_LANGSMITH_TRACING,
    LANGSMITH_PROJECT
)


class Observability:
    """
    Unified observability class for LangGraph + LLMOps
    """

    def __init__(self):

        self.events = []

        print("Observability logging:", ENABLE_OBSERVABILITY_LOGGING)
        print("LangSmith tracing:", ENABLE_LANGSMITH_TRACING)

        # Configure LangSmith tracing dynamically
        self.configure_tracing()

    # -----------------------------
    # Configure LangSmith
    # -----------------------------

    def configure_tracing(self):

        if ENABLE_LANGSMITH_TRACING:

            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT

            print("LangSmith tracing ENABLED")

        else:

            os.environ["LANGCHAIN_TRACING_V2"] = "false"

            print("LangSmith tracing DISABLED")

    # -----------------------------
    # Node-level logging
    # -----------------------------

    def log(self, node_name: str, data: dict):

        if not ENABLE_OBSERVABILITY_LOGGING:
            return

        self.events.append({
            "type": "node",
            "node": node_name,
            "data": data,
            "timestamp": time.time()
        })

    # -----------------------------
    # Generic event logging
    # -----------------------------

    def track_event(self, event_name: str, data: dict = None):

        if not ENABLE_OBSERVABILITY_LOGGING:
            return

        self.events.append({
            "type": "event",
            "event": event_name,
            "data": data or {},
            "timestamp": time.time()
        })

    # -----------------------------
    # Get full trace
    # -----------------------------

    def get_trace(self):

        return self.events

    # -----------------------------
    # Summary
    # -----------------------------

    def summary(self):

        return {
            "total_events": len(self.events),
            "nodes_logged": sum(
                1 for e in self.events
                if e["type"] == "node"
            ),
            "events_logged": sum(
                1 for e in self.events
                if e["type"] == "event"
            )
        }


























# import time


# # core/observability.py
# class Observability:
#     """
#     Unified observability class for LangGraph + LLMOps
#     """
#     def __init__(self):
#         self.events = []

#     def log(self, node_name: str, data: dict):
#         """
#         Node-level logging
#         """
#         self.events.append({
#             "type": "node",
#             "node": node_name,
#             "data": data
#         })

#     def track_event(self, event_name: str, data: dict = None):
#         """
#         Generic event logging (LLM calls, tools, retries, etc.)
#         """
#         self.events.append({
#             "type": "event",
#             "event": event_name,
#             "data": data or {}
#         })

#     def get_trace(self):
#         """
#         Return all events for streaming / debugging
#         """
#         return self.events

#     def summary(self):
#         """
#         Return a simple summary
#         """
#         return {
#             "total_events": len(self.events),
#             "nodes_logged": sum(1 for e in self.events if e["type"] == "node"),
#             "events_logged": sum(1 for e in self.events if e["type"] == "event")
#         }