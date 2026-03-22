import json

def fix_tool_input(query, last_output, obs=None):
    from core.llm import call_llm

    prompt = f"""
    Fix the tool input.

    Query: {query}

    Bad Output:
    {last_output}

    Return ONLY valid JSON.
    """

    response = call_llm(prompt, obs)

    try:
        return json.loads(response)
    except:
        return {}