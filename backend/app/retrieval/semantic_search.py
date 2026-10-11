
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.embeddings.gemini_embedder import embed_query


def search_similar_chunks(
    db: Session,
    query: str,
    owner_id: str,
    limit: int = 5,
) -> list[tuple[Chunk, float]]:
    query_embedding = embed_query(query)

    distance = Chunk.embedding.cosine_distance(query_embedding)

    results = db.execute(
        select(Chunk, distance.label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.owner_id == owner_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    ).all()

    return [
        (chunk, float(distance_value))
        for chunk, distance_value in results
    ]
