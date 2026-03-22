import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from core.vector_db import add_knowledge, search_knowledge, get_knowledge_collection

collection = get_knowledge_collection()



model = SentenceTransformer("all-MiniLM-L6-v2")

knowledge_texts = []
knowledge_metadata = []

dimension = 384
index = faiss.IndexFlatL2(dimension)

###### chroma db  implemented ####
def load_knowledge():

    texts = []
    metadatas = []

    for filename in os.listdir("knowledge"):

        with open(f"knowledge/{filename}") as f:

            doc = f.read()

        chunks = chunk_text(doc)

        for chunk in chunks:

            texts.append(chunk)

            metadatas.append({
                "source": filename
            })

    add_knowledge(texts, metadatas)

    print("Knowledge stored in vector DB:", len(texts))

###### chroma db implemented ####
def search_knowledge(query, source_filter=None):

    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    final_results = []

    for doc, meta, dist in zip(documents, metadatas, distances):

        if source_filter:
            if meta["source"] != source_filter:
                continue

        final_results.append({
            "text": doc,
            "source": meta["source"],
            "distance": dist
        })

    return final_results

def chunk_text(text, chunk_size=300):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end

    return chunks


#### for hybrid search - vecttor+ keyword search ####
def keyword_search(query):

    query_words = query.lower().split()

    results = []

    for text in knowledge_texts:

        for word in query_words:

            if word in text.lower():

                results.append(text)
                break

    return results[:3]