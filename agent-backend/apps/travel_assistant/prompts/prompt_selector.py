import random

PROMPT_VERSIONS = [
    "agent_prompt_v1",
    "agent_prompt_v2",
    "agent_prompt_v3"
]

def choose_prompt():
    # selected = random.choice(PROMPT_VERSIONS)
    selected = "agent_prompt_v1"
    print(
        "[PROMPT SELECTOR]",
        selected
    )
    return selected