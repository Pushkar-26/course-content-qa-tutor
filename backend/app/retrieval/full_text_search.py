
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document


def run_fts_query(
    db: Session,
    tsquery,
    owner_id: str,
    limit: int,
) -> list[tuple[Chunk, float]]:
    searchable_text = func.concat_ws(
        " ",
        Chunk.section,
        Chunk.text,
    )

    tsvector = func.to_tsvector(
        "english",
        searchable_text,
    )

    rank = func.ts_rank_cd(
        tsvector,
        tsquery,
    )

    results = db.execute(
        select(
            Chunk,
            rank.label("rank"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.owner_id == owner_id,
            Chunk.text.is_not(None),
            tsvector.op("@@")(tsquery),
        )
        .order_by(rank.desc())
        .limit(limit)
    ).all()

    return [
        (chunk, float(rank_value))
        for chunk, rank_value in results
    ]


def search_full_text(
    db: Session,
    query: str,
    owner_id: str,
    limit: int = 5,
) -> list[tuple[Chunk, float]]:
    query = " ".join(query.split()).strip()

    if not query:
        return []

    and_query = func.plainto_tsquery(
        "english",
        query,
    )

    results = run_fts_query(
        db=db,
        tsquery=and_query,
        owner_id=owner_id,
        limit=limit,
    )

    if results:
        return results

    tokens = re.findall(r"[A-Za-z0-9]+", query.lower())

    if not tokens:
        return []

    or_query_text = " | ".join(tokens)

    or_query = func.to_tsquery(
        "english",
        or_query_text,
    )

    return run_fts_query(
        db=db,
        tsquery=or_query,
        owner_id=owner_id,
        limit=limit,
    )
