def safe_log(obs, node_name: str, data: dict):
    """Log to observability safely. Fail silently if the method is missing or errors."""
    try:
        if obs:
            obs.log(node_name, data)
    except Exception:
        pass