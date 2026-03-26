"""
intent_validator.py

Hybrid Intent Validation for Travel Agent

Flow:

1) Keyword check
2) LLM classification fallback
"""

from typing import Tuple

from config import settings
from core.llm import call_llm   


# -------------------------------------
# TRAVEL KEYWORDS
# -------------------------------------

PRODUCT_KEYWORDS = [
    "flight",
    "flights",
    "hotel",
    "hotels",
    "trip",
    "travel",
    "destination",
    "itinerary",
    "visa",
    "airport",
    "tour",
    "booking",
    "vacation",
    "holiday",
    "resort",
    "train",
    "bus",
    "car rental",
    "cruise"
]


# -------------------------------------
# STEP 1 — FAST KEYWORD CHECK
# -------------------------------------
def keyword_check(query: str) -> bool:
    normalized_query = query.strip().lower()
    return any(word in normalized_query for word in PRODUCT_KEYWORDS)


# -------------------------------------
# STEP 2 — LLM CLASSIFIER
# -------------------------------------
def classify_intent_with_llm(query: str) -> str:
    prompt = f"""
        You are an intent classifier.
        Classify the user query as either TRAVEL or NON_TRAVEL.
        Return ONLY TRAVEL or NON_TRAVEL.

        Query:
        {query}
    """

    response = call_llm(prompt, obs=None)

    # Handle LangChain/OpenAI style response objects
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    return response_text.strip().upper()  # normalize output

# -------------------------------------
# MAIN FUNCTION
# -------------------------------------
def validate_product_intent(query: str) -> Tuple[bool, str]:
    """
    Returns (is_travel: bool, intent: str)
    """

    print("INTENT CHECK STARTED")

    # Normalize query
    normalized_query = query.strip().lower()

    # STEP 1 — Keyword check
    if keyword_check(normalized_query):
        print("KEYWORD MATCHED")
        return True, "TRAVEL"

    # STEP 2 — LLM fallback
    try:
        print("CALLING LLM FOR INTENT")
        intent = classify_intent_with_llm(normalized_query)
        print("LLM INTENT RESULT:", intent)
    except Exception as e:
        print("Intent classifier failed:", e)
        return False, "NON_TRAVEL"

    if intent == "TRAVEL":
        return True, "TRAVEL"

    return False, "NON_TRAVEL"