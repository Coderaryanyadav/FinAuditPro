import os
import tempfile
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.middleware.rbac import require_permission
from api.schemas.document import DocumentRead
from database.models import User
from database.repositories.document_repo import DocumentRepository
from services.document_service import DocumentService
from security.rbac import Permission
from core.exceptions import ValidationError, EntityNotFoundError, AuthError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    engagement_id: int = Form(...),
    document_type: str = Form("Uploaded"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.UPLOAD_DOCUMENTS))
):
    """Upload document file and register in managed storage."""
    doc_repo = DocumentRepository(db)
    doc_service = DocumentService(doc_repo)

    # Save uploaded file to temp file
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_file.bin")
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return doc_service.upload_document(
            engagement_id=engagement_id,
            file_path=temp_file_path,
            document_type=document_type
        )
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve document metadata by ID."""
    doc_repo = DocumentRepository(db)
    doc_service = DocumentService(doc_repo)
    try:
        return doc_service.get_document(document_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/engagement/{engagement_id}", response_model=List[DocumentRead])
def get_engagement_documents(
    engagement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents for engagement."""
    doc_repo = DocumentRepository(db)
    doc_service = DocumentService(doc_repo)
    return doc_service.get_engagement_documents(engagement_id)
