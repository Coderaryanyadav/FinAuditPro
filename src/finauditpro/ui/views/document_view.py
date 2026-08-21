"""Primary Document Intelligence Workspace View for FinAuditPro."""

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
from finauditpro.ui.theme import CardWidget
from finauditpro.ui.workers.document_worker import DocumentProcessingWorker


class DocumentView(QWidget):
    """Document Intelligence Workspace View supporting asynchronous uploads, FTS search, category filters, and evidence linking."""

    document_changed = Signal()

    def __init__(self, document_service: DocumentService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document_service = document_service
        self.current_engagement_id: str | None = None
        self.active_workers: list[DocumentProcessingWorker] = []

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Row
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Document Intelligence Workspace")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")

        self.upload_btn = QPushButton("+ Upload Document")
        self.upload_btn.clicked.connect(self._on_upload_clicked)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.upload_btn)

        layout.addLayout(header_layout)

        # Search Bar & Category Filter Row
        search_card = CardWidget()
        s_layout = QHBoxLayout()

        search_lbl = QLabel("Search Engagement Documents (FTS5):")
        search_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Enter keyword (e.g. GST, Bank Balance, Section 80C, Invoice)..."
        )
        self.search_input.returnPressed.connect(self._on_search)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("SecondaryButton")
        search_btn.clicked.connect(self._on_search)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self._on_clear_search)

        s_layout.addWidget(search_lbl)
        s_layout.addWidget(self.search_input, stretch=1)
        s_layout.addWidget(search_btn)
        s_layout.addWidget(clear_btn)

        search_card.content_layout.addLayout(s_layout)
        layout.addWidget(search_card)

        # Document Directory Table
        card = CardWidget()
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Filename", "Category", "Size", "Pages", "SHA-256 Hash", "Status", "Uploaded"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)

        card.content_layout.addWidget(self.table)
        layout.addWidget(card)

    def set_engagement(self, engagement_id: str | None) -> None:
        self.current_engagement_id = engagement_id
        if engagement_id:
            self.title_label.setText("Document Intelligence Workspace")
            self.upload_btn.setEnabled(True)
        else:
            self.title_label.setText("Document Intelligence Workspace (Select Engagement)")
            self.upload_btn.setEnabled(False)
        self.refresh()

    def refresh(self) -> None:
        if not self.current_engagement_id:
            self.table.setRowCount(0)
            return

        docs = self.document_service.list_documents_for_engagement(self.current_engagement_id)
        self.table.setRowCount(0)

        for row, doc in enumerate(docs):
            self.table.insertRow(row)

            item_name = QTableWidgetItem(doc.filename)
            item_name.setData(Qt.ItemDataRole.UserRole, doc.id)

            size_mb = doc.file_size_bytes / (1024 * 1024)
            size_str = (
                f"{doc.file_size_bytes / 1024:.1f} KB" if size_mb < 1.0 else f"{size_mb:.1f} MB"
            )
            hash_str = f"{doc.content_hash[:12]}..." if doc.content_hash else "-"

            cat_str = (
                doc.human_category.value if doc.human_category else doc.document_category.value
            )

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(cat_str))
            self.table.setItem(row, 2, QTableWidgetItem(size_str))
            self.table.setItem(row, 3, QTableWidgetItem(str(doc.page_count)))
            self.table.setItem(row, 4, QTableWidgetItem(hash_str))

            status_val = doc.status.value if hasattr(doc.status, "value") else str(doc.status)
            status_item = QTableWidgetItem(status_val)
            if status_val in ("Ready", "Completed", "Indexed"):
                status_item.setForeground(Qt.GlobalColor.green)
            elif status_val in ("Failed", "Quarantined"):
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 5, status_item)
            self.table.setItem(row, 6, QTableWidgetItem(doc.created_at.strftime("%Y-%m-%d %H:%M")))

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
            self,
            "Upload & Processing Complete",
            "Document successfully processed and indexed into FTS5.",
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
        self.table.setRowCount(0)

        for row, res in enumerate(results):
            self.table.insertRow(row)

            item_name = QTableWidgetItem(f"{res.filename} (Page {res.page_number})")
            item_name.setData(Qt.ItemDataRole.UserRole, res.document_id)

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, QTableWidgetItem(res.document_category))
            self.table.setItem(row, 2, QTableWidgetItem("-"))
            self.table.setItem(row, 3, QTableWidgetItem(f"Page {res.page_number}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"Source: {res.text_source}"))
            self.table.setItem(row, 5, QTableWidgetItem(res.snippet))
            self.table.setItem(row, 6, QTableWidgetItem("Match Found"))

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
