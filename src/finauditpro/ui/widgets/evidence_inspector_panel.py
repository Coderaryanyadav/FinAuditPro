"""Evidence Inspector Panel for right pane of Unified Working Paper Workspace."""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.document_service import DocumentDetailsDTO, DocumentService
from finauditpro.ui.theme import CardWidget
from finauditpro.ui.widgets.custom_combo import CustomComboBox


class EvidenceInspectorPanel(QWidget):
    """Right-pane panel for native document viewing, page navigation, text highlighting, and SHA-256 verification."""

    attach_evidence_requested = Signal(str, int, str)  # (document_id, page_number, excerpt)
    document_changed = Signal(str)  # (document_id)

    def __init__(
        self,
        document_service: DocumentService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.document_service = document_service
        self.current_document_id: str | None = None
        self.current_details: DocumentDetailsDTO | None = None
        self.current_page: int = 1
        self.documents_list: list[Any] = []

        self._init_ui()

    def set_document_service(self, service: DocumentService) -> None:
        self.document_service = service

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Document & Page Selector Card
        self.selector_card = CardWidget("EVIDENCE & DOCUMENT INSPECTOR")
        c_layout = QVBoxLayout()
        c_layout.setSpacing(8)

        # Document Dropdown Row
        doc_row = QHBoxLayout()
        doc_lbl = QLabel("Document:")
        doc_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self.combo_docs = CustomComboBox()
        self.combo_docs.currentIndexChanged.connect(self._on_doc_combo_changed)
        doc_row.addWidget(doc_lbl)
        doc_row.addWidget(self.combo_docs, stretch=1)
        c_layout.addLayout(doc_row)

        # Navigation & Page Row
        page_row = QHBoxLayout()
        page_lbl = QLabel("Page Navigation:")
        page_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")

        self.btn_prev_page = QPushButton("◀ Prev")
        self.btn_prev_page.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_prev_page.clicked.connect(self._prev_page)

        self.spin_page = QSpinBox()
        self.spin_page.setRange(1, 1)
        self.spin_page.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        self.spin_page.valueChanged.connect(self._on_page_spin_changed)

        self.lbl_max_pages = QLabel("/ 1")
        self.lbl_max_pages.setStyleSheet("font-size: 11px; color: #64748B;")

        self.btn_next_page = QPushButton("Next ▶")
        self.btn_next_page.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_next_page.clicked.connect(self._next_page)

        page_row.addWidget(page_lbl)
        page_row.addWidget(self.btn_prev_page)
        page_row.addWidget(self.spin_page)
        page_row.addWidget(self.lbl_max_pages)
        page_row.addWidget(self.btn_next_page)
        page_row.addStretch()

        c_layout.addLayout(page_row)
        self.selector_card.content_layout.addLayout(c_layout)
        layout.addWidget(self.selector_card)

        # 2. Document Details & Meta Badge
        self.lbl_meta = QLabel("No document selected.")
        self.lbl_meta.setWordWrap(True)
        self.lbl_meta.setStyleSheet(
            "background: #F8FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #475569;"
        )
        layout.addWidget(self.lbl_meta)

        # 3. Main Viewer Tabs
        self.tabs = QTabWidget()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 1px solid #CBD5E1; "
            "border-radius: 6px; font-family: monospace; font-size: 12px; padding: 8px; color: #0F172A; }"
        )
        self.text_edit.setPlaceholderText(
            "Select or click a working paper evidence link to inspect content."
        )

        self.tabs.addTab(self.text_edit, "Extracted Page Evidence")
        layout.addWidget(self.tabs, stretch=1)

        # 4. Action Footer
        footer = QHBoxLayout()
        self.btn_attach = QPushButton("+ Attach Page as Evidence to WP")
        self.btn_attach.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_attach.setStyleSheet(
            "QPushButton { background: #0F766E; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }\n"
            "QPushButton:hover { background: #0D9488; }"
        )
        self.btn_attach.clicked.connect(self._on_attach_clicked)
        footer.addWidget(self.btn_attach)
        footer.addStretch()
        layout.addLayout(footer)

    def load_engagement_documents(self, engagement_id: str | None) -> None:
        self.combo_docs.blockSignals(True)
        self.combo_docs.clear()
        self.documents_list = []
        if self.document_service and engagement_id:
            try:
                self.documents_list = (
                    self.document_service.list_documents_for_engagement(engagement_id)
                )
                for doc in self.documents_list:
                    self.combo_docs.addItem(f"📄 {doc.filename} (Pages: {doc.page_count})", doc.id)
            except Exception:
                pass

        if not self.documents_list:
            self.combo_docs.addItem("No Documents Found", None)
            self.btn_attach.setEnabled(False)
        else:
            self.btn_attach.setEnabled(True)
        self.combo_docs.blockSignals(False)

    def open_document_page(
        self, document_id: str, page_number: int = 1, highlight_text: str | None = None
    ) -> None:
        if not document_id or not self.document_service:
            return

        self.current_document_id = document_id
        try:
            self.current_details = self.document_service.get_document_details(document_id)
        except Exception:
            self.current_details = None
            self.text_edit.setPlainText(f"Unable to load document details for ID: {document_id}")
            return

        if not self.current_details or not self.current_details.document:
            return

        doc = self.current_details.document
        idx = self.combo_docs.findData(document_id)
        if idx >= 0:
            self.combo_docs.blockSignals(True)
            self.combo_docs.setCurrentIndex(idx)
            self.combo_docs.blockSignals(False)

        max_p = max(1, doc.page_count)
        self.spin_page.blockSignals(True)
        self.spin_page.setMaximum(max_p)
        page_num = max(1, min(page_number, max_p))
        self.spin_page.setValue(page_num)
        self.lbl_max_pages.setText(f"/ {max_p}")
        self.spin_page.blockSignals(False)
        self.current_page = page_num

        hash_snip = f"{doc.content_hash[:16]}..." if doc.content_hash else "N/A"
        cat_val = (
            doc.document_category.value
            if hasattr(doc.document_category, "value")
            else str(doc.document_category)
        )
        meta_html = (
            f"<b>{doc.filename}</b> | Category: <b>{cat_val}</b><br/>"
            f"Page {page_num} of {max_p} | SHA-256: <code style='color:#2563EB;'>{hash_snip}</code>"
        )
        self.lbl_meta.setText(meta_html)

        self._display_page_content(page_num, highlight_text)

    def _display_page_content(self, page_num: int, highlight_text: str | None = None) -> None:
        if not self.current_details:
            return

        page_texts = self.current_details.page_texts
        fallback_msg = (
            f"--- Page {page_num} Extracted Text ---\n(No text extracted for page {page_num})"
        )
        content = page_texts.get(page_num, fallback_msg)
        self.text_edit.setPlainText(content)

        if highlight_text and highlight_text.strip():
            cursor = self.text_edit.textCursor()
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#FEF08A"))  # Soft Yellow highlight
            fmt.setForeground(QColor("#854D0E"))

            pattern = highlight_text.strip()
            found = False
            cursor.setPosition(0)
            while not cursor.atEnd():
                cursor = self.text_edit.document().find(pattern, cursor)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(fmt)
                found = True

            if not found:
                # Fallback: highlight first matching term
                terms = [t for t in pattern.split() if len(t) > 3]
                for term in terms[:3]:
                    c = self.text_edit.document().find(term, 0)
                    if not c.isNull():
                        c.mergeCharFormat(fmt)

    def _on_doc_combo_changed(self, idx: int) -> None:
        doc_id = self.combo_docs.currentData()
        if doc_id and doc_id != self.current_document_id:
            self.open_document_page(doc_id, page_number=1)
            self.document_changed.emit(doc_id)

    def _on_page_spin_changed(self, val: int) -> None:
        if self.current_document_id:
            self.current_page = val
            self._display_page_content(val)

    def _prev_page(self) -> None:
        if self.spin_page.value() > 1:
            self.spin_page.setValue(self.spin_page.value() - 1)

    def _next_page(self) -> None:
        if self.spin_page.value() < self.spin_page.maximum():
            self.spin_page.setValue(self.spin_page.value() + 1)

    def _on_attach_clicked(self) -> None:
        if not self.current_document_id:
            return
        excerpt = self.text_edit.textCursor().selectedText().strip()
        if not excerpt:
            excerpt = self.text_edit.toPlainText()[:200].strip()
        self.attach_evidence_requested.emit(self.current_document_id, self.current_page, excerpt)
