from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

GLOBAL_QSS = """
* {
    font-family: 'Inter', 'SF Pro Display', 'Segoe UI', -apple-system, sans-serif;
    color: #0f172a; /* slate-900 */
}

/* Base Window Backgrounds */
QMainWindow, QDialog, QWidget#appBg {
    background-color: #f8fafc; /* slate-50 */
}

/* Custom Scrollbars */
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
    background: #94a3b8;
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
    background: #94a3b8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

/* Line Edits & Text Fields */
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
    border: 2px solid #0ea5e9; /* FinAuditPro Sky Blue */
    background-color: #ffffff;
}

/* ComboBoxes */
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

/* Table Widgets */
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
    color: #334155;
    padding: 12px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
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
    color: #0369a1;
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

/* Sidebar Navigation Buttons - Dark Theme High Contrast */
QPushButton#navButton {
    background-color: transparent;
    color: #cbd5e1; /* High contrast Slate 300 on dark sidebar */
    border: none;
    border-radius: 8px;
    text-align: left;
    padding-left: 20px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#navButton:hover {
    background-color: #1e293b; /* Slate 800 hover */
    color: #ffffff;
}
QPushButton#navButton[active="true"] {
    background-color: #0284c7; /* Vibrant Sky Blue Active */
    color: #ffffff;
    padding-left: 20px;
    font-weight: 700;
}
"""

def apply_shadow(widget, blur=24, dx=0, dy=4, alpha=15):
    """
    Applies a clean, modern soft drop shadow effect to any QWidget.
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)
