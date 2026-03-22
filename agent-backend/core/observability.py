import time


# core/observability.py
class Observability:
    """
    Unified observability class for LangGraph + LLMOps
    """
    def __init__(self):
        self.events = []

    def log(self, node_name: str, data: dict):
        """
        Node-level logging
        """
        self.events.append({
            "type": "node",
            "node": node_name,
            "data": data
        })

    def track_event(self, event_name: str, data: dict = None):
        """
        Generic event logging (LLM calls, tools, retries, etc.)
        """
        self.events.append({
            "type": "event",
            "event": event_name,
            "data": data or {}
        })

    def get_trace(self):
        """
        Return all events for streaming / debugging
        """
        return self.events

    def summary(self):
        """
        Return a simple summary
        """
        return {
            "total_events": len(self.events),
            "nodes_logged": sum(1 for e in self.events if e["type"] == "node"),
            "events_logged": sum(1 for e in self.events if e["type"] == "event")
        }