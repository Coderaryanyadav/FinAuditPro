"""
Document Intelligence Workspace View for FinAuditPro.
Enterprise document vault supporting FTS search, category filters, and evidence indexing.
"""
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.document_service import DocumentService
from finauditpro.domain.document_entities import DocumentCategoryEnum
from finauditpro.ui.dialogs.document_viewer_dialog import DocumentViewerDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, PageHeader
from finauditpro.ui.workers.document_worker import DocumentProcessingWorker


class DocumentView(QWidget):
    """Document Intelligence Workspace View supporting uploads, FTS search, and evidence linking."""

    document_changed = Signal()

    def __init__(self, document_service: DocumentService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document_service = document_service
        self.current_engagement_id: str | None = None
        self.active_workers: list[DocumentProcessingWorker] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Documents",
            subtitle="Upload, extract, and index audit evidence, bank statements, and trial balances.",
            action_text="+ Upload Document",
            action_callback=self._on_upload_clicked,
        )
        self.upload_btn = self.header.action_btn
        layout.addWidget(self.header)

        # 2. Search Bar Card
        search_card = CardWidget()
        s_layout = QHBoxLayout()
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(10)

        search_lbl = QLabel("Search:")
        search_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;"
        )

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search full text (FTS5) for keywords (e.g. GST, Bank Balance, Invoice)..."
        )
        self.search_input.setStyleSheet(
            "QLineEdit { border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 10px; font-size: 12px; background: #FFFFFF; }"
            "QLineEdit:focus { border-color: #2563EB; }"
        )
        self.search_input.returnPressed.connect(self._on_search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear_search)

        s_layout.addWidget(search_lbl)
        s_layout.addWidget(self.search_input, stretch=1)
        s_layout.addWidget(search_btn)
        s_layout.addWidget(clear_btn)
        search_card.content_layout.addLayout(s_layout)
        layout.addWidget(search_card)

        # 3. Document Directory Table Card & Empty State
        self.table_card = CardWidget("DOCUMENT EVIDENCE DIRECTORY")
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["FILENAME", "CATEGORY", "SIZE", "PAGES", "SHA-256 HASH", "STATUS", "UPLOADED"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 7):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_double_click)

        self.empty_state = EmptyStateWidget(
            title="No documents uploaded yet",
            description="Upload PDF, Excel, CSV, or image documents to enable OCR text extraction, FTS search, and AI copilot analysis.",
            action_text="+ Upload Document",
            action_callback=self._on_upload_clicked,
        )

        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

    def set_active_engagement(self, engagement: Any) -> None:
        if hasattr(engagement, "id"):
            self.set_engagement(engagement.id)
        elif engagement:
            self.set_engagement(str(engagement))
        else:
            self.set_engagement(None)

    def set_engagement(self, engagement_id: str | None) -> None:
        self.current_engagement_id = engagement_id
        if engagement_id:
            self.header.title_lbl.setText("Documents")
            self.header.action_btn.setEnabled(True)
        else:
            self.header.title_lbl.setText("Documents (Select Engagement)")
            self.header.action_btn.setEnabled(False)
        self.refresh()


    def refresh(self) -> None:
        if not self.current_engagement_id:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        docs = self.document_service.list_documents_for_engagement(self.current_engagement_id)
        if not docs:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        for row, doc in enumerate(docs):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(doc.filename)
            item_name.setData(Qt.ItemDataRole.UserRole, doc.id)

            size_mb = doc.file_size_bytes / (1024 * 1024)
            size_str = (
                f"{doc.file_size_bytes / 1024:.1f} KB" if size_mb < 1.0 else f"{size_mb:.1f} MB"
            )
            hash_str = f"{doc.content_hash[:12]}..." if doc.content_hash else "—"
            cat_str = (
                doc.human_category.value if doc.human_category else doc.document_category.value
            )

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(cat_str))
            self.table.setItem(row, 2, QTableWidgetItem(size_str))
            self.table.setItem(row, 3, QTableWidgetItem(str(doc.page_count)))
            self.table.setItem(row, 4, QTableWidgetItem(hash_str))

            status_val = doc.status.value if hasattr(doc.status, "value") else str(doc.status)
            self.table.setItem(row, 5, QTableWidgetItem(f"● {status_val}"))
            self.table.setItem(row, 6, QTableWidgetItem(doc.created_at.strftime("%Y-%m-%d %H:%M")))

        self.table.setFixedHeight(max(1, len(docs)) * 36 + 32)

    def _on_upload_clicked(self) -> None:
        if not self.current_engagement_id:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document to Upload",
            "",
            "Documents (*.pdf *.csv *.xlsx *.txt *.png *.jpg *.jpeg *.tiff);;All Files (*)",
        )
        if file_path:
            worker = DocumentProcessingWorker(
                document_service=self.document_service,
                engagement_id=self.current_engagement_id,
                file_path=file_path,
                category=DocumentCategoryEnum.GENERAL,
                parent=self,
            )
            worker.processing_completed.connect(self._on_worker_completed)
            worker.processing_failed.connect(self._on_worker_failed)
            self.active_workers.append(worker)
            worker.start()

    def _on_worker_completed(self, doc: object) -> None:
        QMessageBox.information(
            self, "Upload & Processing Complete", "Document successfully processed and indexed."
        )
        self.refresh()
        self.document_changed.emit()

    def _on_worker_failed(self, filename: str, error_message: str) -> None:
        QMessageBox.warning(
            self,
            "Document Processing Error",
            f"Processing failed for '{filename}':\n{error_message}",
        )
        self.refresh()

    def _on_search(self) -> None:
        query = self.search_input.text().strip()
        if not query or not self.current_engagement_id:
            self.refresh()
            return

        results = self.document_service.search_documents(self.current_engagement_id, query)
        if not results:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        for row, res in enumerate(results):
            self.table.insertRow(row)
            item_name = QTableWidgetItem(f"{res.filename} (Page {res.page_number})")
            item_name.setData(Qt.ItemDataRole.UserRole, res.document_id)
            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(res.document_category))
            self.table.setItem(row, 2, QTableWidgetItem("—"))
            self.table.setItem(row, 3, QTableWidgetItem(f"Page {res.page_number}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"Source: {res.text_source}"))
            self.table.setItem(row, 5, QTableWidgetItem("● Match Found"))
            self.table.setItem(
                row, 6, QTableWidgetItem(res.snippet[:40] if hasattr(res, "snippet") else "—")
            )

        self.table.setFixedHeight(max(1, len(results)) * 36 + 32)

    def _on_clear_search(self) -> None:
        self.search_input.clear()
        self.refresh()

    def _on_double_click(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item is not None:
                doc_id = item.data(Qt.ItemDataRole.UserRole)
                if doc_id:
                    try:
                        dialog = DocumentViewerDialog(self.document_service, doc_id, parent=self)
                        dialog.exec()
                    except Exception as ex:
                        QMessageBox.critical(self, "Error", f"Could not open document viewer: {ex}")
