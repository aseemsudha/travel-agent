from langsmith import traceable

# Safe wrapper

def trace(name):

    def decorator(func):

        @traceable(name=name)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator