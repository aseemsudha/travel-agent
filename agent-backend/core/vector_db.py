import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import os
from app_config import EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_PATH, MEMORY_TTL_DAYS, MEMORY_SUMMARY_BATCH_SIZE, MEMORY_MAX_RECORDS, MEMORY_DELETE_EXPIRED, MEMORY_TTL_DAYS
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

def maintain_memory(session_id=None, auto_delete_expired=MEMORY_DELETE_EXPIRED):
    """
    Maintain user memories:
    1. Delete expired memories (TTL-based) if auto_delete_expired is True
    2. Summarize oldest memories if memory count exceeds MEMORY_MAX_RECORDS
    3. Works for a specific session_id if provided, else all memories
    """
    collection = get_memory_collection()
    current_time = time.time()

    # -----------------------
    # Fetch memories
    # -----------------------
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

    # Ensure each memory has an 'id' in metadata
    for md in metadatas:
        if "id" not in md:
            md["id"] = str(uuid.uuid4())

    # -----------------------
    # Delete expired memories
    # -----------------------
    if auto_delete_expired:
        expired_ids = []
        for meta in metadatas:
            ttl_days = meta.get("ttl_days", MEMORY_TTL_DAYS)
            timestamp = meta.get("timestamp", current_time)
            if (current_time - timestamp) > ttl_days * 86400:  # convert days to seconds
                expired_ids.append(meta["id"])

        if expired_ids:
            collection.delete(ids=expired_ids)
            print(f"Deleted {len(expired_ids)} expired memories.")

        # Refresh documents/metadatas after deletion
        documents = [doc for doc, meta in zip(documents, metadatas) if meta["id"] not in expired_ids]
        metadatas = [meta for meta in metadatas if meta["id"] not in expired_ids]

    memory_count = len(documents)
    print(f"Memory count (after TTL cleanup) for session {session_id}: {memory_count}")

    # -----------------------
    # Summarize oldest memories if over limit
    # -----------------------
    if memory_count > MEMORY_MAX_RECORDS:
        print("Memory limit exceeded. Creating summary...")

        # Create summary text
        summary_text = "Summary of past user memories:\n"
        for doc in documents:
            summary_text += f"- {doc}\n"

        # Prepare summary metadata
        summary_metadata = {"type": "summary", "timestamp": current_time, "ttl_days": MEMORY_TTL_DAYS}
        if session_id:
            summary_metadata["session_id"] = session_id
        summary_id = str(uuid.uuid4())
        summary_metadata["id"] = summary_id

        # Store summary as new memory
        collection.add(
            documents=[summary_text],
            embeddings=[model.encode(summary_text).tolist()],
            metadatas=[summary_metadata],
            ids=[summary_id]
        )
        print("Summary stored as a new memory.")

        # Delete old memories that were summarized
        old_ids = [meta["id"] for meta in metadatas]
        if old_ids:
            collection.delete(ids=old_ids)
            print(f"Deleted {len(old_ids)} old memories after summarization.")


def store_memory(text, metadata):
    """
    Store a memory and trigger maintenance
    - text: memory content
    - metadata: dict, must include "session_id" for session-specific memory
    """
    collection = get_memory_collection()
    full_metadata = metadata.copy() if metadata else {}
    full_metadata.update({
        "timestamp": time.time(),
        "ttl_days": full_metadata.get("ttl_days", MEMORY_TTL_DAYS)
    })

    collection.add(
        documents=[text],
        embeddings=[model.encode(text).tolist()],
        metadatas=[full_metadata],
        ids=[str(uuid.uuid4())]
    )

    print("Memory stored:", text)
    print("Memory count:", collection.count())

    # Maintain memory after adding
    maintain_memory(session_id=full_metadata.get("session_id"), auto_delete_expired=True)