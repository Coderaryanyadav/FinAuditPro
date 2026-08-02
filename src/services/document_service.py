import os
from typing import List, Optional
from core.exceptions import ValidationError, EntityNotFoundError, AuthError
from database.repositories.document_repo import DocumentRepository
from database.models import Document, DocumentPage
from security.security_manager import SecurityManager
from security.rbac import Permission

class DocumentService:
    """
    Service responsible for managing uploaded documents with RBAC security gates.
    """

    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo

    def upload_document(self, engagement_id: int, file_path: str, document_type: str) -> Document:
        """Register a new document upload in the system."""
        sm = SecurityManager()
        if not sm.current_session:
            raise AuthError("Authentication required: No active session. Please log in to upload documents.")
        if not sm.check_permission(Permission.UPLOAD_DOCUMENTS):
            raise AuthError("User role lacks permission UPLOAD_DOCUMENTS to ingest document.")

        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist at path: {file_path}")
            
        file_name = os.path.basename(file_path)
        managed_dir = os.path.join("data", "documents", f"eng_{engagement_id}")
        os.makedirs(managed_dir, exist_ok=True)
        dest_path = os.path.join(managed_dir, file_name)
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            import shutil
            shutil.copy2(file_path, dest_path)

        return self.document_repo.create(
            engagement_id=engagement_id,
            file_name=file_name,
            file_path=dest_path,
            document_type=document_type
        )

    def get_document(self, document_id: int) -> Document:
        """Retrieve a document by ID."""
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise EntityNotFoundError(f"Document {document_id} not found.")
        return document

    def get_engagement_documents(self, engagement_id: int) -> List[Document]:
        """Get all documents for a specific engagement."""
        return self.document_repo.get_by_engagement_id(engagement_id)

    def get_audit_documents(self, audit_id: int) -> List[Document]:
        """Get all documents for a specific audit project."""
        return self.document_repo.get_by_audit_id(audit_id)

    def upload_audit_document(self, audit_id: int, file_path: str, doc_type: str = "Uploaded") -> Document:
        """Register a document for an audit project after validating file existence."""
        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist at path: {file_path}")
        file_name = os.path.basename(file_path)
        return self.document_repo.create(
            audit_id=audit_id,
            file_name=file_name,
            file_path=file_path,
            doc_type=doc_type
        )

    def mark_as_vectorized(self, document_id: int) -> None:
        """Update status once AI pipeline finishes processing."""
        self.document_repo.mark_vectorized(document_id)

    def add_document_page_data(self, document_id: int, page_number: int, ocr_text: str) -> DocumentPage:
        """Store OCR data for a specific page."""
        return self.document_repo.add_page(document_id, page_number, ocr_text)
