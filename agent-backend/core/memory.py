from app_config import SHORT_TERM_MEMORY_LIMIT

memory_store = {}


def get_memory(session_id):

    history = memory_store.get(session_id, [])

    return history[-SHORT_TERM_MEMORY_LIMIT:]


def save_memory(session_id, message):

    if session_id not in memory_store:
        memory_store[session_id] = []

    memory_store[session_id].append(message)

    # keep only last N messages

    if len(memory_store[session_id]) > SHORT_TERM_MEMORY_LIMIT:

        memory_store[session_id] = memory_store[session_id][
            -SHORT_TERM_MEMORY_LIMIT:
        ]








# memory_store = {}

# def get_memory(session_id):
#     return memory_store.get(session_id, [])


# def save_memory(session_id, message):

#     if session_id not in memory_store:
#         memory_store[session_id] = []

#     memory_store[session_id].append(message)