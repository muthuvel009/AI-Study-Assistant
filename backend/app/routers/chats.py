import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Chat, Message, Document, DocumentChunk
from app.schemas.chat import ChatMessageCreate, ChatSendResponse, ChatMessageResponse
from app.services.ai_service import generate_embedding, generate_rag_answer

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatSendResponse)
def send_message(
    request: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG Chat endpoint:
    1. If document_id provided, verify ownership
    2. Generate query embedding
    3. Perform pgvector cosine similarity search filtered strictly by current_user.id
    4. Assemble grounded context and call Gemini
    5. Persist user message and assistant answer with citations
    """
    # 1. If document_id provided, verify ownership
    if request.document_id:
        doc = (
            db.query(Document)
            .filter(Document.id == request.document_id, Document.user_id == current_user.id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected study document not found or access denied.",
            )

    # 2. Get or create active chat session for current user
    chat = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .first()
    )
    if not chat:
        chat = Chat(
            user_id=current_user.id,
            title="Study Session",
            document_id=request.document_id,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # 3. Generate query embedding
    query_vector = generate_embedding(request.query)

    # 4. Perform pgvector semantic search strictly scoped to current_user
    distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)

    search_query = (
        db.query(DocumentChunk, Document.filename, distance_expr.label("distance"))
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.user_id == current_user.id)
        .filter(DocumentChunk.embedding.isnot(None))
    )

    if request.document_id:
        search_query = search_query.filter(Document.id == request.document_id)

    results = (
        search_query
        .order_by(distance_expr.asc())
        .limit(settings.TOP_K)
        .all()
    )

    context_chunks = []
    for chunk, doc_filename, dist in results:
        # Cosine distance ranges from 0 (identical) to 2 (opposite)
        distance_val = float(dist) if dist is not None else 1.0
        similarity_score = max(0.0, 1.0 - distance_val)
        context_chunks.append({
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "document_name": doc_filename,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "cosine_distance": round(distance_val, 4),
            "similarity": similarity_score,
        })

    # 5. Generate grounded study response via Gemini
    rag_result = generate_rag_answer(request.query, context_chunks)
    answer_text = rag_result["answer"]
    sources_list = rag_result["sources"]

    # 6. Store user message in database
    user_msg = Message(
        chat_id=chat.id,
        sender="user",
        content=request.query,
    )
    db.add(user_msg)

    # 7. Store assistant message with citations in database
    assistant_msg = Message(
        chat_id=chat.id,
        sender="assistant",
        content=answer_text,
        sources=json.dumps(sources_list),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatSendResponse(
        answer=answer_text,
        response=answer_text,
        sources=sources_list,
        chat_id=str(chat.id),
        document_id=request.document_id,
    )


@router.get("/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve message history for current authenticated user's active chat."""
    chat = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .first()
    )
    if not chat:
        return []

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    history = []
    for msg in messages:
        sources_list = []
        if msg.sources:
            try:
                sources_list = json.loads(msg.sources)
            except Exception:
                sources_list = []

        history.append(
            ChatMessageResponse(
                id=str(msg.id),
                sender=msg.sender,
                text=msg.content,
                sources=sources_list,
                timestamp=msg.created_at.strftime("%I:%M %p") if msg.created_at else None,
                created_at=msg.created_at,
            )
        )
    return history


@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear chat messages for the current authenticated user's chat."""
    chat = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .first()
    )
    if chat:
        db.query(Message).filter(Message.chat_id == chat.id).delete()
        db.commit()

    return {"message": "Chat history cleared successfully."}
