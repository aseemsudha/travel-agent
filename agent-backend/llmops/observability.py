import os
import json
import time
import uuid


class Observability:
    def __init__(self):
        self.trace = {
            "trace_id": str(uuid.uuid4()),
            "events": [],
            "start_time": time.time()
        }

    def log_event(self, event_type, data):
        self.trace["events"].append({
            "timestamp": time.time(),
            "event": event_type,
            "data": data
        })

    def export_trace(self):
        log_dir = "logs"

        # ✅ Ensure logs folder exists
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        filename = f"trace_{int(time.time())}.json"
        filepath = os.path.join(log_dir, filename)

        with open(filepath, "w") as f:
            json.dump(self.trace, f, indent=2)

    def track_event(self, data):

        event_type = data.get("type", "event")

        return self.log_event(
            event_type,
            data
        )