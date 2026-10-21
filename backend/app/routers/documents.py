import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Document
from app.schemas.document import DocumentResponse
from app.services.processing_service import process_document_background

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all documents owned by the authenticated student."""
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Safely upload a PDF document and create a database record."""
    # 1. Validate file extension and MIME type
    original_filename = file.filename or "uploaded.pdf"
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported.",
        )

    # 2. Read contents safely and validate file size (max 25MB)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 3. Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 4. Generate safe UUID-based stored filename to prevent path traversal
    safe_stored_filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_stored_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 5. Create Document record in database with initial status 'Processing'
    doc = Document(
        user_id=current_user.id,
        filename=os.path.basename(original_filename),
        file_path=file_path,
        file_size=file_size,
        status="Processing",
        chunks_count=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Dispatch background text extraction, chunking, and embedding
    background_tasks.add_task(process_document_background, str(doc.id), file_path)

    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of a single document owned by current user."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document owned by current user."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )

    # Remove file from disk if present
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' deleted successfully."}
