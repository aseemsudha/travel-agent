from core.llm import call_llm


def evaluate_answer(user_query, answer, knowledge_context):

    prompt = f"""
        You are an AI system evaluator.

        Evaluate the quality of an AI assistant's answer.

        User Question:
        {user_query}

        Answer:
        {answer}

        Knowledge Context:
        {knowledge_context}

        Evaluate based on:

        1. Relevance to the question
        2. Correctness based on knowledge
        3. Completeness
        4. Hallucination risk

        Return a JSON response:

        {{
            "relevance_score": 1-10,
            "correctness_score": 1-10,
            "completeness_score": 1-10,
            "hallucination_risk": "low | medium | high",
            "feedback": "short explanation"
        }}
    """

    try:
        evaluation = json.loads(response)
    except:
        evaluation = {
            "relevance_score": 0,
            "correctness_score": 0,
            "completeness_score": 0,
            "hallucination_risk": "unknown",
            "feedback": "Failed to parse evaluation"
        }

    return evaluation