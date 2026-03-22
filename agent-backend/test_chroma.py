from core.vector_db import add_knowledge

add_knowledge(
    ["Test destination: Paris"],
    [{"source": "test"}]
)

print("Test write completed")