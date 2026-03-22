import os
from dotenv import load_dotenv

load_dotenv()


# Toggle
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "true").lower() == "true"

# AI Studio
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")