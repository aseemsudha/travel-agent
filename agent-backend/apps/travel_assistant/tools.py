# tools.py

import requests
import os
from datetime import datetime
import time
# from core.knowledge_rag import search_knowledge
from core.vector_db import search_knowledge
from app_config import DEFAULT_PREFERENCE

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# =====================================================
# UTILS
# =====================================================
def safe_get(url, params):
    try:
        response = requests.get(url, params=params, timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# =====================================================
# CORE RECOMMENDER
# =====================================================
def smart_place_recommender(tool_input: dict):
    print("SSSRunninggggggggggggggggggggggggggggggg")
    city = tool_input.get("city", "")
    category = tool_input.get("category", "tourist places")
    preference = tool_input.get("preference", DEFAULT_PREFERENCE)

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{category} in {city}"

    data = safe_get(url, {"query": query, "key": GOOGLE_MAPS_API_KEY})

    if "error" in data:
        return {"error": data["error"]}

    places = data.get("results", [])[:8]
    results = []

    for place in places:
        name = place.get("name")
        rating = place.get("rating", 4.0)
        reviews = place.get("user_ratings_total", 1000)

        crowd_data = estimate_crowd({
            "place": name,
            "rating": rating,
            "reviews": reviews
        })

        wait_data = temple_wait_time({
            "place": name,
            "crowd_level": crowd_data["crowd_level"]
        })

        score = rating * 2 - (reviews / 10000)

        if preference.lower() == "quiet":
            score += 2 if crowd_data["crowd_level"] == "Low" else -1
        elif preference.lower() == "crowded":
            score += 2 if crowd_data["crowd_level"] in ["High", "Very High"] else 0

        # results.append({
        #     "name": name,
        #     "rating": rating,
        #     "reviews": reviews,
        #     "crowd": crowd_data["crowd_level"],
        #     "wait_time": wait_data["estimated_wait_minutes"],
        #     "score": round(score, 2)
        # })

        location = place.get("geometry", {}).get("location", {})

        lat = location.get("lat")
        lng = location.get("lng")

        results.append({
            "name": name,
            "rating": rating,
            "reviews": reviews,
            "crowd": crowd_data["crowd_level"],
            "wait_time": wait_data["estimated_wait_minutes"],
            "score": round(score, 2),
            "lat": lat,
            "lng": lng
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return {
        "city": city,
        "category": category,
        "results": results[:5]
    }


# =====================================================
# SPECIALIZED WRAPPERS
# =====================================================
def smart_temple_recommender(tool_input: dict):
    tool_input["category"] = "hindu temples"
    return smart_place_recommender(tool_input)


def smart_food_recommender(tool_input: dict):
    tool_input["category"] = "restaurants"
    return smart_place_recommender(tool_input)


def smart_hotel_recommender(tool_input: dict):
    tool_input["category"] = "hotels"
    return smart_place_recommender(tool_input)


# =====================================================
# CROWD + WAIT
# =====================================================
def estimate_crowd(tool_input: dict):
    rating = tool_input.get("rating", 4.0)
    reviews = tool_input.get("reviews", 1000)

    hour = datetime.now().hour
    weekday = datetime.now().weekday()

    score = 0

    if rating > 4.5:
        score += 2
    if reviews > 5000:
        score += 2

    if 6 <= hour <= 10:
        score += 2
    elif 10 <= hour <= 16:
        score += 1

    if weekday >= 5:
        score += 2

    if score <= 2:
        level = "Low"
    elif score <= 4:
        level = "Medium"
    elif score <= 6:
        level = "High"
    else:
        level = "Very High"

    return {"crowd_level": level}


def temple_wait_time(tool_input: dict):
    crowd = tool_input.get("crowd_level", "Medium")

    mapping = {
        "Low": 10,
        "Medium": 25,
        "High": 45,
        "Very High": 90
    }

    return {"estimated_wait_minutes": mapping.get(crowd, 30)}


# =====================================================
# GOOGLE SEARCH
# =====================================================
# def google_maps_search(tool_input: dict):
#     query = tool_input.get("query", "")

#     url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
#     data = safe_get(url, {"query": query, "key": GOOGLE_MAPS_API_KEY})

#     if "error" in data:
#         return {"error": data["error"]}

#     results = []

#     for place in data.get("results", [])[:5]:
#         results.append({
#             "name": place.get("name"),
#             "address": place.get("formatted_address"),
#             "rating": place.get("rating")
#         })

#     return {"query": query, "results": results}

def google_maps_search(tool_input: dict):

    query = tool_input.get("query", "")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    data = safe_get(
        url,
        {
            "query": query,
            "key": GOOGLE_MAPS_API_KEY
        }
    )

    if not data or "error" in data:
        return {
            "error": data.get("error", "Google Maps API failed")
        }

    results = []

    for place in data.get("results", [])[:5]:

        location = (
            place.get("geometry", {})
            .get("location", {})
        )

        lat = location.get("lat")
        lng = location.get("lng")

        if lat is None or lng is None:
            continue

        results.append({
            "name": place.get("name"),
            "lat": float(lat),
            "lng": float(lng)
        })

    return {
        "status": "success",
        "results": results
    }


# =====================================================
# FESTIVALS
# =====================================================
def festival_detector(tool_input: dict):
    city = tool_input.get("city", "").lower()

    festivals_db = {
        "kerala": ["Thrissur Pooram", "Onam", "Attukal Pongala"],
        "varanasi": ["Dev Deepawali", "Mahashivratri"]
    }

    return {"city": city, "festivals": festivals_db.get(city, [])}


# =====================================================
# TRAVEL PLAN
# =====================================================
def suggest_travel_plan(tool_input: dict):
    city = tool_input.get("city", "")
    interest = tool_input.get("interest", "general")

    return {
        "city": city,
        "plan": f"Suggested itinerary in {city} focusing on {interest}"
    }


# =====================================================
# RAG TOOL
# =====================================================
import time
from core.vector_db import search_knowledge


# =====================================================
# RAG TOOL
# =====================================================
def retrieve_travel_knowledge(tool_input: dict):

    query = tool_input.get("query", "")
    k = tool_input.get("k", 3)

    # -----------------------------
    # Validate input
    # -----------------------------
    if not query:

        return {
            "status": "error",
            "message": "Query is required",
            "results": []
        }

    start_time = time.time()

    # -----------------------------
    # Safe retrieval
    # -----------------------------
    try:

        results = search_knowledge(query, k=k)

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
            "results": []
        }

    latency = int((time.time() - start_time) * 1000)

    # -----------------------------
    # No results case
    # -----------------------------
    if not results:

        return {
            "status": "success",
            "query": query,
            "documents_found": 0,
            "latency_ms": latency,
            "results": []
        }

    # -----------------------------
    # Format results
    # -----------------------------
    formatted_results = []

    for r in results:

        formatted_results.append(
            {
                "text": r.get("text", ""),
                "source": (
                    r.get("metadata", {}).get("source", "unknown")
                    if isinstance(r.get("metadata"), dict)
                    else "unknown"
                )
            }
        )

    # -----------------------------
    # Final response
    # -----------------------------
    return {
        "status": "success",
        "query": query,
        "documents_found": len(formatted_results),
        "latency_ms": latency,
        "results": formatted_results
    }



