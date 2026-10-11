from app.db.database import SessionLocal
from app.retrieval.semantic_search import search_similar_chunks


db = SessionLocal()

try:
    query = "How did the Internet begin?"

    results = search_similar_chunks(
        db=db,
        query=query,
        limit=5,
    )

    print(f"Query: {query}")
    print(f"Results: {len(results)}")

    for rank, (chunk, distance) in enumerate(results, start=1):
        similarity = 1 - distance

        print(f"\n========== RESULT {rank} ==========")
        print("Similarity:", similarity)
        print("Document:", chunk.source)
        print("Pages:", chunk.page_number, "-", chunk.page_end)
        print("Section:", chunk.section)
        print("Text:", chunk.text[:500])

finally:
    db.close()