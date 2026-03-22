import os
import json
from collections import defaultdict


LOG_DIR = "logs"


def load_all_logs():
    logs = []

    if not os.path.exists(LOG_DIR):
        return logs

    for file in os.listdir(LOG_DIR):
        if file.endswith(".json"):
            with open(os.path.join(LOG_DIR, file), "r") as f:
                try:
                    trace = json.load(f)

                    # ✅ Handle stringified JSON
                    if isinstance(trace, str):
                        trace = json.loads(trace)

                    # ✅ Only valid traces
                    if isinstance(trace, dict) and "events" in trace:
                        logs.append(trace)

                except Exception as e:
                    print(f"Skipping {file}: {e}")

    return logs

def prompt_performance():
    logs = load_all_logs()
    scores = defaultdict(list)

    for session in logs:
        prompt_version = None
        evaluation = None

        for entry in session.get("events", []):   # ✅ FIX
            if entry["event"] == "PROMPT_VERSION":
                prompt_version = entry["data"]

            if entry["event"] == "ANSWER_EVALUATION":
                evaluation = entry["data"]

        if prompt_version and evaluation:
            try:
                score = evaluation.get("relevance_score", 0)   # ✅ FIX
                scores[prompt_version].append(score)
            except:
                continue

    return {
        k: sum(v)/len(v) if v else 0
        for k, v in scores.items()
    }

def hallucination_rate():
    logs = load_all_logs()

    total = 0
    high = 0

    for session in logs:
        for entry in session.get("events", []):   # ✅ FIX
            if entry["event"] == "ANSWER_EVALUATION":
                total += 1

                data = entry["data"]

                if isinstance(data, dict):
                    if data.get("hallucination_risk") == "high":
                        high += 1
                elif isinstance(data, str):
                    if "high" in data.lower():
                        high += 1

    return high / total if total else 0

def tool_usage():
    logs = load_all_logs()
    tool_counts = defaultdict(int)

    for session in logs:
        for entry in session.get("events", []):   # ✅ FIX
            if entry["event"] == "TOOL_CALL":
                tool = entry["data"]["tool"]
                tool_counts[tool] += 1

    return dict(tool_counts)

def success_rate():
    logs = load_all_logs()

    total = 0
    success = 0

    for session in logs:
        has_final = False

        for entry in session.get("events", []):
            if entry["event"] == "FINAL_ANSWER":
                has_final = True

        total += 1
        if has_final:
            success += 1

    return success / total if total else 0

def retry_rate():
    logs = load_all_logs()

    total = 0
    retries = 0

    for session in logs:
        triggered = False

        for entry in session.get("events", []):
            if entry["event"] == "WEAK_RETRIEVAL_DETECTED":
                triggered = True

        total += 1
        if triggered:
            retries += 1

    return retries / total if total else 0

def failure_reasons():
    logs = load_all_logs()

    reasons = defaultdict(int)

    for session in logs:
        for entry in session.get("events", []):
            if entry["event"] in [
                "AGENT_ERROR",
                "REASONING_LOOP_DETECTED",
                "TOOL_LOOP_DETECTED",
                "MAX_STEPS_REACHED"
            ]:
                reasons[entry["event"]] += 1

    return dict(reasons)

def prompt_stats():
    logs = load_all_logs()

    stats = defaultdict(lambda: {"count": 0, "success": 0})

    for session in logs:
        prompt_version = None
        success = False

        for entry in session.get("events", []):
            if entry["event"] == "PROMPT_VERSION":
                prompt_version = entry["data"]

            if entry["event"] == "FINAL_ANSWER":
                success = True

        if prompt_version:
            stats[prompt_version]["count"] += 1
            if success:
                stats[prompt_version]["success"] += 1

    return {
        k: v["success"] / v["count"] if v["count"] else 0
        for k, v in stats.items()
    }