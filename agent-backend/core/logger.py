import logging
import json

class StructuredLogger:

    def __init__(self):

        self.logger = logging.getLogger("agent")

        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()

        formatter = logging.Formatter("%(message)s")

        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

        self.logger.propagate = False   # ADD THIS

    def log(self, **kwargs):

        log_entry = {
            "event": kwargs.get("event"),
            "session_id": kwargs.get("session_id"),
            "node": kwargs.get("node"),
            "latency_ms": kwargs.get("latency_ms")
        }

        # Add any extra fields dynamically

        for key, value in kwargs.items():

            if key not in log_entry and value is not None:

                log_entry[key] = value

        self.logger.info(json.dumps(log_entry))


logger = StructuredLogger()