# tools.py

import requests
import os
from datetime import datetime
from core.knowledge_rag import search_knowledge

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
    city = tool_input.get("city", "")
    category = tool_input.get("category", "tourist places")
    preference = tool_input.get("preference", "balanced")

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

        results.append({
            "name": name,
            "rating": rating,
            "reviews": reviews,
            "crowd": crowd_data["crowd_level"],
            "wait_time": wait_data["estimated_wait_minutes"],
            "score": round(score, 2)
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
def google_maps_search(tool_input: dict):
    query = tool_input.get("query", "")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    data = safe_get(url, {"query": query, "key": GOOGLE_MAPS_API_KEY})

    if "error" in data:
        return {"error": data["error"]}

    results = []

    for place in data.get("results", [])[:5]:
        results.append({
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating")
        })

    return {"query": query, "results": results}


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
def retrieve_travel_knowledge(tool_input: dict):
    query = tool_input.get("query", "")

    results = search_knowledge(query)

    if not results:
        return {"result": "No knowledge found"}

    return {
        "query": query,
        "results": [r["text"] for r in results]
    }



# def smart_temple_recommender(tool_input):

#     import requests
#     import os

#     GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

#     # ---------------------------
#     # 1. Parse Input
#     # ---------------------------
#     if isinstance(tool_input, dict):
#         city = tool_input.get("city", "")
#         preference = tool_input.get("preference", "balanced")
#     else:
#         city = str(tool_input)
#         preference = "balanced"

#     # ---------------------------
#     # 2. Google Places API
#     # ---------------------------
#     url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

#     query = f"hindu temples in {city}"

#     params = {
#         "query": query,
#         "key": GOOGLE_MAPS_API_KEY
#     }

#     response = requests.get(url, params=params)
#     data = response.json()

#     raw_places = data.get("results", [])[:8]

#     results = []

#     # ---------------------------
#     # 3. Process Places
#     # ---------------------------
#     for place in raw_places:

#         try:
#             name = place.get("name")
#             rating = place.get("rating", 4.0)
#             reviews = place.get("user_ratings_total", 500)

#             lat = place["geometry"]["location"]["lat"]
#             lng = place["geometry"]["location"]["lng"]

#             # ---------------------------
#             # Crowd Estimation
#             # ---------------------------
#             if reviews > 20000:
#                 crowd = "Very High"
#             elif reviews > 10000:
#                 crowd = "High"
#             elif reviews > 3000:
#                 crowd = "Medium"
#             else:
#                 crowd = "Low"

#             # ---------------------------
#             # Wait Time
#             # ---------------------------
#             wait_map = {
#                 "Low": 10,
#                 "Medium": 25,
#                 "High": 45,
#                 "Very High": 75
#             }

#             wait_time = wait_map.get(crowd, 20)

#             # ---------------------------
#             # Scoring Logic
#             # ---------------------------
#             score = rating * 2
#             score -= reviews / 10000

#             if preference.lower() == "quiet":
#                 if crowd == "Low":
#                     score += 3
#                 elif crowd == "Medium":
#                     score += 1
#                 else:
#                     score -= 2

#             elif preference.lower() == "crowded":
#                 if crowd in ["High", "Very High"]:
#                     score += 3

#             # ---------------------------
#             # Reason
#             # ---------------------------
#             if crowd == "Low":
#                 reason = "Peaceful and less crowded"
#             elif crowd == "Medium":
#                 reason = "Moderate crowd, manageable"
#             else:
#                 reason = "Popular temple, can be crowded"

#             results.append({
#                 "name": name,
#                 "rating": rating,
#                 "reviews": reviews,
#                 "crowd": crowd,
#                 "wait_time": wait_time,
#                 "lat": lat,
#                 "lng": lng,
#                 "score": round(score, 2),
#                 "why": reason
#             })

#         except Exception:
#             continue

#     # ---------------------------
#     # 4. Sort & Return
#     # ---------------------------
#     results = sorted(results, key=lambda x: x["score"], reverse=True)

#     return results[:5]



# def get_religious_places(city: str):

#     places_db = {
#         "kerala": [
#             "Sabarimala Temple",
#             "Guruvayur Temple",
#             "Padmanabhaswamy Temple",
#             "Chottanikkara Temple",
#             "Vaikom Mahadeva Temple"
#         ],
#         "varanasi": [
#             "Kashi Vishwanath Temple",
#             "Durga Temple",
#             "Sankat Mochan Temple",
#             "Tulsi Manas Temple"
#         ]
#     }

#     return places_db.get(city.lower(), ["Local temple 1", "Local temple 2"])



# -------------------------------
# 4. Detect festivals in city
# -------------------------------
# def festival_detector(tool_input):

#     if isinstance(tool_input, dict):
#         city = tool_input.get("city", "")
#     else:
#         city = extract_value(tool_input)

#     query = f"festivals in {city} India upcoming"

#     url = "https://serpapi.com/search.json"

#     params = {
#         "q": query,
#         "api_key": os.getenv("SERPAPI_KEY")
#     }

#     response = requests.get(url, params=params)
#     data = response.json()

#     snippets = []

#     for result in data.get("organic_results", [])[:5]:
#         snippets.append(result.get("snippet", ""))

#     return "\n".join(snippets)



