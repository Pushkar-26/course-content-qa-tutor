from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Chunk
from app.retrieval.reranker import RerankedResult


@dataclass
class ContextChunk:
    chunk: Chunk
    relevance_score: float
    is_anchor: bool = False
    citation_id: str = ""


@dataclass
class BuiltContext:
    chunks: list[ContextChunk]
    text: str


def get_neighbors(
    db: Session,
    chunk: Chunk,
    window: int = 1,
) -> list[Chunk]:
    start_index = max(0, chunk.chunk_index - window)
    end_index = chunk.chunk_index + window

    return db.scalars(
        select(Chunk)
        .where(
            Chunk.document_id == chunk.document_id,
            Chunk.chunk_index >= start_index,
            Chunk.chunk_index <= end_index,
        )
        .order_by(Chunk.chunk_index)
    ).all()


def expand_neighbors(
    db: Session,
    reranked_results: list[RerankedResult],
    window: int = 1,
    max_chunks: int = 12,
) -> list[ContextChunk]:
    selected: dict[str, ContextChunk] = {}

    for result in reranked_results:
        anchor = result.chunk.chunk

        selected[anchor.id] = ContextChunk(
            chunk=anchor,
            relevance_score=result.score,
            is_anchor=True,
        )

        neighbors = get_neighbors(
            db=db,
            chunk=anchor,
            window=window,
        )

        for neighbor in neighbors:
            if neighbor.id == anchor.id:
                continue

            if neighbor.id not in selected:
                selected[neighbor.id] = ContextChunk(
                    chunk=neighbor,
                    relevance_score=0.0,
                    is_anchor=False,
                )

    anchors = {
        result.chunk.chunk.id: result.score
        for result in reranked_results
    }

    ordered = sorted(
        selected.values(),
        key=lambda item: (
            item.chunk.source,
            item.chunk.chunk_index,
        ),
    )

    def priority(item: ContextChunk):
        return (
            0 if item.is_anchor else 1,
            -anchors.get(item.chunk.id, 0.0),
            item.chunk.source,
            item.chunk.chunk_index,
        )

    anchor_first = sorted(
        ordered,
        key=priority,
    )

    return anchor_first[:max_chunks]


def format_context(
    chunks: list[ContextChunk],
) -> str:
    sections = []

    for index, item in enumerate(chunks, start=1):
        chunk = item.chunk

        page_text = str(chunk.page_number)

        if chunk.page_end and chunk.page_end != chunk.page_number:
            page_text = f"{chunk.page_number}-{chunk.page_end}"

        section_text = chunk.section or "Unknown section"

        sections.append(
            f"[{item.citation_id}]\n"
            f"Source: {chunk.source}\n"
            f"Pages: {page_text}\n"
            f"Section: {section_text}\n"
            f"Chunk ID: {chunk.id}\n"
            f"Content:\n{chunk.text}"
        )

    return "\n\n".join(sections)


def build_context(
    db: Session,
    reranked_results: list[RerankedResult],
    window: int = 1,
    max_chunks: int = 12,
) -> BuiltContext:
    if not reranked_results:
        return BuiltContext(
            chunks=[],
            text="",
        )

    context_chunks = expand_neighbors(
        db=db,
        reranked_results=reranked_results,
        window=window,
        max_chunks=max_chunks,
    )

    for index, item in enumerate(context_chunks, start=1):
        item.citation_id = f"C{index}"

    context_text = format_context(context_chunks)

    return BuiltContext(
        chunks=context_chunks,
        text=context_text,
    )