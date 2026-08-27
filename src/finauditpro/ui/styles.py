"""
FinAuditPro Enterprise — Global Design System & Component Stylesheet
Apple-grade macOS & Linear enterprise desktop UI design system.
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

GLOBAL_QSS = """
/* ── BASE RESET ─────────────────────────────────────────────────────────── */
* {
    font-family: .AppleSystemUIFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    font-size: 14px;
    font-weight: 400;
    color: #0F172A;
    outline: none;
}
QWidget {
    background-color: transparent;
    color: #0F172A;
}
QLabel {
    background-color: transparent;
    border: none;
    color: #0F172A;
}
QFrame {
    background-color: transparent;
    border: none;
}

/* ── APP BACKGROUND ──────────────────────────────────────────────────────── */
QMainWindow { background-color: #F8FAFC; }
QDialog { background-color: #FFFFFF; }
#appBg, QWidget#dashboardMain, QFrame#dashboardMainBody, QScrollArea#dashboardMainScroll, QStackedWidget { background-color: #F8FAFC; }

/* ── FORM INPUTS & CONTROLS ──────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QDateEdit, QDateTimeEdit {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 7px;
    padding: 8px 12px;
    font-size: 14px;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QDateEdit:hover, QDateTimeEdit:hover {
    border-color: #CBD5E1;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus, QDateTimeEdit:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QDateEdit:disabled, QDateTimeEdit:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
    border-color: #F1F5F9;
}

QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport {
    background-color: #F8FAFC; border: none;
}

/* ── CHECKBOX ────────────────────────────────────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #0F172A;
    font-size: 14px;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
}
QCheckBox::indicator:hover {
    border-color: #2563EB;
}
QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    image: url("data:image/svg+xml;utf8,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2024%2024'%20fill='none'%20stroke='white'%20stroke-width='3'%20stroke-linecap='round'%20stroke-linejoin='round'%3E%3Cpolyline%20points='20%206%209%2017%204%2012'%3E%3C/polyline%3E%3C/svg%3E");
}
QCheckBox::indicator:disabled {
    background-color: #F1F5F9;
    border-color: #E2E8F0;
}

/* ── SCROLLBARS ──────────────────────────────────────────────────────────── */
QScrollBar:vertical   { border:none; background:transparent; width:6px; margin:0; }
QScrollBar:horizontal { border:none; background:transparent; height:6px; margin:0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #CBD5E1; border-radius: 3px; min-height:24px; min-width:24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0px; width: 0px; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ── TOOLTIP ─────────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 500;
}

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
QFrame#dashboardSidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}
QLabel#sidebarLogoBadge {
    background-color: #2563EB;
    color: #FFFFFF;
    border-radius: 7px;
    font-size: 14px;
    font-weight: 800;
}
QLabel#sidebarAppTitle {
    font-size: 17px; font-weight: 700;
    color: #0F172A; border: none;
}
QLabel#sidebarSectionLabel {
    font-size: 11px; font-weight: 700;
    color: #94A3B8;
    padding: 14px 12px 6px 12px; border: none;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid #F1F5F9;
    background-color: transparent;
    padding: 4px;
}
QLabel#userAvatar {
    background-color: #2563EB; color: #FFFFFF;
    border-radius: 15px; font-weight: 800; font-size: 12px; border: none;
}
QLabel#userName { font-size: 14px; font-weight: 600; color: #0F172A; border: none; }
QLabel#userRole { font-size: 12px; color: #64748B; border: none; }

/* Nav buttons with thin blue left indicator */
QPushButton#navButton {
    background-color: transparent;
    color: #475569;
    border: 1px solid transparent;
    border-radius: 6px;
    text-align: left;
    padding: 0px 12px;
    font-size: 14px;
    font-weight: 500;
    min-height: 36px;
    max-height: 36px;
}
QPushButton#navButton:hover {
    background-color: #F1F5F9;
    color: #1E293B;
}
QPushButton#navButton:checked, QPushButton#navButton[active="true"] {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 600;
    border-left: 3px solid #2563EB;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
}

