from core.llm import call_llm


def improve_answer(user_query, answer, evaluation_feedback, knowledge_context):

    prompt = f"""
        You are an AI assistant improving a previous answer.

        User Question:
        {user_query}

        Previous Answer:
        {answer}

        Evaluation Feedback:
        {evaluation_feedback}

        Knowledge Context:
        {knowledge_context}

        Your task:
        Improve the previous answer based on the feedback.

        Rules:
        - Fix any incorrect information
        - Add missing useful details
        - Avoid hallucination
        - Keep answer concise and helpful

        Return only the improved answer.
    """

    improved_answer = call_llm(prompt)

    return improved_answer