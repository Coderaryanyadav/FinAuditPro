"""
Interactive Embedded PDF Viewer Component for FinAuditPro.
Uses PySide6.QtPdf / PySide6.QtPdfWidgets for native, high-DPI PDF document rendering,
page navigation, zoom controls, and smooth scrolling.
"""

import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QStackedWidget, QSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

from .styles import EmptyStateWidget, apply_shadow

logger = logging.getLogger(__name__)

class PDFViewerWidget(QWidget):
    """
    Embedded High-DPI Interactive PDF Document Viewer.
    Features:
    - Page Stepper: Prev/Next & Jump to Page
    - Zoom Controls: Zoom In (+), Zoom Out (-), Fit Width, Fit Page
    - Native PySide6 QtPdf Engine
    - Graceful fallback for unparseable or non-PDF files
    """

    page_changed = Signal(int, int) # current_page, total_pages

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._total_pages = 0
        self._zoom_factor = 1.0

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Control Toolbar
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(44)
        self.toolbar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 4px 12px;
            }
            QPushButton {
                background-color: #f8fafc;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #475569;
                border: none;
            }
        """)

        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(8)

        # Page Navigation
        self.btn_prev = QPushButton("◄ Prev")
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.clicked.connect(self.prev_page)

        self.lbl_page_info = QLabel("Page 0 of 0")

        self.btn_next = QPushButton("Next ►")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self.next_page)

        tb_layout.addWidget(self.btn_prev)
        tb_layout.addWidget(self.lbl_page_info)
        tb_layout.addWidget(self.btn_next)

        tb_layout.addSpacing(16)

        # Divider
        div1 = QFrame()
        div1.setFixedSize(1, 20)
        div1.setStyleSheet("background-color: #cbd5e1;")
        tb_layout.addWidget(div1)

        tb_layout.addSpacing(8)

        # Zoom Controls
        self.btn_zoom_out = QPushButton("Zoom -")
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.lbl_zoom_val = QLabel("100%")

        self.btn_zoom_in = QPushButton("Zoom +")
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        self.btn_fit_width = QPushButton("Fit Width")
        self.btn_fit_width.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fit_width.clicked.connect(self.fit_width)

        self.btn_fit_page = QPushButton("Fit Page")
        self.btn_fit_page.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fit_page.clicked.connect(self.fit_page)

        tb_layout.addWidget(self.btn_zoom_out)
        tb_layout.addWidget(self.lbl_zoom_val)
        tb_layout.addWidget(self.btn_zoom_in)
        tb_layout.addWidget(self.btn_fit_width)
        tb_layout.addWidget(self.btn_fit_page)

        tb_layout.addStretch()

        main_layout.addWidget(self.toolbar)

        # 2. Main Stack (PdfView vs Empty/Error State)
        self.stack = QStackedWidget()
        
        # Page 0: Empty state
        self.empty_widget = EmptyStateWidget(
            title="No PDF Loaded",
            description="Select a valid PDF document from the audit workspace to view interactive page rendering."
        )
        self.stack.addWidget(self.empty_widget)

        # Page 1: Native QPdfView
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_view.setStyleSheet("background-color: #525659; border: none;")
        self.stack.addWidget(self.pdf_view)

        main_layout.addWidget(self.stack, 1)

        # Connect QPdfView page navigator signals if available
        try:
            navigator = self.pdf_view.pageNavigator()
            navigator.currentPageChanged.connect(self._on_page_navigated)
        except Exception:
            pass

    def load_pdf(self, file_path: str) -> bool:
        """Loads and displays a PDF file in the embedded view."""
        if not file_path or not os.path.exists(file_path):
            self.stack.setCurrentIndex(0)
            self._update_toolbar_state(0, 0)
            return False

        if not file_path.lower().endswith(".pdf"):
            self.stack.setCurrentIndex(0)
            self._update_toolbar_state(0, 0)
            return False

        try:
            self._current_path = file_path
            self.pdf_document.load(file_path)
            self._total_pages = self.pdf_document.pageCount()

            if self._total_pages > 0:
                self.stack.setCurrentIndex(1)
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
                self._zoom_factor = 1.0
                self._update_toolbar_state(1, self._total_pages)
                return True
            else:
                self.stack.setCurrentIndex(0)
                self._update_toolbar_state(0, 0)
                return False

        except Exception as e:
            logger.error(f"Failed to load PDF document '{file_path}': {e}")
            self.stack.setCurrentIndex(0)
            self._update_toolbar_state(0, 0)
            return False

    def _update_toolbar_state(self, page_num: int, total_pages: int):
        self.lbl_page_info.setText(f"Page {page_num} of {total_pages}")
        self.btn_prev.setEnabled(page_num > 1)
        self.btn_next.setEnabled(page_num < total_pages)
        self.lbl_zoom_val.setText(f"{int(self._zoom_factor * 100)}%")

    def _on_page_navigated(self, page_idx: int):
        current = page_idx + 1
        self._update_toolbar_state(current, self._total_pages)
        self.page_changed.emit(current, self._total_pages)

    def prev_page(self):
        try:
            nav = self.pdf_view.pageNavigator()
            if nav.currentPage() > 0:
                nav.jump(nav.currentPage() - 1, nav.location())
        except Exception:
            pass

    def next_page(self):
        try:
            nav = self.pdf_view.pageNavigator()
            if nav.currentPage() < self._total_pages - 1:
                nav.jump(nav.currentPage() + 1, nav.location())
        except Exception:
            pass

    def zoom_in(self):
        self._zoom_factor = min(self._zoom_factor * 1.25, 3.0)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self._zoom_factor)
        self.lbl_zoom_val.setText(f"{int(self._zoom_factor * 100)}%")

    def zoom_out(self):
        self._zoom_factor = max(self._zoom_factor / 1.25, 0.4)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self._zoom_factor)
        self.lbl_zoom_val.setText(f"{int(self._zoom_factor * 100)}%")

    def fit_width(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self._zoom_factor = 1.0
        self.lbl_zoom_val.setText("100%")

    def fit_page(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        self._zoom_factor = 1.0
        self.lbl_zoom_val.setText("Fit")
