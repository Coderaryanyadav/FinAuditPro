"""Document Viewer Dialog with native QPdfView, Extracted Text, Table Inspector, and Evidence Linking."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.document_service import (
    CreateEvidenceLinkDTO,
    DocumentDetailsDTO,
    DocumentService,
)
from finauditpro.domain.document_entities import DocumentCategoryEnum
from finauditpro.ui.theme import CardWidget

try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView

    QT_PDF_AVAILABLE = True
except ImportError:
    QT_PDF_AVAILABLE = False


class DocumentViewerDialog(QDialog):
    """Dialog for inspecting native document pages, extracted text, OCR metrics, tables, and evidence links."""

    def __init__(self, document_service: DocumentService, document_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document_service = document_service
        self.document_id = document_id
        self.details: DocumentDetailsDTO = self.document_service.get_document_details(document_id)

        self.setWindowTitle(f"Document Inspection — {self.details.document.filename}")
        self.resize(900, 700)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        doc = self.details.document

        # Header Info Card
        header_card = CardWidget()
        h_layout = QHBoxLayout()

        info_box = QVBoxLayout()
        title = QLabel(doc.filename)
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")

        size_mb = doc.file_size_bytes / (1024 * 1024)
        hash_snip = f"{doc.content_hash[:16]}..."
        status_color = "#10b981" if doc.status.value in ("Ready", "Completed") else "#ef4444"
        meta_str = f"Status: <span style='color:{status_color};font-weight:bold;'>{doc.status.value}</span> | Size: {size_mb:.2f} MB | Pages: {doc.page_count} | SHA-256: {hash_snip}"

        meta_lbl = QLabel(meta_str)
        meta_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")

        info_box.addWidget(title)
        info_box.addWidget(meta_lbl)
        h_layout.addLayout(info_box, stretch=1)

        # Category Override Box
        cat_box = QHBoxLayout()
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #f8fafc;")

        self.cat_combo = QComboBox()
        for cat in DocumentCategoryEnum:
            self.cat_combo.addItem(cat.value, cat)

        curr_cat = doc.human_category or doc.document_category
        idx = self.cat_combo.findText(curr_cat.value)
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)

        self.cat_combo.currentIndexChanged.connect(self._on_category_changed)

        cat_box.addWidget(cat_lbl)
        cat_box.addWidget(self.cat_combo)
        h_layout.addLayout(cat_box)

        header_card.content_layout.addLayout(h_layout)
        layout.addWidget(header_card)

        # Tabbed Viewer Body
        self.tabs = QTabWidget()

        # Tab 1: Extracted Text & Provenance
        self.text_tab = QWidget()
        self._init_text_tab()
        self.tabs.addTab(self.text_tab, "Extracted Text & Provenance")

        # Tab 2: Document Preview (Native QPdfView / Image)
        self.preview_tab = QWidget()
        self._init_preview_tab()
        self.tabs.addTab(self.preview_tab, "Native Preview")

        # Tab 3: Tables (if extracted)
        self.table_tab = QWidget()
        self._init_table_tab()
        self.tabs.addTab(self.table_tab, f"Structured Tables ({len(self.details.tables)})")

        # Tab 4: Evidence Links
        self.evidence_tab = QWidget()
        self._init_evidence_tab()
        self.tabs.addTab(self.evidence_tab, f"Evidence Links ({len(self.details.evidence_links)})")

        layout.addWidget(self.tabs, stretch=1)

        # Footer Actions
        footer = QHBoxLayout()

        link_btn = QPushButton("+ Link Page as Evidence")
        link_btn.clicked.connect(self._on_link_evidence_clicked)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("SecondaryButton")
        close_btn.clicked.connect(self.accept)

        footer.addWidget(link_btn)
        footer.addStretch()
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _init_text_tab(self) -> None:
        t_layout = QVBoxLayout(self.text_tab)
        t_layout.setContentsMargins(12, 12, 12, 12)

        # Page selector combo
        page_box = QHBoxLayout()
        page_lbl = QLabel("Page:")
        page_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #f8fafc;")

        self.page_combo = QComboBox()
        for p in range(1, self.details.document.page_count + 1):
            self.page_combo.addItem(f"Page {p} of {self.details.document.page_count}", p)

        if self.details.document.page_count == 0:
            self.page_combo.addItem("No Pages Extracted", 0)

        self.page_combo.currentIndexChanged.connect(self._on_page_changed)

        self.provenance_badge = QLabel("")
        self.provenance_badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #38bdf8; padding-left: 12px;")

        page_box.addWidget(page_lbl)
        page_box.addWidget(self.page_combo)
        page_box.addWidget(self.provenance_badge)
        page_box.addStretch()

        t_layout.addLayout(page_box)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #121418;
                color: #f8fafc;
                font-family: monospace;
                font-size: 12px;
                border: 1px solid #2e3440;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        t_layout.addWidget(self.text_edit, stretch=1)

        self._load_page_text(1)

    def _init_preview_tab(self) -> None:
        p_layout = QVBoxLayout(self.preview_tab)
        p_layout.setContentsMargins(12, 12, 12, 12)

        stored_file = Path(self.details.document.stored_path)
        if stored_file.is_file() and stored_file.suffix.lower() == ".pdf" and QT_PDF_AVAILABLE:
            pdf_doc = QPdfDocument(self)
            pdf_doc.load(str(stored_file))

            pdf_view = QPdfView(self)
            pdf_view.setDocument(pdf_doc)
            p_layout.addWidget(pdf_view, stretch=1)
        elif stored_file.is_file() and stored_file.suffix.lower() in (
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
        ):
            pixmap = QPixmap(str(stored_file))
            lbl = QLabel()
            lbl.setPixmap(
                pixmap.scaled(
                    700,
                    500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            p_layout.addWidget(lbl, stretch=1)
        else:
            lbl = QLabel(f"Native document preview for stored file:\n'{stored_file.name}'")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
            p_layout.addWidget(lbl, stretch=1)

    def _init_table_tab(self) -> None:
        tbl_layout = QVBoxLayout(self.table_tab)
        tbl_layout.setContentsMargins(12, 12, 12, 12)

        self.table_widget = QTableWidget()
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl_layout.addWidget(self.table_widget, stretch=1)

        self._load_tables()

    def _load_tables(self) -> None:
        if not self.details.tables:
            self.table_widget.setRowCount(1)
            self.table_widget.setColumnCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("No structured tables extracted from document."))
            return

        first_tbl = self.details.tables[0]
        try:
            rows = json.loads(first_tbl.rows_json)
        except Exception:
            rows = []

        if not rows:
            return

        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(rows[0]))

        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                self.table_widget.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

    def _init_evidence_tab(self) -> None:
        ev_layout = QVBoxLayout(self.evidence_tab)
        ev_layout.setContentsMargins(12, 12, 12, 12)

        self.evidence_table = QTableWidget()
        self.evidence_table.setColumnCount(4)
        self.evidence_table.setHorizontalHeaderLabels(["Page", "Target Type", "Title / Target", "Snippet"])
        self.evidence_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.evidence_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.evidence_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.evidence_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        ev_layout.addWidget(self.evidence_table, stretch=1)

        self._refresh_evidence_table()

    def _refresh_evidence_table(self) -> None:
        links = self.details.evidence_links
        self.evidence_table.setRowCount(0)

        for row, link in enumerate(links):
            self.evidence_table.insertRow(row)
            self.evidence_table.setItem(row, 0, QTableWidgetItem(str(link.page_number)))
            self.evidence_table.setItem(row, 1, QTableWidgetItem(link.target_type))
            self.evidence_table.setItem(row, 2, QTableWidgetItem(link.title))
            self.evidence_table.setItem(row, 3, QTableWidgetItem(link.snippet or "-"))

    def _load_page_text(self, page_num: int) -> None:
        if not self.details.pages or page_num < 1 or page_num > len(self.details.pages):
            self.text_edit.setText("[No page text available.]")
            self.provenance_badge.setText("")
            return

        page_data = self.details.pages[page_num - 1]
        text = page_data.extracted_text
        source = page_data.text_source.value if hasattr(page_data.text_source, "value") else str(page_data.text_source)
        conf = page_data.confidence_score or 1.0

        self.provenance_badge.setText(f"Source: {source} | OCR Confidence: {conf:.0%}")
        self.text_edit.setText(text if text else "[Empty Page]")

    def _on_page_changed(self, index: int) -> None:
        p = self.page_combo.currentData()
        if p and isinstance(p, int):
            self._load_page_text(p)

    def _on_category_changed(self, index: int) -> None:
        new_cat = self.cat_combo.currentData()
        if new_cat:
            self.document_service.override_document_category(self.details.document.id, new_cat)

    def _on_link_evidence_clicked(self) -> None:
        page_num = self.page_combo.currentData() or 1
        sel_text = self.text_edit.textCursor().selectedText()

        dialog = LinkEvidenceDialog(
            document_name=self.details.document.filename,
            page_number=page_num,
            selected_snippet=sel_text,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dto = CreateEvidenceLinkDTO(
                engagement_id=self.details.document.engagement_id,
                document_id=self.details.document.id,
                page_number=page_num,
                target_type=dialog.target_type_input.text().strip() or "Audit Finding",
                title=dialog.title_input.text().strip(),
                snippet=dialog.snippet_input.text().strip(),
            )
            saved_link = self.document_service.create_evidence_link(dto)
            self.details.evidence_links.append(saved_link)
            self._refresh_evidence_table()
            self.tabs.setCurrentWidget(self.evidence_tab)
            QMessageBox.information(self, "Evidence Linked", "Page successfully linked as audit evidence.")


class LinkEvidenceDialog(QDialog):
    """Dialog for defining evidence link title, target type, and snippet."""

    def __init__(
        self,
        document_name: str,
        page_number: int,
        selected_snippet: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Link Page as Audit Evidence")
        self.resize(500, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_lbl = QLabel(f"Linking '{document_name}' — Page {page_number}")
        info_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(info_lbl)

        form = QFormLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Verification of Section 80C Tax Deduction")
        self.title_input.setText(f"Page {page_number} Evidence")

        self.target_type_input = QLineEdit()
        self.target_type_input.setText("Audit Finding")

        self.snippet_input = QLineEdit()
        self.snippet_input.setText(selected_snippet)

        form.addRow("Evidence Title:", self.title_input)
        form.addRow("Audit Target Type:", self.target_type_input)
        form.addRow("Excerpt / Snippet:", self.snippet_input)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Create Evidence Link")
        save_btn.clicked.connect(self.accept)

        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)
