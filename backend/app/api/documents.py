import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.services.document_ingestion import process_document


router = APIRouter(prefix="/documents", tags=["Documents"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt"}


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}",
        )

    document_id = str(uuid4())
    safe_name = f"{document_id}{extension}"
    file_path = UPLOAD_DIR / safe_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        id=document_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=extension,
        status="uploaded",
        owner_id=current_user.id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunk_count = process_document(document, db)

    return {
        "document_id": document.id,
        "filename": document.filename,
        "stored_as": safe_name,
        "status": document.status,
        "page_count": document.page_count,
        "chunks_saved": chunk_count,
    }


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = Path(document.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document file not found",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf" if document.file_type == ".pdf" else None,
        filename=document.filename,
    )

@router.get("")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return {
        "documents": [
            {
                "document_id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "status": document.status,
                "page_count": document.page_count,
                "uploaded_at": document.uploaded_at,
            }
            for document in documents
        ]
    }
@router.get("")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return {
        "documents": [
            {
                "document_id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "status": doc.status,
                "page_count": doc.page_count,
                "uploaded_at": doc.uploaded_at,
            }
            for doc in documents
        ]
    }

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = Path(document.file_path).resolve()
    upload_root = UPLOAD_DIR.resolve()

    # Only allow deletion of files stored in the uploads directory.
    if not file_path.is_relative_to(upload_root):
        raise HTTPException(
            status_code=500,
            detail="Invalid stored document path",
        )

    try:
        db.delete(document)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete document from database",
        ) from exc

    # Remove the original uploaded file after the DB transaction succeeds.
    try:
        file_path.unlink(missing_ok=True)
    except OSError as exc:
        # The database record is already deleted; log the leftover-file issue.
        print(f"Could not remove uploaded file {file_path}: {exc}")

    return {"message": "Document deleted successfully"}
@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.get(Document, document_id)

    if document is None or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = Path(document.file_path).resolve()
    upload_root = UPLOAD_DIR.resolve()

    if not file_path.is_relative_to(upload_root):
        raise HTTPException(
            status_code=500,
            detail="Invalid stored document path",
        )

    try:
        db.delete(document)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete document",
        ) from exc

    try:
        file_path.unlink(missing_ok=True)
    except OSError as exc:
        print(f"Could not remove file: {exc}")

    return {"message": "Document deleted successfully"}