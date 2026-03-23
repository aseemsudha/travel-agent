from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


model = SentenceTransformer("all-MiniLM-L6-v2")

memory_texts = []

dimension = 384
index = faiss.IndexFlatL2(dimension)


def add_memory(text):

    embedding = model.encode([text])
    index.add(np.array(embedding))

    memory_texts.append(text)

def search_memory_faiss(query, k=3):

    if len(memory_texts) == 0:
        return []

    query_embedding = model.encode([query])

    distances, indices = index.search(np.array(query_embedding), k)

    results = []

    for idx in indices[0]:
        if idx < len(memory_texts):
            results.append(memory_texts[idx])

    # remove duplicates
    unique_results = list(dict.fromkeys(results))

    return unique_results
