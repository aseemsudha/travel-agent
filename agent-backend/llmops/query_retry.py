from core.llm import call_llm

def generate_retry_query(user_query):

    prompt = f"""
        Improve the following travel search query so that a knowledge database can return better results.

        Query:
        {user_query}

        Improved Search Query:
    """

    response = call_llm(prompt)

    return response.strip()