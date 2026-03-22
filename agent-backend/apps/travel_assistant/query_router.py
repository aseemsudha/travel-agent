from core.llm import call_llm

def route_query(user_query):

    prompt = f"""
    Classify the user's query into one category.

    Categories:

    memory
    knowledge
    itinerary
    crowd
    general

    User Query:
    {user_query}

    Only return the category name.
    """

    response = call_llm(prompt)

    return response.strip().lower()