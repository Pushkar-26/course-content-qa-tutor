
from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import Conversation, Message, User
from app.generation.answer_generator import (
    generate_final_answer,
    generate_general_answer,
)
from app.retrieval.context_builder import build_context
from app.retrieval.reranked_search import reranked_search


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    previous_query: str | None = None
    history: list[str] | None = None
    mode: Literal["course", "general"] = "course"


class SourceResponse(BaseModel):
    id: int
    document_id: str
    source: str
    page_start: int
    page_end: int | None
    section: str | None
    chunk_id: str
    preview: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceResponse]
    retrieval_queries: list[str]
    fts_queries: list[str]
    conversation_id: str


def save_exchange(
    db: Session,
    conversation: Conversation,
    query: str,
    answer: str,
    sources: list[SourceResponse],
):
    conversation.updated_at = datetime.utcnow()

    db.add(conversation)
    db.flush()

    db.add(
        Message(
            id=str(uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=query,
            sources=[],
        )
    )

    db.add(
        Message(
            id=str(uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources=[source.dict() for source in sources],
        )
    )

    db.commit()


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty",
        )

    if request.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )
    else:
        conversation = Conversation(
            id=str(uuid4()),
            user_id=current_user.id,
            title=query[:60],
        )

    try:
        # General AI mode: answer using Gemini's general knowledge.
        if request.mode == "general":
            answer = generate_general_answer(query)

            save_exchange(
                db=db,
                conversation=conversation,
                query=query,
                answer=answer,
                sources=[],
            )

            return ChatResponse(
                query=query,
                answer=answer,
                sources=[],
                retrieval_queries=[],
                fts_queries=[],
                conversation_id=conversation.id,
            )

        # Course Materials mode: use the existing RAG pipeline.
        reranked_result = reranked_search(
            db=db,
            query=query,
            owner_id=current_user.id,
            previous_query=request.previous_query,
            history=request.history,
            retrieval_limit=30,
            candidate_limit=20,
            final_limit=5,
        )

        if not reranked_result.results:
            answer = (
                "I could not find enough relevant "
                "course material to answer this question."
            )

            save_exchange(
                db=db,
                conversation=conversation,
                query=query,
                answer=answer,
                sources=[],
            )

            return ChatResponse(
                query=query,
                answer=answer,
                sources=[],
                retrieval_queries=reranked_result.retrieval_queries,
                fts_queries=reranked_result.fts_queries,
                conversation_id=conversation.id,
            )

        context = build_context(
            db=db,
            reranked_results=reranked_result.results,
            window=1,
            max_chunks=12,
        )

        if not context.chunks:
            answer = (
                "I could not find enough relevant "
                "course material to answer this question."
            )

            save_exchange(
                db=db,
                conversation=conversation,
                query=query,
                answer=answer,
                sources=[],
            )

            return ChatResponse(
                query=query,
                answer=answer,
                sources=[],
                retrieval_queries=reranked_result.retrieval_queries,
                fts_queries=reranked_result.fts_queries,
                conversation_id=conversation.id,
            )

        final_answer = generate_final_answer(
            query=query,
            context=context,
        )

        context_chunk_map = {
            item.chunk.id: item.chunk
            for item in context.chunks
        }

        sources = []

        for index, citation in enumerate(
            final_answer.citations,
            start=1,
        ):
            chunk = context_chunk_map.get(citation.chunk_id)

            if chunk is None:
                continue

            sources.append(
                SourceResponse(
                    id=index,
                    document_id=chunk.document_id,
                    source=citation.source,
                    page_start=citation.page_start,
                    page_end=citation.page_end,
                    section=citation.section,
                    chunk_id=citation.chunk_id,
                    preview=chunk.text[:1000],
                )
            )

        save_exchange(
            db=db,
            conversation=conversation,
            query=query,
            answer=final_answer.answer,
            sources=sources,
        )

        return ChatResponse(
            query=query,
            answer=final_answer.answer,
            sources=sources,
            retrieval_queries=reranked_result.retrieval_queries,
            fts_queries=reranked_result.fts_queries,
            conversation_id=conversation.id,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        print(f"Chat processing error: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Chat processing failed.",
        ) from exc

@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return {
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            }
            for conversation in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "sources": message.sources or [],
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }
@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return {
        "conversations": [
            {
                "id": item.id,
                "title": item.title,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "sources": message.sources or [],
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }