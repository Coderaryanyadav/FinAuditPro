from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

GLOBAL_QSS = """
* {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #1e293b; /* slate-800 */
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
    background: #cbd5e1; /* slate-300 */
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8; /* slate-400 */
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
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

/* Line Edits */
QLineEdit {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    background-color: #ffffff;
    font-size: 13px;
    color: #0f172a;
}
QLineEdit:focus {
    border: 2px solid #0ea5e9; /* FinAuditPro Blue */
}

/* ComboBoxes */
QComboBox {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    background-color: #ffffff;
    color: #0f172a;
    font-size: 13px;
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
    border-radius: 8px;
    border: none;
    font-size: 13px;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    padding: 10px;
    font-weight: bold;
    font-size: 11px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}
QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
}
QTableWidget::item:selected {
    background-color: #f0f9ff;
    color: #0369a1;
}

/* Buttons */
QPushButton {
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
}
QPushButton#navButton {
    background-color: transparent;
    color: #64748b;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding-left: 20px;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background-color: #f8fafc;
    color: #0f172a;
}
QPushButton#navButton[active="true"] {
    background-color: #f0f9ff;
    color: #0369a1;
    border-left: 4px solid #0ea5e9;
    padding-left: 16px;
    font-weight: 600;
}
"""

def apply_shadow(widget, blur=16, dx=0, dy=4, alpha=15):
    """
    Applies a clean, modern, hardware-accelerated soft drop shadow to any widget.
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)
