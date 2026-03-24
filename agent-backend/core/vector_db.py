import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import os
from app_config import EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_PATH, MEMORY_TTL_DAYS, MEMORY_SUMMARY_BATCH_SIZE, MEMORY_MAX_RECORDS
import time


# -----------------------------
# Initialize embedding model
# -----------------------------
model = SentenceTransformer(
    EMBEDDING_MODEL
)

# -----------------------------
# Initialize Chroma client
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

persist_dir = os.path.join(BASE_DIR, CHROMA_PATH)
print("BASE_DIR path:", BASE_DIR)

print("Chroma path:", persist_dir)
print("Exists:", os.path.exists(persist_dir))

print("Chroma will be stored at:", persist_dir)

client = chromadb.PersistentClient(
    path=persist_dir,
    settings=Settings(
        anonymized_telemetry=False
    )
)

# -----------------------------
# Get or create collection
# -----------------------------
def get_knowledge_collection():
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )
    return collection


# -----------------------------
# Add knowledge to vector DB
# -----------------------------
def add_knowledge(texts, metadatas):

    collection = get_knowledge_collection()

    embeddings = model.encode(texts).tolist()

    ids = [str(uuid.uuid4()) for _ in texts]

    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print("Knowledge stored and persisted to disk")


# -----------------------------
# Search knowledge
# -----------------------------
def search_knowledge(query, k=3, source_filter=None):

    collection = get_knowledge_collection()

    query_embedding = model.encode(query).tolist()

    if source_filter:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"source": source_filter}
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    knowledge_results = []

    for doc, meta in zip(documents, metadatas):
        knowledge_results.append({
            "text": doc,
            "metadata": meta
        })

    return knowledge_results


def get_memory_collection():

    collection = client.get_or_create_collection(
        name="user_memory"
    )

    return collection

def save_memory(text, metadata=None):

    collection = get_memory_collection()

    embedding = model.encode(text).tolist()

    metadata = metadata or {}

    metadata.update({
        "timestamp": time.time(),
        "ttl_days": MEMORY_TTL_DAYS
    })

    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[str(uuid.uuid4())]
    )

    print("Memory stored:", text)
    print("Memory count:", collection.count())

# def save_memory(text, metadata=None):
    
#     collection = get_memory_collection()

#     embedding = model.encode(text).tolist()

#     collection.add(
#         documents=[text],
#         embeddings=[embedding],
#         metadatas=[metadata or {}],
#         ids=[str(uuid.uuid4())]
#     )

#     print("Memory stored:", text)
#     print("Memory count:", collection.count())

def search_memory(query, k=3):

    collection = get_memory_collection()

    print("Memory count:", collection.count())

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )

    documents = results.get("documents", [[]])[0]

    print("Retrieved memory:", documents)

    return documents

def get_memory_count():

    collection = get_memory_collection()

    count = collection.count()

    print("Memory count:", count)

    return count

def summarize_memories(memories):

    if not memories:
        return None

    summary_text = "Summary of past user memories:\n"

    for m in memories:
        summary_text += f"- {m}\n"

    return summary_text

def delete_old_memories(ids):

    collection = get_memory_collection()

    collection.delete(ids=ids)

    print("Deleted old memories:", len(ids))

def get_oldest_memories(session_id):

    collection = get_memory_collection()

    results = collection.get(
        where={
            "session_id": session_id
        },
        limit=MEMORY_SUMMARY_BATCH_SIZE,
        include=["documents", "metadatas", "ids"]
    )

    documents = results.get("documents", [])
    ids = results.get("ids", [])

    return documents, ids

    

# -----------------------------
# Maintain memory limits
# -----------------------------
def maintain_memory(session_id=None):
    """
    Summarize and delete old memories if memory count exceeds threshold.
    If session_id is provided, only consider that session.
    """
    collection = get_memory_collection()

    # Retrieve all memories or session-specific memories
    if session_id:
        results = collection.get(
            where={"session_id": session_id},
            limit=MEMORY_SUMMARY_BATCH_SIZE,
            include=["documents", "metadatas"]
        )
    else:
        results = collection.get(
            limit=MEMORY_SUMMARY_BATCH_SIZE,
            include=["documents", "metadatas"]
        )

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    memory_count = len(documents)
    print("Memory count:", memory_count)

    if memory_count <= MEMORY_MAX_RECORDS:
        return  # No action needed

    print("Memory limit exceeded. Running summarization...")

    # Summarize oldest memories
    summary_text = "Summary of past user memories:\n"
    for doc in documents:
        summary_text += f"- {doc}\n"

    # Store summary as a new memory
    if session_id:
        summary_metadata = {"session_id": session_id, "type": "summary"}
    else:
        summary_metadata = {"type": "summary"}

    # Add summary without triggering another maintenance loop
    collection.add(
        documents=[summary_text],
        embeddings=[model.encode(summary_text).tolist()],
        metadatas=[summary_metadata],
        ids=[str(uuid.uuid4())]
    )

    # Delete old memories
    ids_to_delete = [md["id"] for md in metadatas if "id" in md]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} old memories.")

def store_memory(text, metadata):
    """
    Add a memory and maintain limits.
    """
    collection = get_memory_collection()
    memory_id = str(uuid.uuid4())

    full_metadata = metadata.copy()
    full_metadata.update({
        "timestamp": time.time(),
        "ttl_days": MEMORY_TTL_DAYS,
        "id": memory_id
    })

    embedding = model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[full_metadata],
        ids=[memory_id]
    )

    print("Memory stored:", text)
    print("Memory count:", collection.count())

    # Trigger maintenance
    maintain_memory(full_metadata.get("session_id"))