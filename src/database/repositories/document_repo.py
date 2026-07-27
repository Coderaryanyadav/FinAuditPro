from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Document, DocumentPage

class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, document_id: int) -> Optional[Document]:
        return self.session.query(Document).filter(Document.id == document_id).first()

    def get_by_engagement_id(self, engagement_id: int) -> List[Document]:
        return self.session.query(Document).filter((Document.engagement_id == engagement_id) | (Document.audit_id == engagement_id)).all()

    def get_by_audit_id(self, audit_id: int) -> List[Document]:
        return self.session.query(Document).filter((Document.audit_id == audit_id) | (Document.engagement_id == audit_id)).all()

    def create(self, engagement_id: int = None, audit_id: int = None, file_name: str = "", file_path: str = "", document_type: str = None, doc_type: str = "Uploaded") -> Document:
        document = Document(
            engagement_id=engagement_id or audit_id,
            audit_id=audit_id or engagement_id,
            file_name=file_name,
            file_path=file_path,
            document_type=document_type,
            doc_type=doc_type
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def mark_vectorized(self, document_id: int) -> None:
        document = self.get_by_id(document_id)
        if document:
            document.is_vectorized = True
            self.session.commit()

    def add_page(self, document_id: int, page_number: int, ocr_text: str) -> DocumentPage:
        page = DocumentPage(
            document_id=document_id,
            page_number=page_number,
            ocr_text=ocr_text
        )
        self.session.add(page)
        self.session.commit()
        self.session.refresh(page)
        return page
