import os
import weaviate
from weaviate.classes.generate import GenerativeConfig


client = weaviate.connect_to_local(
    headers={
        "X-Cohere-Api-Key": os.getenv("COHERE_API_KEY"),
        "X-Anthropic-Api-Key": os.getenv("ANTHROPIC_API_KEY"),
    },
)

chunks = client.collections.use("Chunks")

rag_config = GenerativeConfig.anthropic(
    model="claude-3-5-haiku-latest"
)

response = chunks.generate.hybrid(
    query="collection aliases in Weaviate Python",
    limit=5,
    grouped_task="How do I use collection aliases in Weaviate? Can you show me a Python example? Cite the source URLs please.",
    generative_provider=rag_config
)

print(response.generative.text)

for o in response.objects:
    print(o.properties["path"])

client.close()
