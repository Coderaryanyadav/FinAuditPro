"""
FinAuditPro Enterprise — Global Design System & Component Stylesheet
Apple-grade macOS & Linear enterprise desktop UI design system.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


GLOBAL_QSS = """
/* ── BASE RESET ─────────────────────────────────────────────────────────── */
* {
    font-family: 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
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
QMainWindow, QDialog { background-color: #F8FAFC; }
#appBg, QWidget#dashboardMain, QFrame#dashboardMainBody, QScrollArea#dashboardMainScroll, QStackedWidget { background-color: #F8FAFC; }
QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport {
    background-color: #F8FAFC; border: none;
}

/* ── SCROLLBARS ──────────────────────────────────────────────────────────── */
QScrollBar:vertical   { border:none; background:transparent; width:5px; margin:0; }
QScrollBar:horizontal { border:none; background:transparent; height:5px; margin:0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #CBD5E1; border-radius: 2px; min-height:20px; min-width:20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #94A3B8;
}

/* ── TOOLTIP ─────────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
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
    font-size: 13px;
    font-weight: 800;
}
QLabel#sidebarAppTitle {
    font-size: 15px; font-weight: 800;
    color: #0F172A; border: none; letter-spacing: -0.3px;
}
QLabel#sidebarSectionLabel {
    font-size: 10px; font-weight: 800;
    color: #94A3B8;
    padding-left: 10px; border: none;
    letter-spacing: 0.8px; text-transform: uppercase;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid #F1F5F9;
    background-color: transparent;
}
QLabel#userAvatar {
    background-color: #2563EB; color: #FFFFFF;
    border-radius: 13px; font-weight: 800; font-size: 11px; border: none;
}
QLabel#userName { font-size: 12px; font-weight: 700; color: #0F172A; border: none; }
QLabel#userRole { font-size: 11px; color: #64748B; border: none; }

/* Nav buttons with thin blue left indicator */
QPushButton#navButton {
    background-color: transparent;
    color: #475569;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding-left: 10px;
    font-size: 13px;
    font-weight: 500;
    height: 34px;
}
QPushButton#navButton:hover {
    background-color: #F1F5F9;
    color: #0F172A;
}
QPushButton#navButton:checked, QPushButton#navButton[active="true"] {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 700;
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
    border-radius: 8px;
    padding: 0px 6px;
}
QLineEdit#globalSearchInput {
    border: none; background: transparent;
    font-size: 13px; color: #0F172A;
    padding: 4px 8px;
}
QLabel#globalShortcutBadge {
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    color: #64748B;
    font-size: 10px; font-weight: 700;
    border-radius: 4px; padding: 2px 6px;
}

/* Active Engagement Context Selector Dropdown */
QComboBox#clientSelectorCombo {
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 5px 12px;
    background-color: #FFFFFF;
    color: #0F172A;
    font-size: 12px;
    font-weight: 700;
}
QComboBox#clientSelectorCombo:hover {
    border-color: #2563EB;
    background-color: #F8FAFC;
}
QComboBox#clientSelectorCombo::drop-down {
    border: none;
    width: 22px;
}
QComboBox#clientSelectorCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    color: #0F172A;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
QPushButton {
    font-size: 12px; padding: 6px 14px;
    border-radius: 6px; font-weight: 600;
    border: 1px solid transparent;
    color: #0F172A;
    background-color: #F1F5F9;
}
QPushButton:hover  { background-color: #E2E8F0; }
QPushButton:pressed { background-color: #CBD5E1; }

QPushButton#primaryBtn, QPushButton#primaryButton {
    background-color: #2563EB; color: #FFFFFF;
    font-size: 12px; font-weight: 700; border-radius: 6px;
    padding: 7px 16px; border: none;
}
QPushButton#primaryBtn:hover, QPushButton#primaryButton:hover {
    background-color: #1D4ED8;
}

/* ── CONTENT CARDS ───────────────────────────────────────────────────────── */
QFrame#contentCard, QFrame#cardFrame, QFrame#metricCard,
QFrame#recentProjectsTableFrame, QFrame#auditProgressCard, QFrame#riskMatrixWidget,
QFrame#needsAttentionPanel, QFrame#auditWorkspacePanel {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QLabel#metricTitle {
    color: #64748B; font-size: 10px; font-weight: 800;
    border: none; background: transparent; letter-spacing: 0.6px;
}
QLabel#metricValue {
    color: #0F172A; font-size: 28px; font-weight: 800;
    border: none; background: transparent; letter-spacing: -0.6px;
}

/* ── TABLE WIDGET ────────────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    border: none;
    gridline-color: #F1F5F9;
    font-size: 13px;
}
QTableWidget::item, QTableView::item {
    padding: 8px 12px;
    border-bottom: 1px solid #F1F5F9;
    color: #0F172A;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 12px;
}
"""


def apply_card_shadow(widget: QWidget) -> None:
    """Apply subtle ambient card drop shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(12)
    shadow.setColor(QColor(0, 0, 0, 8))
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)
