from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.embeddings.gemini_embedder import embed_document_batch


BATCH_SIZE = 20


def get_embedding_text(chunk: Chunk) -> str:
    if chunk.section:
        return f"{chunk.section}\n\n{chunk.text}"

    return chunk.text


def embed_pending_chunks(db: Session) -> int:
    total_embedded = 0

    while True:
        chunks = db.scalars(
            select(Chunk)
            .where(Chunk.embedding.is_(None))
            .order_by(Chunk.id)
            .limit(BATCH_SIZE)
        ).all()

        if not chunks:
            break

        texts = [
            get_embedding_text(chunk)
            for chunk in chunks
        ]

        embeddings = embed_document_batch(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        db.commit()

        total_embedded += len(chunks)

        print(
            f"Embedded {len(chunks)} chunks "
            f"(total: {total_embedded})"
        )

    return total_embedded