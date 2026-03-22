# tool_registry.py

from apps.travel_assistant.tools import (
    smart_place_recommender,
    smart_temple_recommender,
    smart_food_recommender,
    smart_hotel_recommender,
    estimate_crowd,
    suggest_travel_plan,
    temple_wait_time,
    festival_detector,
    google_maps_search,
    retrieve_travel_knowledge
)

# =====================================================
# TOOL REGISTRY WITH METADATA
# =====================================================

TOOLS = {
    "smart_place_recommender": {
        "func": smart_place_recommender,
        "description": "Generic fallback tool. Use ONLY when category is unclear.",
        "input_schema": ["city", "category", "preference"]
    },
    "smart_temple_recommender": {
        "func": smart_temple_recommender,
        "description": "PRIMARY tool for temple recommendations. Use for any temple-related query.",
        "input_schema": ["city", "preference"]
    },
    "smart_food_recommender": {
        "func": smart_food_recommender,
        "description": "PRIMARY tool for restaurants, cafes, and food-related queries.",
        "input_schema": ["city", "preference"]
    },
    "smart_hotel_recommender": {
        "func": smart_hotel_recommender,
        "description": "PRIMARY tool for hotels and stay recommendations.",
        "input_schema": ["city", "preference"]
    },
    "estimate_crowd": {
        "func": estimate_crowd,
        "description": "Estimate crowd level at a place based on rating, reviews, and time.",
        "input_schema": ["place", "rating", "reviews"]
    },
    "temple_wait_time": {
        "func": temple_wait_time,
        "description": "Estimate waiting time based on crowd level.",
        "input_schema": ["place", "crowd_level"]
    },
    "suggest_travel_plan": {
        "func": suggest_travel_plan,
        "description": "Generate a travel itinerary based on city and user interests.",
        "input_schema": ["city", "interest"]
    },
    "festival_detector": {
        "func": festival_detector,
        "description": "Find festivals happening in a city.",
        "input_schema": ["city"]
    },
    "google_maps_search": {
        "func": google_maps_search,
        "description": "Search places using Google Maps for general queries.",
        "input_schema": ["query"]
    },
    "retrieve_travel_knowledge": {
        "func": retrieve_travel_knowledge,
        "description": "Retrieve travel-related knowledge using RAG.",
        "input_schema": ["query"]
    }
}


# =====================================================
# SAFE TOOL EXECUTION (IMPORTANT)
# =====================================================
def execute_tool(tool_name, tool_input):
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    tool = TOOLS[tool_name]

    try:
        return tool["func"](tool_input)
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}