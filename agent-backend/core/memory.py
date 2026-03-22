memory_store = {}

def get_memory(session_id):
    return memory_store.get(session_id, [])


def save_memory(session_id, message):

    if session_id not in memory_store:
        memory_store[session_id] = []

    memory_store[session_id].append(message)