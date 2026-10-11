from app.embeddings.gemini_embedder import embed_document


text = """
ARPANET was one of the earliest computer networks and
played an important role in the development of the Internet.
"""

embedding = embed_document(text)

print("Embedding generated successfully")
print("Dimensions:", len(embedding))

magnitude = sum(value * value for value in embedding) ** 0.5
print("Vector magnitude:", magnitude)

print("First 5 values:", embedding[:5])