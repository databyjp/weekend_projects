import weaviate
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.util import generate_uuid5
import json
from chonkie import NeuralChunker, TokenChunker
import os
from tqdm import tqdm


# chunker = NeuralChunker(
#     model="mirth/chonky_modernbert_base_1",  # Default model
#     device_map="cpu",                        # Device to run the model on ('cpu', 'cuda', etc.)
#     min_characters_per_chunk=10,             # Minimum characters for a chunk
# )


chunker = TokenChunker(
    tokenizer="word", # Default tokenizer (or use "gpt2", etc.)
    chunk_size=512, # Maximum tokens per chunk
    chunk_overlap=128 # Overlap between chunks
)


client = weaviate.connect_to_local(
    headers={
        "X-Cohere-Api-Key": os.getenv("COHERE_API_KEY")
    },
)

if not client.collections.exists("Chunks"):
    client.collections.create(
        name="Chunks",
        properties=[
            Property(name="chunk", data_type=DataType.TEXT),
            Property(name="chunk_no", data_type=DataType.INT),
            Property(name="path", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
        ],
        vector_config=Configure.Vectors.text2vec_cohere(
            model="embed-v4.0",
            source_properties=["chunk", "path"]
        )
    )

chunks = client.collections.use("Chunks")

with open("./output/weaviate_docs_crawl4ai.json", "r") as f:
    data = json.load(f)

with chunks.batch.fixed_size(batch_size=50) as batch:
    for path, text in tqdm(data.items()):
        if "docs.weaviate.io/weaviate" in path:
            for i, chunk in enumerate(chunker.chunk(text)):
                batch.add_object(
                    properties={
                        "chunk": chunk.text,
                        "chunk_no": i,
                        "path": path
                    },
                    uuid=generate_uuid5("Chunks", f"{path}-{i}")
                )

client.close()
