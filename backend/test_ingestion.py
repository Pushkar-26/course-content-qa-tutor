from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Document, Chunk
from app.services.document_ingestion import process_document


db = SessionLocal()

try:
    document = db.scalar(
        select(Document)
        .order_by(Document.uploaded_at.desc())
    )

    if not document:
        print("No document found")
        raise SystemExit(1)

    print("Processing:", document.filename)

    chunk_count = db.scalar(
        select(Chunk.id)
        .where(Chunk.document_id == document.id)
        .limit(1)
    )

    if chunk_count:
        print("Chunks already exist for this document")
        raise SystemExit(0)

    total_chunks = process_document(document, db)

    print("Pages:", document.page_count)
    print("Chunks saved:", total_chunks)
    print("Status:", document.status)

finally:
    db.close()