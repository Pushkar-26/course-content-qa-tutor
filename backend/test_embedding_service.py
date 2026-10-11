from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.db.models import Chunk
from app.embeddings.embedding_service import embed_pending_chunks


db = SessionLocal()

try:
    pending_before = db.scalar(
        select(func.count())
        .select_from(Chunk)
        .where(Chunk.embedding.is_(None))
    )

    print("Pending chunks before:", pending_before)

    embedded = embed_pending_chunks(db)

    pending_after = db.scalar(
        select(func.count())
        .select_from(Chunk)
        .where(Chunk.embedding.is_(None))
    )

    print("New embeddings created:", embedded)
    print("Pending chunks after:", pending_after)

finally:
    db.close()