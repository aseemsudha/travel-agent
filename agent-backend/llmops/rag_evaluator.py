def is_retrieval_weak(results):

    if not results:
        return True

    if len(results) < 2:
        return True

    return False