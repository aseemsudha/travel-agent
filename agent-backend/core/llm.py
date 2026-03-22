from google import genai
import os
from dotenv import load_dotenv
import time
import requests
import subprocess

# ✅ LLMOps Observability
from llmops.observability import Observability as LLMObs

from langsmith import traceable


# -------------------------------
# CONFIG
# -------------------------------

load_dotenv(dotenv_path=".env")

USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "asia-south1")

MODEL_AI_STUDIO = "gemini-2.5-flash"
MODEL_VERTEX = "gemini-2.5-flash"


# -------------------------------
# OBSERVABILITY
# -------------------------------

llm_obs = LLMObs()


# -------------------------------
# TOKEN HELPER
# -------------------------------

def get_access_token():

    result = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception("Failed to get GCP access token")

    return result.stdout.strip()


# -------------------------------
# VERTEX REST CALL
# -------------------------------

def call_vertex(prompt: str):

    token = get_access_token()

    # response = requests.post(
    #     url,
    #     headers=headers,
    #     json=data,
    #     timeout=60
    # )

    # print("Vertex status:", response.status_code)
    # print("Vertex response:", response.text)

    url = (
        f"https://{GCP_LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{GCP_PROJECT_ID}/locations/{GCP_LOCATION}/"
        f"publishers/google/models/{MODEL_VERTEX}:generateContent"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    print("Vertex URL:", url)

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60
    )

    print("Vertex status:", response.status_code)
    print("Vertex response:", response.text)

    if response.status_code != 200:
        raise Exception(response.text)

    result = response.json()

    text = result["candidates"][0]["content"]["parts"][0]["text"]

    return text


# -------------------------------
# AI STUDIO CALL
# -------------------------------

def call_ai_studio(prompt: str):

    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model=MODEL_AI_STUDIO,
        contents=prompt
    )

    return response.text


# -------------------------------
# PROXY CLIENT (KEY PART)
# -------------------------------

class ModelProxy:

    def generate_content(self, model=None, contents=None, **kwargs):

        start_time = time.time()

        provider = "VERTEX_AI" if USE_VERTEX_AI else "AI_STUDIO"

        print(f"\n🔹 LLM Provider: {provider}")

        try:

            if USE_VERTEX_AI:

                output = call_vertex(contents)

            else:

                output = call_ai_studio(contents)

            latency = round(time.time() - start_time, 3)

            llm_obs.track_event({
                "type": "llm_call",
                "provider": provider,
                "prompt": str(contents)[:500],
                "response": output[:500],
                "latency": latency,
                "status": "success"
            })

            class Response:
                text = output

            return Response()

        except Exception as e:

            latency = round(time.time() - start_time, 3)

            llm_obs.track_event({
                "type": "llm_call",
                "provider": provider,
                "prompt": str(contents)[:500],
                "error": str(e),
                "latency": latency,
                "status": "error"
            })

            raise Exception(f"LLM failed ({provider}): {str(e)}")


class ClientProxy:

    def __init__(self):

        self.models = ModelProxy()


# -------------------------------
# GLOBAL CLIENT (SAME INTERFACE)
# -------------------------------

client = ClientProxy()

# -------------------------------
# BACKWARD COMPATIBILITY
# -------------------------------

@traceable(name="call_llm")
def call_llm(prompt: str, obs=None) -> str:
    """
    Compatibility wrapper so existing code using call_llm() keeps working.
    """

    response = client.models.generate_content(
        model="any",
        contents=prompt
    )

    return response.text







# from google import genai
# import os
# from dotenv import load_dotenv
# import time
# # ✅ LLMOps Observability (keep this)
# from llmops.observability import Observability as LLMObs


# # -------------------------------
# # CONFIG
# # -------------------------------
# load_dotenv(dotenv_path=".env")

# api_key = os.getenv("GOOGLE_API_KEY")
# client = genai.Client(api_key=api_key)
# model_name = "gemini-2.5-flash"

# # -------------------------------
# # GLOBAL LLM OBS (LLMOps)
# # -------------------------------
# llm_obs = LLMObs()

# # -------------------------------
# # LLM CALL
# # -------------------------------
# def call_llm(prompt: str, obs: LLMObs = None) -> str:
#     """
#     Calls the LLM with optional LLMOps observability tracking.
#     """
#     start_time = time.time()
#     try:
#         response = client.models.generate_content(
#             model=model_name,
#             contents=prompt
#         )
#         output = response.text

#         # Track with LLMOps observability
#         if obs:
#             obs.track_event({
#                 "type": "llm_call",
#                 "prompt": prompt[:500],
#                 "response": output[:500],
#                 "latency": round(time.time() - start_time, 3),
#                 "status": "success"
#             })

#         return output

#     except Exception as e:
#         if obs:
#             obs.track_event({
#                 "type": "llm_call",
#                 "prompt": prompt[:500],
#                 "error": str(e),
#                 "latency": round(time.time() - start_time, 3),
#                 "status": "error"
#             })
#         raise Exception(f"LLM failed: {str(e)}")