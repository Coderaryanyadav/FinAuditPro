"""Document processing pipeline orchestrator executing stage transitions, security validation, text extraction, OCR, heuristic classification, and FTS5 indexing."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from finauditpro.domain.document_entities import (
    DocumentCategoryEnum,
    DocumentPage,
    DocumentStatusEnum,
    DocumentTable,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.infrastructure.documents.document_classifier import classify_document_text
from finauditpro.infrastructure.documents.document_extractors import (
    extract_document_content,
)
from finauditpro.infrastructure.documents.document_security import (
    DocumentSecurityError,
    detect_mime_type,
    get_native_storage_dir,
    sanitize_filename,
    validate_document_security,
)


@dataclass
class ProcessedDocumentResult:
    filename: str
    original_path: str
    stored_path: str
    content_hash: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    status: DocumentStatusEnum
    failed_stage: str | None
    failure_reason: str | None
    machine_category: DocumentCategoryEnum
    category_confidence: float
    category_evidence: list[str]
    pages: list[DocumentPage]
    tables: list[DocumentTable]
    audit_events: list[AuditEvent]


class DocumentPipeline:
    """Orchestrates document ingestion across explicit, inspectable processing stages."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or get_native_storage_dir()

    def process_incoming_file(
        self,
        engagement_id: str,
        source_path: Path | str,
        category: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL,
    ) -> ProcessedDocumentResult:
        """Run complete document lifecycle: Upload -> Validate -> Store -> Extract -> OCR -> Classify -> Ready."""
        path = Path(source_path)
        events: list[AuditEvent] = []

        # Stage 1: UPLOADED
        events.append(
            AuditEvent(
                engagement_id=engagement_id,
                actor="System",
                action="Document Upload Started",
                details=f"File: '{path.name}'",
            )
        )

        # Stage 2: VALIDATING
        clean_name = path.name
        try:
            clean_name = sanitize_filename(path.name)
            content_hash = validate_document_security(path)
            mime_type = detect_mime_type(path)
            file_size = path.stat().st_size
            events.append(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="System",
                    action="Document Validation Passed",
                    details=f"MIME: '{mime_type}', Size: {file_size} bytes, SHA256: {content_hash[:12]}...",
                )
            )
        except DocumentSecurityError as sec_ex:
            events.append(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="System",
                    action="Document Quarantined",
                    details=f"Security check failed for '{path.name}': {sec_ex}",
                )
            )
            return ProcessedDocumentResult(
                filename=clean_name,
                original_path=str(path.resolve()),
                stored_path="",
                content_hash="0" * 64,
                mime_type="application/octet-stream",
                file_size_bytes=path.stat().st_size if path.exists() else 0,
                page_count=0,
                status=DocumentStatusEnum.QUARANTINED,
                failed_stage="VALIDATING",
                failure_reason=str(sec_ex),
                machine_category=DocumentCategoryEnum.GENERAL,
                category_confidence=0.0,
                category_evidence=[],
                pages=[],
                tables=[],
                audit_events=events,
            )

        # Stage 3: STORED
        eng_doc_dir = self.storage_dir / f"eng_{engagement_id}"
        eng_doc_dir.mkdir(parents=True, exist_ok=True)

        ext = path.suffix.lower()
        destination_path = eng_doc_dir / f"{content_hash}{ext}"

        try:
            if not destination_path.exists():
                shutil.copy2(path, destination_path)
            events.append(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="System",
                    action="Document Stored Immutably",
                    details=f"Destination: '{destination_path.name}'",
                )
            )
        except Exception as st_ex:
            return ProcessedDocumentResult(
                filename=clean_name,
                original_path=str(path.resolve()),
                stored_path="",
                content_hash=content_hash,
                mime_type=mime_type,
                file_size_bytes=file_size,
                page_count=0,
                status=DocumentStatusEnum.FAILED,
                failed_stage="STORED",
                failure_reason=f"Storage error: {st_ex}",
                machine_category=DocumentCategoryEnum.GENERAL,
                category_confidence=0.0,
                category_evidence=[],
                pages=[],
                tables=[],
                audit_events=events,
            )

        # Stage 4 & 5: EXTRACTING & OCR
        try:
            raw_pages, raw_tables = extract_document_content(destination_path, mime_type)

            doc_id = ""  # Populated downstream
            pages: list[DocumentPage] = [
                DocumentPage(
                    document_id=doc_id,
                    page_number=pg.page_number,
                    extracted_text=pg.text,
                    text_source=pg.text_source,
                    ocr_applied=pg.ocr_applied,
                    confidence_score=pg.confidence,
                    layout_json=pg.layout_json,
                )
                for pg in raw_pages
            ]

            tables: list[DocumentTable] = [
                DocumentTable(
                    document_id=doc_id,
                    page_number=tbl.page_number,
                    table_index=tbl.table_index,
                    rows_json=json.dumps(tbl.rows),
                    bbox_json=json.dumps(tbl.bbox) if tbl.bbox else None,
                )
                for tbl in raw_tables
            ]

            ocr_count = sum(1 for p in pages if p.ocr_applied)
            events.append(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor="System",
                    action="Text & Table Extraction Completed",
                    details=f"Extracted {len(pages)} pages ({ocr_count} via OCR, {len(tables)} tables).",
                )
            )
        except Exception as ext_ex:
            return ProcessedDocumentResult(
                filename=clean_name,
                original_path=str(path.resolve()),
                stored_path=str(destination_path.resolve()),
                content_hash=content_hash,
                mime_type=mime_type,
                file_size_bytes=file_size,
                page_count=0,
                status=DocumentStatusEnum.FAILED,
                failed_stage="EXTRACTING",
                failure_reason=f"Extraction error: {ext_ex}",
                machine_category=DocumentCategoryEnum.GENERAL,
                category_confidence=0.0,
                category_evidence=[],
                pages=[],
                tables=[],
                audit_events=events,
            )

        # Stage 6: CLASSIFYING
        full_text = "\n".join(p.extracted_text for p in pages)
        machine_cat, conf, evidence = classify_document_text(full_text, filename=clean_name)
        final_cat: DocumentCategoryEnum = category if category != DocumentCategoryEnum.GENERAL else machine_cat


        events.append(
            AuditEvent(
                engagement_id=engagement_id,
                actor="System",
                action="Document Classified",
                details=f"Category: '{final_cat.value}' (Confidence: {conf:.0%}, Evidence: {evidence[:3]})",
            )
        )

        # Stage 7: READY
        events.append(
            AuditEvent(
                engagement_id=engagement_id,
                actor="System",
                action="Document Pipeline Ready",
                details=f"Document '{clean_name}' ready for inspection & FTS search.",
            )
        )

        return ProcessedDocumentResult(
            filename=clean_name,
            original_path=str(path.resolve()),
            stored_path=str(destination_path.resolve()),
            content_hash=content_hash,
            mime_type=mime_type,
            file_size_bytes=file_size,
            page_count=len(pages),
            status=DocumentStatusEnum.READY,
            failed_stage=None,
            failure_reason=None,
            machine_category=final_cat,
            category_confidence=conf,
            category_evidence=evidence,
            pages=pages,
            tables=tables,
            audit_events=events,
        )
