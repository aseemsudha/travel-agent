import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from core.vector_db import add_knowledge, get_knowledge_collection
from app_config import KNOWLEDGE_DIR, TOP_K, CHUNK_SIZE

collection = get_knowledge_collection()



model = SentenceTransformer("all-MiniLM-L6-v2")

knowledge_texts = []
knowledge_metadata = []

dimension = 384
index = faiss.IndexFlatL2(dimension)


def load_knowledge():

    collection = get_knowledge_collection()

    texts = []
    metadatas = []

    print("Loading knowledge from:", KNOWLEDGE_DIR)

    for filename in os.listdir(KNOWLEDGE_DIR):

        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(KNOWLEDGE_DIR, filename)

        print("Processing file:", filename)

        with open(file_path, "r", encoding="utf-8") as f:

            doc = f.read()

        chunks = chunk_text(doc, chunk_size=CHUNK_SIZE)

        print("Chunks created:", len(chunks))

        for chunk in chunks:

            texts.append(chunk)

            metadatas.append({
                "source": filename
            })

    if not texts:

        print("No knowledge found.")
        return

    print("Storing knowledge in vector DB...")

    add_knowledge(texts, metadatas)

    print("Knowledge ingestion completed.")

def chunk_text(text, chunk_size=500, overlap=100):

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


#### for hybrid search - vector+ keyword search ####
def keyword_search(query):

    query_words = query.lower().split()

    results = []

    for text in knowledge_texts:

        for word in query_words:

            if word in text.lower():

                results.append(text)
                break

    return results[:3]

def bootstrap_knowledge():

    collection = get_knowledge_collection()

    count = collection.count()

    print("Knowledge collection count:", count)

    if count == 0:

        print("Knowledge DB is empty. Loading knowledge.")

        load_knowledge()

        count = collection.count()

        print("New knowledge count:", count)

    else:

        print("Knowledge already exists. Skipping ingestion.")