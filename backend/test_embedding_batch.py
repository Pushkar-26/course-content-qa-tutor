from app.embeddings.gemini_embedder import embed_document_batch


texts = [
    "ARPANET was one of the earliest computer networks.",
    "Jupiter is the largest planet in the Solar System.",
    "The Domain Name System maps domain names to IP addresses.",
]

embeddings = embed_document_batch(texts)

print("Embeddings generated:", len(embeddings))

for i, embedding in enumerate(embeddings, start=1):
    magnitude = sum(value * value for value in embedding) ** 0.5

    print(
        f"Embedding {i}: "
        f"dimensions={len(embedding)}, "
        f"magnitude={magnitude}"
    )