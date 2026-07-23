from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

GLOBAL_QSS = """
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
}

/* Base Window & Widget Backgrounds */
QMainWindow, QDialog, QWidget#appBg {
    background-color: #f8fafc;
}

/* Custom Sleek Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #0ea5e9;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #0ea5e9;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

/* Line Edits & Text Inputs */
QLineEdit, QTextEdit {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 9px 14px;
    background-color: #ffffff;
    font-size: 13px;
    color: #0f172a;
    selection-background-color: #e0f2fe;
}
QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #0ea5e9;
    background-color: #ffffff;
}

/* Dropdown ComboBoxes */
QComboBox {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 14px;
    background-color: #ffffff;
    color: #0f172a;
    font-size: 13px;
    font-weight: 600;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox:focus {
    border: 2px solid #0ea5e9;
}

/* Tables */
QTableWidget {
    background-color: #ffffff;
    gridline-color: #f1f5f9;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    font-size: 13px;
    outline: none;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 12px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
}
QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
}
QTableWidget::item:selected {
    background-color: #f0f9ff;
    color: #0284c7;
    font-weight: 600;
}

/* Buttons */
QPushButton {
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 8px;
    font-weight: 600;
    border: none;
}
QPushButton#primaryButton {
    background-color: #0ea5e9;
    color: #ffffff;
}
QPushButton#primaryButton:hover {
    background-color: #0284c7;
}
QPushButton#primaryButton:pressed {
    background-color: #0369a1;
}

/* Sidebar Navigation Buttons - FAIGN Dark Glassmorphism */
QPushButton#navButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding-left: 18px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#navButton:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #f8fafc;
}
QPushButton#navButton[active="true"] {
    background-color: #0ea5e9;
    color: #ffffff;
    padding-left: 18px;
    font-weight: 700;
}
"""

def apply_shadow(widget, blur=24, dx=0, dy=4, alpha=15):
    """Applies a clean, modern soft drop shadow effect to any QWidget."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)

class EmptyStateWidget(QWidget):
    """Reusable empty state component when tables/lists have no records."""
    def __init__(self, title: str = "No Records Found", description: str = "There is no data to display for the selected criteria."):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container = QFrame()
        container.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 32px;")
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("font-size: 32px; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #334155; border: none; margin-top: 8px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("font-size: 13px; color: #64748b; border: none; margin-top: 4px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        
        cl.addWidget(icon_lbl)
        cl.addWidget(title_lbl)
        cl.addWidget(desc_lbl)
        layout.addWidget(container)

class LoadingStateWidget(QWidget):
    """Reusable loading spinner/progress component during DB queries, LLM calls, or OCR processing."""
    def __init__(self, message: str = "Processing requested operation..."):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container = QFrame()
        container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;")
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #0ea5e9; border: none;")
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pbar = QProgressBar()
        pbar.setRange(0, 0)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet("""
            QProgressBar { border: none; background-color: #e0f2fe; border-radius: 3px; }
            QProgressBar::chunk { background-color: #0ea5e9; border-radius: 3px; }
        """)
        
        cl.addWidget(msg_lbl)
        cl.addWidget(pbar)
        layout.addWidget(container)

class ErrorStateWidget(QWidget):
    """Reusable explicit error banner component displaying exact details."""
    def __init__(self, title: str = "Operation Error", details: str = "An unexpected error occurred while executing the request."):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container = QFrame()
        container.setStyleSheet("background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 24px;")
        cl = QVBoxLayout(container)
        
        title_lbl = QLabel(f"⚠️ {title}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #dc2626; border: none;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        details_lbl = QLabel(str(details))
        details_lbl.setStyleSheet("font-size: 13px; color: #991b1b; border: none; margin-top: 8px;")
        details_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_lbl.setWordWrap(True)
        
        cl.addWidget(title_lbl)
        cl.addWidget(details_lbl)
        layout.addWidget(container)
