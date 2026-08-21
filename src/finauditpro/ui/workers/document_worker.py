"""Asynchronous PySide6 worker thread for off-main-thread document processing."""

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.domain.document_entities import DocumentCategoryEnum


class DocumentProcessingWorker(QThread):
    """QThread executing document ingestion, extraction, OCR, and FTS indexing off the UI thread."""

    processing_started = Signal(str)  # filename
    processing_progress = Signal(str, int, int)  # stage_name, current_page, total_pages
    processing_completed = Signal(object)  # Document entity
    processing_failed = Signal(str, str)  # filename, error_message

    def __init__(
        self,
        document_service: DocumentService,
        engagement_id: str,
        file_path: str,
        category: DocumentCategoryEnum = DocumentCategoryEnum.GENERAL,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.document_service = document_service
        self.engagement_id = engagement_id
        self.file_path = file_path
        self.category = category

    def run(self) -> None:
        filename = Path(self.file_path).name
        self.processing_started.emit(filename)
        self.processing_progress.emit("Validating & Hashing", 0, 1)

        try:
            dto = UploadDocumentDTO(
                engagement_id=self.engagement_id,
                file_path=self.file_path,
                category=self.category,
            )

            self.processing_progress.emit("Extracting Text & OCR", 1, 1)
            doc = self.document_service.upload_and_process_document(dto)

            if doc.status == "Quarantined" or doc.status == "Failed":
                self.processing_failed.emit(
                    filename, doc.failure_reason or "Document processing failed."
                )
            else:
                self.processing_progress.emit("Ready", doc.page_count, doc.page_count)
                self.processing_completed.emit(doc)

        except Exception as ex:
            self.processing_failed.emit(filename, str(ex))
