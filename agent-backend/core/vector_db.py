import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import os


# -----------------------------
# Initialize embedding model
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# Initialize Chroma client
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

persist_dir = os.path.join(BASE_DIR, "chroma")

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
        name="travel_knowledge"
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