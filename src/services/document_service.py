import os
from typing import List, Optional
from core.exceptions import ValidationError, EntityNotFoundError
from database.repositories.document_repo import DocumentRepository
from database.models import Document, DocumentPage

class DocumentService:
    """
    Service responsible for managing uploaded documents.
    
    Repositories used:
    - DocumentRepository
    
    Business Rules:
    - Verifies file exists physically before creating DB record.
    - Tracks vectorization status for AI RAG pipeline.
    """

    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo

    def upload_document(self, engagement_id: int, file_path: str, document_type: str) -> Document:
        """Register a new document upload in the system."""
        if not os.path.exists(file_path):
            raise ValidationError(f"File does not exist at path: {file_path}")
            
        file_name = os.path.basename(file_path)
        return self.document_repo.create(
            engagement_id=engagement_id,
            file_name=file_name,
            file_path=file_path,
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

    def mark_as_vectorized(self, document_id: int) -> None:
        """Update status once AI pipeline finishes processing."""
        self.document_repo.mark_vectorized(document_id)

    def add_document_page_data(self, document_id: int, page_number: int, ocr_text: str) -> DocumentPage:
        """Store OCR data for a specific page."""
        return self.document_repo.add_page(document_id, page_number, ocr_text)
