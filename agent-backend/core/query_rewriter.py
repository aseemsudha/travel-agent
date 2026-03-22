from core.llm import call_llm

def rewrite_query(user_query):

    prompt = f"""
Convert the following user question into a concise search query
that will help retrieve travel knowledge.

User Question:
{user_query}

Search Query:
"""

    rewritten_query = call_llm(prompt)

    return rewritten_query.strip()