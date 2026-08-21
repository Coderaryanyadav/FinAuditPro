"""Application service orchestrating document ingestion, search, categorization, and evidence linking."""

from dataclasses import dataclass
from pathlib import Path

from finauditpro.domain.document_entities import (
    Document,
    DocumentCategoryEnum,
    DocumentPage,
    DocumentStatusEnum,
    DocumentTable,
    EvidenceLink,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.infrastructure.documents.document_pipeline import DocumentPipeline
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.document_repository import (
    DocumentRepository,
)
from finauditpro.infrastructure.persistence.repositories.engagement_repository import (
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.evidence_repository import (
    EvidenceRepository,
)


@dataclass(frozen=True)
class UploadDocumentDTO:
    engagement_id: str
    file_path: str
    category: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL


@dataclass(frozen=True)
class CreateEvidenceLinkDTO:
    engagement_id: str
    document_id: str
    page_number: int = 1
    target_type: str = "Audit Finding"
    target_id: str | None = None
    title: str = "Evidence Reference"
    snippet: str | None = None


@dataclass
class DocumentDetailsDTO:
    document: Document
    pages: list[DocumentPage]
    tables: list[DocumentTable]
    evidence_links: list[EvidenceLink]


@dataclass
class DocumentSearchResultDTO:
    document_id: str
    filename: str
    document_category: str
    page_number: int
    text_source: str
    snippet: str
    confidence_score: float


class DocumentService:
    """Application service for Document Lifecycle, Extraction, FTS5 Search, and Evidence Linking."""

    def __init__(
        self, db_manager: DatabaseManager, pipeline: DocumentPipeline | None = None
    ) -> None:
        self.db_manager = db_manager
        # Keep source documents alongside the selected database.  This makes a
        # user-selected database self-contained and gives test/deployment
        # environments an explicit writable storage root.
        if pipeline is None:
            database_path = Path(str(db_manager.engine.url.database))
            pipeline = DocumentPipeline(storage_dir=database_path.parent / "documents")
        self.pipeline = pipeline

    def upload_and_process_document(self, dto: UploadDocumentDTO) -> Document:
        """Upload a file, run the security/extraction/OCR pipeline, index FTS5, and persist metadata/pages."""
        source_path = Path(dto.file_path)
        if not source_path.is_file():
            raise EntityNotFoundError("Source File", dto.file_path)

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            # Check if identical hash already exists in engagement (Dedup Check)
            doc_repo = DocumentRepository(session)
            from finauditpro.infrastructure.documents.document_security import calculate_sha256

            try:
                c_hash = calculate_sha256(source_path)
                existing = doc_repo.get_by_hash(dto.engagement_id, c_hash)
                if existing:
                    return existing
            except Exception:
                pass

        # Execute Document Pipeline across inspectable stages
        res = self.pipeline.process_incoming_file(
            engagement_id=dto.engagement_id,
            source_path=source_path,
            category=dto.category,
        )

        doc = Document(
            engagement_id=dto.engagement_id,
            filename=res.filename,
            original_path=res.original_path,
            stored_path=res.stored_path,
            content_hash=res.content_hash,
            mime_type=res.mime_type,
            file_size_bytes=res.file_size_bytes,
            page_count=res.page_count,
            document_category=res.machine_category,
            status=res.status,
            failed_stage=res.failed_stage,
            failure_reason=res.failure_reason,
            machine_category=res.machine_category,
            category_confidence=res.category_confidence,
            category_evidence=res.category_evidence,
        )

        # Update page and table document IDs
        pages = []
        for pg in res.pages:
            pages.append(
                DocumentPage(
                    id=pg.id,
                    document_id=doc.id,
                    page_number=pg.page_number,
                    extracted_text=pg.extracted_text,
                    text_source=pg.text_source,
                    ocr_applied=pg.ocr_applied,
                    confidence_score=pg.confidence_score,
                    layout_json=pg.layout_json,
                )
            )

        tables = []
        for tbl in res.tables:
            tables.append(
                DocumentTable(
                    id=tbl.id,
                    document_id=doc.id,
                    page_number=tbl.page_number,
                    table_index=tbl.table_index,
                    rows_json=tbl.rows_json,
                    bbox_json=tbl.bbox_json,
                )
            )

        with self.db_manager.session_scope() as session:
            doc_repo = DocumentRepository(session)
            saved_doc = doc_repo.add(doc)
            doc_repo.add_pages(pages)
            if tables:
                doc_repo.add_tables(tables)

            # Index pages into FTS5 virtual table if READY
            if doc.status == DocumentStatusEnum.READY or doc.status == DocumentStatusEnum.COMPLETED:
                doc_repo.index_pages_fts(dto.engagement_id, doc.id, pages)

            # Persist Hash-Chained Audit Events for each pipeline stage
            audit_repo = AuditEventRepository(session)
            for ev in res.audit_events:
                ev.engagement_id = dto.engagement_id
                audit_repo.add(ev)

        return saved_doc

    def list_documents_for_engagement(self, engagement_id: str) -> list[Document]:
        with self.db_manager.session_scope() as session:
            repo = DocumentRepository(session)
            return repo.list_by_engagement(engagement_id)

    def get_document_details(self, document_id: str) -> DocumentDetailsDTO:
        with self.db_manager.session_scope() as session:
            doc_repo = DocumentRepository(session)
            doc = doc_repo.get_by_id(document_id)
            if not doc:
                raise EntityNotFoundError("Document", document_id)

            pages = doc_repo.get_document_pages(document_id)

            ev_repo = EvidenceRepository(session)
            evidence_links = ev_repo.list_links_by_document(document_id)

            # Fetch tables
            from sqlalchemy import select

            from finauditpro.infrastructure.persistence.models import DocumentTableModel

            tbl_stmt = select(DocumentTableModel).where(
                DocumentTableModel.document_id == document_id
            )
            tbl_models = session.scalars(tbl_stmt).all()
            tables = [
                DocumentTable(
                    id=m.id,
                    document_id=m.document_id,
                    page_number=m.page_number,
                    table_index=m.table_index,
                    rows_json=m.rows_json,
                    bbox_json=m.bbox_json,
                    created_at=m.created_at,
                )
                for m in tbl_models
            ]

            return DocumentDetailsDTO(
                document=doc,
                pages=pages,
                tables=tables,
                evidence_links=evidence_links,
            )

    def override_document_category(
        self, document_id: str, new_category: DocumentCategoryEnum
    ) -> Document:
        """Allow auditor to explicitly override machine classification."""
        with self.db_manager.session_scope() as session:
            repo = DocumentRepository(session)
            doc = repo.update_category(document_id, new_category)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=doc.engagement_id,
                    actor="Auditor",
                    action="Document Category Overridden",
                    details=f"Document '{doc.filename}' category updated to '{new_category.value}'.",
                )
            )
            return doc

    def search_documents(self, engagement_id: str, query: str) -> list[DocumentSearchResultDTO]:
        """Perform FTS5 search strictly isolated within the engagement boundary."""
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        with self.db_manager.session_scope() as session:
            repo = DocumentRepository(session)
            matches = repo.search_pages(engagement_id, clean_query)

            results: list[DocumentSearchResultDTO] = []
            for doc, page in matches:
                text = page.extracted_text
                idx = text.lower().find(clean_query.lower())
                if idx >= 0:
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(clean_query) + 60)
                    snippet = f"...{text[start:end]}..."
                else:
                    snippet = text[:100]

                results.append(
                    DocumentSearchResultDTO(
                        document_id=doc.id,
                        filename=doc.filename,
                        document_category=doc.document_category.value,
                        page_number=page.page_number,
                        text_source=page.text_source.value
                        if hasattr(page.text_source, "value")
                        else str(page.text_source),
                        snippet=snippet,
                        confidence_score=page.confidence_score or 1.0,
                    )
                )

            return results

    def create_evidence_link(self, dto: CreateEvidenceLinkDTO) -> EvidenceLink:
        """Link a specific document page / snippet as evidence to downstream audit objects."""
        if not dto.title or not dto.title.strip():
            raise ValidationError("Evidence link title cannot be empty.")

        with self.db_manager.session_scope() as session:
            doc_repo = DocumentRepository(session)
            doc = doc_repo.get_by_id(dto.document_id)
            if not doc:
                raise EntityNotFoundError("Document", dto.document_id)

            link = EvidenceLink(
                engagement_id=dto.engagement_id,
                document_id=dto.document_id,
                page_number=dto.page_number,
                target_type=dto.target_type,
                target_id=dto.target_id,
                title=dto.title.strip(),
                snippet=dto.snippet.strip() if dto.snippet else None,
            )

            ev_repo = EvidenceRepository(session)
            saved_link = ev_repo.add_link(link)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="Auditor",
                    action="Evidence Linked",
                    details=f"Linked '{doc.filename}' Page {dto.page_number} to '{dto.target_type}' ({dto.title}).",
                )
            )

            return saved_link

    def list_evidence_links_for_engagement(self, engagement_id: str) -> list[EvidenceLink]:
        with self.db_manager.session_scope() as session:
            ev_repo = EvidenceRepository(session)
            return ev_repo.list_links_by_engagement(engagement_id)

    def delete_document(self, document_id: str) -> bool:
        """Soft delete document and desync FTS5 index while logging audit event."""
        with self.db_manager.session_scope() as session:
            repo = DocumentRepository(session)
            doc = repo.get_by_id(document_id)
            if not doc:
                return False

            success = repo.soft_delete(document_id)
            if success:
                audit_repo = AuditEventRepository(session)
                audit_repo.add(
                    AuditEvent(
                        engagement_id=doc.engagement_id,
                        actor="Auditor",
                        action="Document Soft Deleted",
                        details=f"Soft deleted document '{doc.filename}' (FTS index desynced).",
                    )
                )
            return success
