from core.llm import call_llm


CRITIC_PROMPT = """
You are a strict AI critic.

Your job is to evaluate and improve the assistant's answer.

Check:
1. Is the answer correct?
2. Is it complete?
3. Was the correct tool used?
4. Can the answer be improved?

If the answer is good:
Respond with:
FINAL: <same answer>

If the answer needs improvement:
Respond with:
IMPROVED: <better answer>

Be concise but improve clarity and usefulness.
"""


def run_critic(query, answer, obs=None):
    prompt = f"""
{CRITIC_PROMPT}

User Query:
{query}

Assistant Answer:
{answer}
"""

    response = call_llm(prompt, obs)

    # -------------------------------
    # PARSE RESPONSE (IMPORTANT)
    # -------------------------------
    if "IMPROVED:" in response:
        return response.split("IMPROVED:")[-1].strip()

    if "FINAL:" in response:
        return response.split("FINAL:")[-1].strip()

    # fallback (LLM misbehaves)
    return response.strip()
    