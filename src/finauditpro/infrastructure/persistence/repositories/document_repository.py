"""Document repository for SQLite persistence with FTS5 search and evidence linking."""

import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from finauditpro.domain.document_entities import (
    Document,
    DocumentCategoryEnum,
    DocumentPage,
    DocumentStatusEnum,
    DocumentTable,
    TextSourceEnum,
)
from finauditpro.infrastructure.persistence.models import (
    DocumentModel,
    DocumentPageModel,
    DocumentTableModel,
)


class DocumentRepository:
    """Repository managing Document, Page, Table persistence and FTS5 full-text search."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: DocumentModel) -> Document:
        evidence_list = []
        if model.category_evidence_json:
            try:
                evidence_list = json.loads(model.category_evidence_json)
            except Exception:
                evidence_list = []

        return Document(
            id=model.id,
            engagement_id=model.engagement_id,
            filename=model.filename,
            original_path=model.original_path,
            stored_path=model.stored_path,
            content_hash=model.content_hash,
            mime_type=model.mime_type,
            file_size_bytes=model.file_size_bytes,
            page_count=model.page_count,
            document_category=DocumentCategoryEnum(model.document_category),
            status=DocumentStatusEnum(model.status),
            failed_stage=model.failed_stage,
            failure_reason=model.failure_reason,
            machine_category=DocumentCategoryEnum(model.machine_category)
            if model.machine_category
            else None,
            category_confidence=model.category_confidence,
            category_evidence=evidence_list,
            human_category=DocumentCategoryEnum(model.human_category)
            if model.human_category
            else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            engagement_id=document.engagement_id,
            filename=document.filename,
            original_path=document.original_path,
            stored_path=document.stored_path,
            content_hash=document.content_hash,
            mime_type=document.mime_type,
            file_size_bytes=document.file_size_bytes,
            page_count=document.page_count,
            document_category=document.document_category.value,
            status=document.status.value,
            failed_stage=document.failed_stage,
            failure_reason=document.failure_reason,
            machine_category=document.machine_category.value if document.machine_category else None,
            category_confidence=document.category_confidence,
            category_evidence_json=json.dumps(document.category_evidence),
            human_category=document.human_category.value if document.human_category else None,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    add_document = add

    def add_page(self, page: DocumentPage) -> DocumentPage:
        conf = getattr(page, "ocr_confidence", getattr(page, "confidence_score", 1.0)) or 1.0
        model = DocumentPageModel(
            id=page.id,
            document_id=page.document_id,
            page_number=page.page_number,
            extracted_text=page.extracted_text,
            text_source=page.text_source.value
            if hasattr(page.text_source, "value")
            else str(page.text_source),
            ocr_applied=page.ocr_applied,
            confidence_score=conf,
            layout_json=page.layout_json,
        )
        self.session.add(model)
        self.session.flush()
        return page

    def add_pages(self, pages: list[DocumentPage]) -> list[DocumentPage]:
        return [self.add_page(p) for p in pages]

    def add_tables(self, tables: list[DocumentTable]) -> None:
        models = [
            DocumentTableModel(
                id=tbl.id,
                document_id=tbl.document_id,
                page_number=tbl.page_number,
                table_index=tbl.table_index,
                rows_json=tbl.rows_json,
                bbox_json=tbl.bbox_json,
                created_at=tbl.created_at,
            )
            for tbl in tables
        ]
        self.session.add_all(models)
        self.session.flush()

    def index_pages_fts(
        self, engagement_id: str, document_id: str, pages: list[DocumentPage]
    ) -> None:
        """Insert page texts into SQLite FTS5 virtual table for engagement-isolated search."""
        for p in pages:
            if p.extracted_text and p.extracted_text.strip():
                self.session.execute(
                    text("""
                        INSERT INTO document_fts (engagement_id, document_id, page_id, page_number, extracted_text)
                        VALUES (:eng_id, :doc_id, :page_id, :page_num, :text);
                    """),
                    {
                        "eng_id": engagement_id,
                        "doc_id": document_id,
                        "page_id": p.id,
                        "page_num": p.page_number,
                        "text": p.extracted_text,
                    },
                )
        self.session.flush()

    def get_by_id(self, document_id: str) -> Document | None:
        model = self.session.get(DocumentModel, document_id)
        return self._to_entity(model) if model else None

    def get_by_hash(self, engagement_id: str, content_hash: str) -> Document | None:
        stmt = select(DocumentModel).where(
            DocumentModel.engagement_id == engagement_id,
            DocumentModel.content_hash == content_hash,
            DocumentModel.status != DocumentStatusEnum.DELETED.value,
        )
        model = self.session.scalars(stmt).first()
        return self._to_entity(model) if model else None

    def list_by_engagement(self, engagement_id: str) -> list[Document]:
        stmt = (
            select(DocumentModel)
            .where(
                DocumentModel.engagement_id == engagement_id,
                DocumentModel.status != DocumentStatusEnum.DELETED.value,
            )
            .order_by(DocumentModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

    def get_document_pages(self, document_id: str) -> list[DocumentPage]:
        stmt = (
            select(DocumentPageModel)
            .where(DocumentPageModel.document_id == document_id)
            .order_by(DocumentPageModel.page_number.asc())
        )
        models = self.session.scalars(stmt).all()
        return [
            DocumentPage(
                id=m.id,
                document_id=m.document_id,
                page_number=m.page_number,
                extracted_text=m.extracted_text,
                text_source=TextSourceEnum(m.text_source)
                if m.text_source in TextSourceEnum._value2member_map_
                else TextSourceEnum.BORN_DIGITAL,
                ocr_applied=m.ocr_applied,
                confidence_score=m.confidence_score,
                layout_json=m.layout_json,
            )
            for m in models
        ]

    def update_category(self, document_id: str, category: DocumentCategoryEnum | str) -> Document:
        model = self.session.get(DocumentModel, document_id)
        if not model:
            raise ValueError(f"Document '{document_id}' not found.")
        cat_str = category.value if hasattr(category, "value") else str(category)
        model.human_category = cat_str
        model.document_category = cat_str
        self.session.flush()
        return self._to_entity(model)

    def search_pages(self, engagement_id: str, query: str) -> list[tuple[Document, DocumentPage]]:
        """Perform FTS5 full-text search strictly isolated within the engagement boundary."""
        if not query or not query.strip():
            return []

        import re

        words = re.findall(r"\w+", query)
        if not words:
            return []

        match_expr = " OR ".join(f'"{w}"' for w in words)

        fts_sql = text("""
            SELECT f.document_id, f.page_id, f.page_number, f.extracted_text
            FROM document_fts f
            WHERE f.engagement_id = :eng_id AND f.extracted_text MATCH :match_query;
        """)

        try:
            rows = self.session.execute(
                fts_sql, {"eng_id": engagement_id, "match_query": match_expr}
            ).fetchall()
        except Exception:
            rows = []

        if not rows:
            # Fallback: query document_pages table directly for engagement
            stmt = (
                select(DocumentPageModel)
                .join(DocumentModel, DocumentPageModel.document_id == DocumentModel.id)
                .where(
                    DocumentModel.engagement_id == engagement_id,
                    DocumentModel.status != DocumentStatusEnum.DELETED.value,
                )
            )
            page_models = self.session.scalars(stmt).all()
            rows = [(p.document_id, p.id, p.page_number, p.extracted_text) for p in page_models]

        results: list[tuple[Document, DocumentPage]] = []

        for doc_id, page_id, page_num, text_content in rows:
            doc_model = self.session.get(DocumentModel, doc_id)
            if doc_model and doc_model.status != DocumentStatusEnum.DELETED.value:
                doc = self._to_entity(doc_model)
                page = DocumentPage(
                    id=page_id,
                    document_id=doc_id,
                    page_number=int(page_num),
                    extracted_text=text_content or "",
                    text_source=TextSourceEnum.BORN_DIGITAL,
                    ocr_applied=False,
                    confidence_score=1.0,
                )
                results.append((doc, page))

        return results

    search_text = search_pages

    def soft_delete(self, document_id: str) -> bool:
        """Soft delete document, removing it from FTS index while preserving hash audit provenance."""
        model = self.session.get(DocumentModel, document_id)
        if model:
            model.status = DocumentStatusEnum.DELETED.value
            self.session.execute(
                text("DELETE FROM document_fts WHERE document_id = :doc_id;"),
                {"doc_id": document_id},
            )
            self.session.flush()
            return True
        return False
