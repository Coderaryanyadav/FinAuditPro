"""
FinAuditPro Enterprise — Global Design System & Component Stylesheet
Apple-grade macOS light-mode desktop UI tokens.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


GLOBAL_QSS = """
/* ── BASE RESET ─────────────────────────────────────────────────────────── */
* {
    font-family: 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    color: #1D1D1F;
    outline: none;
}
QWidget {
    background-color: transparent;
    color: #1D1D1F;
}
QLabel {
    background-color: transparent;
    border: none;
    color: #1D1D1F;
}
QFrame {
    background-color: transparent;
    border: none;
}

/* ── APP BACKGROUND ──────────────────────────────────────────────────────── */
QMainWindow, QDialog { background-color: #F5F5F7; }
#appBg, QWidget#dashboardMain, QFrame#dashboardMainBody, QScrollArea#dashboardMainScroll, QStackedWidget { background-color: #F5F5F7; }
QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport {
    background-color: #F5F5F7; border: none;
}

/* ── SCROLLBARS ──────────────────────────────────────────────────────────── */
QScrollBar:vertical   { border:none; background:transparent; width:6px; margin:0; }
QScrollBar:horizontal { border:none; background:transparent; height:6px; margin:0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #D2D2D7; border-radius: 3px; min-height:24px; min-width:24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #AEAEB2;
}

/* ── TOOLTIP ─────────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1D1D1F;
    color: #F5F5F7;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 500;
}

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
QFrame#dashboardSidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E5EA;
}
QLabel#sidebarLogoBadge {
    background-color: #007AFF;
    color: #FFFFFF;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 800;
}
QLabel#sidebarAppTitle {
    font-size: 16px; font-weight: 700;
    color: #1D1D1F; border: none; letter-spacing: -0.3px;
}
QLabel#sidebarSectionLabel {
    font-size: 10px; font-weight: 800;
    color: #86868B;
    padding-left: 10px; border: none;
    letter-spacing: 0.8px; text-transform: uppercase;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid #E5E5EA;
    background-color: transparent;
}
QLabel#userAvatar {
    background-color: #007AFF; color: #FFFFFF;
    border-radius: 14px; font-weight: 700; font-size: 12px; border: none;
}
QLabel#userName { font-size: 13px; font-weight: 700; color: #1D1D1F; border: none; }
QLabel#userRole { font-size: 11px; color: #86868B; border: none; }

/* Nav buttons */
QPushButton#navButton {
    background-color: transparent;
    color: #424245;
    border: none; border-radius: 8px;
    text-align: left; padding-left: 12px;
    font-size: 13px; font-weight: 500;
    height: 36px;
}
QPushButton#navButton:hover {
    background-color: #F2F2F7;
    color: #1D1D1F;
}
QPushButton#navButton:checked, QPushButton#navButton[active="true"] {
    background-color: rgba(0, 122, 255, 0.12);
    color: #007AFF;
    font-weight: 700;
    border-radius: 8px;
}

/* ── HEADER BAR ──────────────────────────────────────────────────────────── */
QFrame#dashboardHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E5EA;
}
QFrame#globalSearchFrame {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 0px 6px;
}
QLineEdit#globalSearchInput {
    border: none; background: transparent;
    font-size: 13px; color: #1D1D1F;
    padding: 4px 8px;
}
QLabel#globalShortcutBadge {
    border: 1px solid #D2D2D7;
    background-color: #FFFFFF;
    color: #6E6E73;
    font-size: 10px; font-weight: 700;
    border-radius: 4px; padding: 2px 6px;
}

/* Active Audit Dropdown Combo Box */
QComboBox#clientSelectorCombo {
    border: 1px solid #D2D2D7;
    border-radius: 8px;
    padding: 5px 12px;
    background-color: #FFFFFF;
    color: #1D1D1F;
    font-size: 12px;
    font-weight: 600;
}
QComboBox#clientSelectorCombo:hover {
    border-color: #007AFF;
}
QComboBox#clientSelectorCombo::drop-down {
    border: none;
    width: 24px;
}
QComboBox#clientSelectorCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    color: #1D1D1F;
    selection-background-color: #007AFF;
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
QPushButton {
    font-size: 13px; padding: 7px 14px;
    border-radius: 8px; font-weight: 500;
    border: 1px solid transparent;
    color: #1D1D1F;
    background-color: #F2F2F7;
}
QPushButton:hover  { background-color: #E5E5EA; }
QPushButton:pressed { background-color: #D2D2D7; }

QPushButton#primaryBtn, QPushButton#primaryButton {
    background-color: #007AFF; color: #FFFFFF;
    font-size: 12px; font-weight: 700; border-radius: 8px;
    padding: 7px 16px; border: none;
}
QPushButton#primaryBtn:hover, QPushButton#primaryButton:hover {
    background-color: #0062CC;
}

/* ── CONTENT CARDS ───────────────────────────────────────────────────────── */
QFrame#contentCard, QFrame#cardFrame, QFrame#metricCard,
QFrame#recentProjectsTableFrame, QFrame#auditProgressCard, QFrame#riskMatrixWidget,
QFrame#needsAttentionPanel, QFrame#auditWorkspacePanel {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 12px;
}

QLabel#metricTitle {
    color: #6E6E73; font-size: 11px; font-weight: 800;
    border: none; background: transparent; letter-spacing: 0.6px;
}
QLabel#metricValue {
    color: #1D1D1F; font-size: 30px; font-weight: 800;
    border: none; background: transparent; letter-spacing: -0.8px;
}

/* ── TABLE WIDGET ────────────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    border: none;
    gridline-color: #F2F2F7;
    font-size: 13px;
}
QTableWidget::item, QTableView::item {
    padding: 10px 14px;
    border-bottom: 1px solid #F2F2F7;
    color: #1D1D1F;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(0, 122, 255, 0.08);
    color: #007AFF;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #64748B;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 10px 14px;
}
"""


def apply_card_shadow(widget: QWidget) -> None:
    """Apply subtle ambient card drop shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(16)
    shadow.setColor(QColor(0, 0, 0, 12))
    shadow.setOffset(0, 3)
    widget.setGraphicsEffect(shadow)
