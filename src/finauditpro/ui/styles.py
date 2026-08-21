"""
FinAuditPro Enterprise — Global Design System & Component Stylesheet
Premium enterprise light-mode & dark-mode desktop UI tokens.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


GLOBAL_QSS = """
/* ── BASE RESET ─────────────────────────────────────────────────────────── */
* {
    font-family: "-apple-system", "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
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
    background-color: #F5F5F7;
    border-right: 1px solid #E5E5EA;
}
QFrame#sidebarLogoContainer {
    background-color: transparent;
    border-bottom: 1px solid #E5E5EA;
}
QLabel#sidebarLogoBadge {
    background-color: #007AFF;
    color: #FFFFFF;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#sidebarAppTitle {
    font-size: 15px; font-weight: 700;
    color: #1D1D1F; border: none; letter-spacing: -0.2px;
}
QLabel#sidebarSectionLabel {
    font-size: 11px; font-weight: 600;
    color: #86868B;
    padding-left: 12px; border: none;
    letter-spacing: 0.5px; text-transform: uppercase;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid #E5E5EA;
    background-color: transparent;
}
QLabel#userAvatar {
    background-color: #007AFF; color: #FFFFFF;
    border-radius: 14px; font-weight: 700; font-size: 12px; border: none;
}
QLabel#userName { font-size: 13px; font-weight: 600; color: #1D1D1F; border: none; }
QLabel#userRole { font-size: 11px; color: #86868B; border: none; }

/* Nav buttons */
QPushButton#navButton {
    background-color: transparent;
    color: #6E6E73;
    border: none; border-radius: 8px;
    text-align: left; padding-left: 12px;
    font-size: 13px; font-weight: 500;
    height: 34px;
}
QPushButton#navButton:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: #1D1D1F;
}
QPushButton#navButton[active="true"] {
    background-color: rgba(0, 122, 255, 0.12);
    color: #007AFF;
    font-weight: 600;
    border-radius: 8px;
    padding-left: 12px;
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
}
QLineEdit#globalSearchInput {
    border: none; background: transparent;
    font-size: 13px; color: #1D1D1F;
}
QLabel#globalShortcutBadge {
    border: 1px solid #E5E5EA;
    background-color: #FFFFFF;
    color: #6E6E73;
    font-size: 11px; font-weight: 600;
    border-radius: 4px; padding: 2px 6px;
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
    font-weight: 600; border: none;
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
    border-radius: 10px;
}

QLabel#metricTitle {
    color: #6E6E73; font-size: 11px; font-weight: 700;
    border: none; background: transparent; letter-spacing: 0.5px;
}
QLabel#metricValue {
    color: #1D1D1F; font-size: 32px; font-weight: 700;
    border: none; background: transparent; letter-spacing: -0.8px;
}
"""


def apply_card_shadow(widget: QWidget) -> None:
    """Apply subtle ambient card drop shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(16)
    shadow.setColor(QColor(0, 0, 0, 10))
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)
