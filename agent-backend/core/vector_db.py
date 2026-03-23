import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import os
from app_config import EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_PATH


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

persist_dir = os.path.join(BASE_DIR, "chroma")
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

    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata or {}],
        ids=[str(uuid.uuid4())]
    )

    print("Memory stored:", text)
    print("Memory count:", collection.count())

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