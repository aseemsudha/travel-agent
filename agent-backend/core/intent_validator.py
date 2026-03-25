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
# STEP 1 — FAST CHECK
# -------------------------------------

def keyword_check(query: str) -> bool:

    query = query.lower()

    return any(
        word in query
        for word in PRODUCT_KEYWORDS
    )


# -------------------------------------
# STEP 2 — LLM CLASSIFIER
# -------------------------------------

def classify_intent_with_llm(query: str) -> str:

    prompt = f"""
        You are an intent classifier.

        Classify the user query.

        Return ONLY:

        TRAVEL
        or
        NON_TRAVEL

        Query:
        {query}
    """

    response = call_llm(prompt, obs=None)

    # Handle LangChain / OpenAI response objects safely
    if hasattr(response, "content"):
        response_text = response.content
    else:
        response_text = str(response)

    return response_text.strip().upper()


# -------------------------------------
# MAIN FUNCTION
# -------------------------------------

def validate_product_intent(query: str) -> Tuple[bool, str]:

    print("INTENT CHECK STARTED")

    # STEP 1 — keyword

    if keyword_check(query):
        print("KEYWORD MATCHED")

        return True, "TRAVEL"

    # STEP 2 — LLM fallback
    
    try:
        print("CALLING LLM FOR INTENT")
        intent = classify_intent_with_llm(query)
        print("INTENT RESULT:", intent)
    except Exception as e:
        print("Intent classifier failed:", e)
        return False, "NON_TRAVEL"

    if intent == "TRAVEL":

        return True, "TRAVEL"

    return False, "NON_TRAVEL"