/* ── HEADER BAR ──────────────────────────────────────────────────────────── */
QFrame#dashboardHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
}
QFrame#globalSearchFrame {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 0px 8px;
}
QFrame#globalSearchFrame:hover {
    border-color: #CBD5E1;
}
QLineEdit#globalSearchInput {
    border: 1px solid transparent; background: transparent;
    font-size: 14px; color: #64748B;
    padding: 6px 8px;
}
QLabel#globalShortcutBadge {
    border: 1px solid #E2E8F0;
    background-color: #F8FAFC;
    color: #94A3B8;
    font-size: 10px; font-weight: 600;
    border-radius: 4px; padding: 2px 6px;
}

/* ── TABS ────────────────────────────────────────────────────────────────── */
QTabWidget::pane { border: 1px solid #E2E8F0; background-color: #FFFFFF; border-radius: 8px; top: -1px; }
QTabBar::tab {
    font-size: 13px; font-weight: 500; padding: 9px 20px;
    color: #475569; background-color: #F1F5F9;
    border: 1px solid #E2E8F0; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    margin-right: 4px; min-height: 20px;
}
QTabBar::tab:hover { background-color: #E2E8F0; color: #0F172A; }
QTabBar::tab:selected {
    color: #2563EB; background-color: #FFFFFF;
    border-color: #CBD5E1; border-bottom: 2px solid #FFFFFF; font-weight: 700;
}

QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    background-color: #FFFFFF;
    color: #0F172A;
    min-height: 24px;
}
QComboBox:focus { border-color: #2563EB; }

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left-width: 0px;
}

QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #64748B;
    margin-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
    outline: none;
    color: #0F172A;
}

QComboBox QAbstractItemView::item {
    border: 1px solid transparent;
    background-color: transparent;
    color: #0F172A;
    min-height: 28px;
    padding: 6px 12px;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #EFF6FF;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F8FAFC;
    color: #0F172A;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}


/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
QPushButton {
    font-size: 14px; padding: 7px 16px;
    border-radius: 6px; font-weight: 500;
    border: 1px solid #CBD5E1;
    color: #334155; background-color: #FFFFFF;
    min-height: 20px;
}
QPushButton:hover  { background-color: #F8FAFC; border-color: #94A3B8; }
QPushButton:pressed { background-color: #F1F5F9; }
QPushButton:disabled { color: #94A3B8; background-color: #F8FAFC; border-color: #F1F5F9; }

QPushButton#primaryBtn, QPushButton#primaryButton {
    background-color: #2563EB; color: #FFFFFF;
    font-size: 14px; font-weight: 600; border-radius: 6px;
    padding: 8px 18px; border: 1px solid #2563EB; min-height: 20px;
}
QPushButton#primaryBtn:hover, QPushButton#primaryButton:hover { background-color: #1D4ED8; }
QPushButton#primaryBtn:pressed, QPushButton#primaryButton:pressed { background-color: #1E40AF; }

/* ── CONTENT CARDS ───────────────────────────────────────────────────────── */
QFrame#contentCard, QFrame#cardFrame, QFrame#metricCard,
QFrame#recentProjectsTableFrame, QFrame#auditProgressCard, QFrame#riskMatrixWidget,
QFrame#needsAttentionPanel, QFrame#auditWorkspacePanel {
    background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;
}

QLabel#metricTitle { color: #64748B; font-size: 11px; font-weight: 600; border: 1px solid transparent; background: transparent; }
QLabel#metricValue { color: #0F172A; font-size: 24px; font-weight: 600; border: 1px solid transparent; background: transparent; }

/* ── TABLE WIDGET ────────────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #FFFFFF; border: none; gridline-color: #F1F5F9;
    font-size: 13px; alternate-background-color: #FAFBFC;
}
QTableWidget::item, QTableView::item { padding: 6px 12px; border-bottom: 1px solid #F1F5F9; color: #0F172A; }
QTableWidget::item:hover, QTableView::item:hover { background-color: #F8FAFC; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #EFF6FF; color: #1D4ED8; }
QHeaderView::section {
    background-color: #FAFBFC; color: #64748B;
    font-size: 11px; font-weight: 600;
    border: none; border-bottom: 1px solid #E2E8F0; padding: 6px 12px;
}
"""


def apply_card_shadow(widget: QWidget) -> None:
    """Apply subtle ambient card drop shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(12)
    shadow.setColor(QColor(0, 0, 0, 8))
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)

