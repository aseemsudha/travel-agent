import random

PROMPT_VERSIONS = [
    "agent_prompt_v1",
    "agent_prompt_v2"
]

def choose_prompt():
    return random.choice(PROMPT_VERSIONS)