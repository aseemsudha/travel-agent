import os

# -----------------------------
# Application Identity
# -----------------------------

APP_NAME = os.getenv(
    "APP_NAME",
    "travel-agent"
)

DOMAIN = os.getenv(
    "DOMAIN",
    "travel"
)

# -----------------------------
# Vector Database
# -----------------------------

COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION",
    "travel_knowledge"
)

CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    "chroma"
)

# -----------------------------
# Models
# -----------------------------

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

EMBEDDING_DIMENSION = int(
    os.getenv("EMBEDDING_DIMENSION", 384)
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "gemini-2.5-flash"
)

TEMPERATURE = float(
    os.getenv("TEMPERATURE", 0)
)

# -----------------------------
# Retrieval
# -----------------------------

TOP_K = int(
    os.getenv("TOP_K", 5)
)

# -----------------------------
# Agent
# -----------------------------

RECURSION_LIMIT = int(
    os.getenv("RECURSION_LIMIT", 10)
)

DEFAULT_PREFERENCE = os.getenv(
    "DEFAULT_PREFERENCE",
    "balanced"
)

# -----------------------------
# Paths
# -----------------------------

KNOWLEDGE_DIR = os.getenv(
    "KNOWLEDGE_DIR",
    "knowledge"
)

CHUNK_SIZE = int(
    os.getenv("CHUNK_SIZE", 300)
)

# -----------------------------
# Observability
# -----------------------------
ENABLE_OBSERVABILITY = True