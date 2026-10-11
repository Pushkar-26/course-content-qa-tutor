from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.ingestion.chunker import create_chunks
from app.ingestion.document_parser import extract_pdf
from app.ingestion.text_cleaner import clean_text


def process_document(document: Document, db: Session) -> int:
    document.status = "processing"
    db.commit()

    try:
        pdf_path = Path(document.file_path)

        pages = extract_pdf(pdf_path)

        for page in pages:
            for line in page["lines"]:
                line["text"] = clean_text(line["text"])

        chunks = create_chunks(
            pages=pages,
            document_id=document.id,
            source=document.filename,
        )

        chunk_records = [
            Chunk(
                id=chunk.chunk_id,
                document_id=chunk.document_id,
                source=chunk.source,
                page_number=chunk.page_number,
                page_end=chunk.page_end,
                section=chunk.section,
                text=chunk.text,
                chunk_index=chunk.chunk_index,
            )
            for chunk in chunks
        ]

        db.add_all(chunk_records)

        document.page_count = len(pages)
        document.status = "processed"

        db.commit()

        return len(chunk_records)

    except Exception:
        db.rollback()

        document.status = "failed"
        db.commit()

        raise