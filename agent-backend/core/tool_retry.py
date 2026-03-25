import time
import logging

logger = logging.getLogger(__name__)

def safe_tool_call(
    tool_func,
    *args,
    retries: int = 2,
    delay: int = 1,
    **kwargs
):
    """
    Safe execution wrapper for tools.

    Handles:
    - retries
    - logging
    - graceful failure
    """

    for attempt in range(retries + 1):

        try:
            logger.info(
                f"[Tool] Calling {tool_func.__name__} "
                f"(attempt {attempt + 1})"
            )

            result = tool_func(*args, **kwargs)

            logger.info(
                f"[Tool] Success: {tool_func.__name__}"
            )

            return result

        except Exception as e:

            logger.error(
                f"[Tool] Failed: {tool_func.__name__} "
                f"error={str(e)}"
            )

            if attempt < retries:

                logger.info(
                    f"[Tool] Retrying in {delay}s..."
                )

                time.sleep(delay)

            else:

                logger.error(
                    f"[Tool] All retries failed: "
                    f"{tool_func.__name__}"
                )

                return {
                    "error": "Tool failed after retries"
                }