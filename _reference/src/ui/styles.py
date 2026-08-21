"""
FinAuditPro V2 — Global Design System Stylesheet
Premium light-mode-first enterprise desktop UI.
Clean surfaces, precise typography, purposeful depth.
"""
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QProgressBar, QPushButton, QApplication
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from .theme import Colors, LightColors, DarkColors, ThemeManager

# ─────────────────────────────────────────────────────────────────────────────
# LIGHT MODE QSS
# ─────────────────────────────────────────────────────────────────────────────
GLOBAL_QSS = """
/* ── BASE RESET ─────────────────────────────────────────────────────────── */
* {
    font-family: "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    color: #1D1D1F;
    outline: none;
}
QWidget {
    background-color: transparent;
    background: transparent;
    color: #1D1D1F;
}
QLabel {
    background-color: transparent;
    background: transparent;
    border: none;
    color: #1D1D1F;
}
QFrame {
    background-color: transparent;
    background: transparent;
    border: none;
}

/* ── APP BACKGROUND ──────────────────────────────────────────────────────── */
QMainWindow, QDialog { background-color: #F5F5F7; }
#appBg, QWidget#dashboardMain, QFrame#dashboardMainBody, QScrollArea#dashboardMainScroll, QStackedWidget { background-color: #F5F5F7; }
QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport,
QScrollArea#dashboardMainScroll, QScrollArea#dashboardMainScroll > QWidget, QScrollArea#dashboardMainScroll #qt_scrollarea_viewport {
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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border:none; background:none; height:0; width:0;
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
QScrollArea#sidebarNavScroll { background: transparent; border: none; }
QWidget#sidebarNavWidget     { background: transparent; }

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

/* Sidebar collapse toggle */
QPushButton#sidebarCollapseBtn {
    background: transparent; border: none; border-radius: 6px;
    color: #86868B;
}
QPushButton#sidebarCollapseBtn:hover {
    background: rgba(0, 0, 0, 0.05); color: #1D1D1F;
}

/* ── HEADER BAR ──────────────────────────────────────────────────────────── */
QFrame#dashboardHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E5EA;
}

/* Global search */
QFrame#globalSearchFrame {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
}
QFrame#globalSearchFrame:hover { border-color: #007AFF; }
QLineEdit#globalSearchInput {
    border: none; background: transparent;
    font-size: 13px; color: #1D1D1F;
}
QLineEdit#globalSearchInput:read-only, QLineEdit#globalSearchInput:disabled {
    color: #1D1D1F; background: transparent;
}
QLabel#globalSearchIcon    { border: none; background: transparent; color: #6E6E73; font-size: 13px; }
QLabel#globalShortcutBadge {
    border: 1px solid #E5E5EA;
    background-color: #FFFFFF;
    color: #6E6E73;
    font-size: 11px; font-weight: 600;
    border-radius: 4px; padding: 2px 6px;
}

/* Active audit combo */
QComboBox#clientSelectorCombo {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px; font-weight: 500;
    color: #1D1D1F;
}
QComboBox#clientSelectorCombo:hover {
    border-color: #D2D2D7;
    background-color: #E5E5EA;
}
QComboBox#clientSelectorCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    selection-background-color: rgba(0, 122, 255, 0.1);
    selection-color: #007AFF;
    color: #1D1D1F;
}
QFrame#activeAuditBadge {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
}
QLabel#activeAuditLabel { font-size: 11px; font-weight: 600; color: #86868B; border: none; }
QLabel#activeAuditValue { font-size: 13px; font-weight: 500; color: #1D1D1F; border: none; }

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
QPushButton:disabled { background-color: #F2F2F7; color: #C7C7CC; }

QPushButton#primaryBtn, QPushButton#primaryButton {
    background-color: #007AFF; color: #FFFFFF;
    font-weight: 600; border: none;
}
QPushButton#primaryBtn:hover, QPushButton#primaryButton:hover {
    background-color: #0062CC;
}
QPushButton#primaryBtn:pressed, QPushButton#primaryButton:pressed {
    background-color: #004999;
}
QPushButton#primaryBtn:disabled, QPushButton#primaryButton:disabled {
    background-color: rgba(0, 122, 255, 0.4); color: #FFFFFF;
}

QPushButton#secondaryBtn, QPushButton#secondaryButton {
    background-color: #F1F3F5; color: #374151;
    border: 1px solid #E5E7EB; font-weight: 500;
}
QPushButton#secondaryBtn:hover, QPushButton#secondaryButton:hover {
    background-color: #EEF0F3; border-color: #D1D5DB;
}

QPushButton#outlineButton {
    background-color: transparent; color: #374151;
    border: 1px solid #E5E7EB;
}
QPushButton#outlineButton:hover {
    background-color: #F7F8FA; border-color: #D1D5DB;
}

QPushButton#iconToolBtn {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    color: #1D1D1F;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#iconToolBtn:hover {
    background-color: #E5E5EA;
    border-color: #D1D1D6;
}

QPushButton#dangerBtn {
    background-color: #FEF2F2; color: #DC2626;
    border: 1px solid #FECACA; font-weight: 600;
}
QPushButton#dangerBtn:hover { background-color: #FEE2E2; }

QPushButton#saveBtn {
    background-color: #059669; color: #FFFFFF;
    font-weight: 600; border: none;
}
QPushButton#saveBtn:hover   { background-color: #047857; }
QPushButton#saveBtn:pressed { background-color: #065F46; }

QPushButton#ghostBtn {
    background-color: transparent; color: #6B7280;
    border: none; padding: 5px 10px;
}
QPushButton#ghostBtn:hover { background-color: #F1F3F5; color: #374151; }

QPushButton#iconToolBtn {
    background-color: transparent; color: #6B7280;
    border: none; border-radius: 6px; font-size: 14px;
}
QPushButton#iconToolBtn:hover { background-color: #F1F3F5; color: #374151; }

/* Login submit */
QPushButton#loginSubmitBtn {
    background-color: #2563EB; color: #FFFFFF;
    font-size: 13px; font-weight: 600;
    border-radius: 6px; border: none;
}
QPushButton#loginSubmitBtn:hover   { background-color: #1D4ED8; }
QPushButton#loginSubmitBtn:pressed { background-color: #1E40AF; }
QPushButton#loginSubmitBtn:disabled { background-color: #BFDBFE; color: #FFFFFF; }

/* ── INPUTS ──────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit {
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 7px 11px;
    background-color: #FFFFFF;
    font-size: 13px; color: #111827;
    selection-background-color: rgba(37,99,235,0.15);
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #2563EB;
    background-color: #FFFFFF;
}
QLineEdit:hover, QTextEdit:hover { border-color: #9CA3AF; }
QLineEdit::placeholder { color: #D1D5DB; }
QLineEdit:disabled, QTextEdit:disabled {
    background-color: #F7F8FA; color: #9CA3AF;
}
QLineEdit#searchField {
    padding: 6px 11px; border: 1px solid #E5E7EB;
    background-color: #F7F8FA; font-size: 12px;
}
QLineEdit#searchField:focus { background-color: #FFFFFF; border-color: #2563EB; }

/* ── COMBOBOX ────────────────────────────────────────────────────────────── */
QComboBox {
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 7px 11px; background-color: #FFFFFF;
    color: #111827; font-size: 13px; font-weight: 400;
}
QComboBox:hover { border-color: #9CA3AF; }
QComboBox:focus { border-color: #2563EB; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 6px; color: #111827;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none; padding: 3px;
}

/* ── TABLES ──────────────────────────────────────────────────────────────── */
QTableWidget, QTableView,
QTableView::viewport, QTableWidget::viewport {
    background-color: #FFFFFF;
    gridline-color: #F1F3F5;
    border: none; font-size: 13px;
    outline: none; color: #374151;
}
QHeaderView, QHeaderView::section {
    background-color: #F7F8FA;
    color: #6B7280;
    padding: 9px 14px;
    font-weight: 600; font-size: 11px;
    letter-spacing: 0.4px;
    border: none; border-bottom: 1px solid #E5E7EB;
}
QTableWidget::item, QTableView::item {
    padding: 9px 14px;
    border-bottom: 1px solid #F1F3F5;
    color: #374151;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #EFF6FF; color: #111827;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: #F7F8FA;
}

/* ── TABS ────────────────────────────────────────────────────────────────── */
QTabWidget::pane { border: none; background: transparent; }
QTabBar {
    background: transparent; border: none;
    border-bottom: 1px solid #E5E7EB;
}
QTabBar::tab {
    background: transparent; color: #6B7280;
    padding: 8px 16px; font-weight: 500; font-size: 13px;
    border: none; border-bottom: 2px solid transparent;
    margin-right: 2px;
}
QTabBar::tab:selected { color: #2563EB; border-bottom: 2px solid #2563EB; font-weight: 600; }
QTabBar::tab:hover:!selected { color: #374151; }

/* ── PROGRESS BAR ────────────────────────────────────────────────────────── */
QProgressBar {
    border: none; background-color: #E5E7EB;
    border-radius: 3px; color: transparent;
}
QProgressBar::chunk { background-color: #2563EB; border-radius: 3px; }

/* ── CHECKBOXES ──────────────────────────────────────────────────────────── */
QCheckBox { border: none; background: transparent; color: #374151; font-size: 12px; spacing: 8px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border-radius: 4px; border: 1.5px solid #D1D5DB; background: #FFFFFF;
}
QCheckBox::indicator:checked  { background: #2563EB; border-color: #2563EB; }
QCheckBox::indicator:hover     { border-color: #2563EB; }

/* ── SPLITTER ────────────────────────────────────────────────────────────── */
QSplitter::handle { background: #E5E7EB; width: 1px; height: 1px; }
QSplitter::handle:hover { background: #D1D5DB; }

/* ── DIALOGS ─────────────────────────────────────────────────────────────── */
QDialog {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
}
QMessageBox { background-color: #FFFFFF; }
QMessageBox QLabel { color: #111827; font-size: 13px; background: transparent; }
QMessageBox QPushButton {
    background-color: #F1F3F5; color: #374151;
    border: 1px solid #E5E7EB; border-radius: 6px;
    padding: 6px 16px; font-size: 12px; font-weight: 500;
}
QMessageBox QPushButton:hover    { background-color: #EEF0F3; }
QMessageBox QPushButton:default  { background-color: #2563EB; color: #FFFFFF; border: none; }
QMessageBox QPushButton:default:hover { background-color: #1D4ED8; }

/* ── CONTENT CARDS ───────────────────────────────────────────────────────── */
QFrame#contentCard, QFrame#cardFrame, QFrame#metricCard,
QFrame#recentProjectsTableFrame, QFrame#auditProgressCard, QFrame#riskMatrixWidget,
QFrame#needsAttentionPanel, QFrame#auditWorkspacePanel,
QFrame#riskDistributionCard, QFrame#aiSummaryCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 10px;
}
QFrame#contentHeader { background-color: #FFFFFF; border-bottom: 1px solid #E5E5EA; }
QFrame#leftContainer { background-color: #FFFFFF; border-right: 1px solid #E5E5EA; }
QFrame#summaryStrip  { background-color: #FFFFFF; border-bottom: 1px solid #E5E5EA; }
QFrame#contentCard:hover { border-color: #D1D5DB; }

/* ── METRIC LABELS ───────────────────────────────────────────────────────── */
QLabel#metricTitle {
    color: #6E6E73; font-size: 11px; font-weight: 700;
    border: none; background: transparent; letter-spacing: 0.5px;
}
QLabel#metricValue {
    color: #1D1D1F; font-size: 32px; font-weight: 700;
    border: none; background: transparent; letter-spacing: -0.8px;
}
QLabel#heroTitle {
    font-size: 28px; font-weight: 700; color: #1D1D1F;
    border: none; letter-spacing: -0.6px; background: transparent;
}
QLabel#heroSub { font-size: 13px; color: #6E6E73; border: none; background: transparent; }
QLabel#headerTitle {
    font-size: 17px; font-weight: 700; color: #111827;
    letter-spacing: -0.2px; background: transparent;
}
QLabel#headerSubtitle { font-size: 12px; color: #6B7280; font-weight: 400; background: transparent; }

QListWidget#clientListWidget {
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    background-color: #FFFFFF;
    color: #1D1D1F;
    outline: none;
}
QListWidget#clientListWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #F2F2F7;
    border-radius: 6px;
    margin: 2px 4px;
}
QListWidget#clientListWidget::item:hover {
    background-color: #F2F2F7;
}
QListWidget#clientListWidget::item:selected {
    background-color: rgba(0, 122, 255, 0.15);
    color: #007AFF;
    font-weight: 600;
}

/* ── STATUS BADGES ───────────────────────────────────────────────────────── */
QLabel#statusBadgeBlue {
    background-color: #EFF6FF; color: #2563EB;
    border-radius: 4px; font-size: 10px; font-weight: 600;
    padding: 2px 7px; border: 1px solid #BFDBFE;
}
QLabel#statusBadgeGreen {
    background-color: #ECFDF5; color: #059669;
    border-radius: 4px; font-size: 10px; font-weight: 600;
    padding: 2px 7px; border: 1px solid #A7F3D0;
}
QLabel#statusBadgeAmber {
    background-color: #FFFBEB; color: #D97706;
    border-radius: 4px; font-size: 10px; font-weight: 600;
    padding: 2px 7px; border: 1px solid #FDE68A;
}
QLabel#statusBadgeRed   {
    background-color: #FEF2F2; color: #DC2626;
    border-radius: 4px; font-size: 10px; font-weight: 600;
    padding: 2px 7px; border: 1px solid #FECACA;
}

QFrame#attentionRow {
    background-color: #F2F2F7;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
}
QFrame#attentionRow:hover {
    border-color: #007AFF;
    background-color: #FFFFFF;
}
QFrame#attentionRow QLabel#attentionLabel {
    font-size: 12px; font-weight: 500; color: #1D1D1F; border: none; background: transparent;
}

/* ── SECTION HEADERS ─────────────────────────────────────────────────────── */
QFrame#actionHeader, QFrame#clientsHeader, QFrame#docsHeader,
QFrame#headerBar, QFrame#historyHeader, QFrame#reportsHeader,
QFrame#settingsHeader, QFrame#aiHeader {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
}

/* ── SETTINGS ────────────────────────────────────────────────────────────── */
QFrame#settingsSection, QFrame#clientFormCard, QFrame#wpSignoffBox {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
}
QLabel#settingsSectionTitle {
    font-size: 13px; font-weight: 600; color: #111827;
    border: none; background: transparent;
}

/* ── CLIENTS PANE ────────────────────────────────────────────────────────── */
QFrame#clientsLeftPane {
    background-color: #F7F8FA;
    border-right: 1px solid #E5E7EB;
}

/* ── COMPLIANCE TABLES ───────────────────────────────────────────────────── */
QFrame#complianceTaskRow {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
}
QFrame#complianceTaskRow:hover { border-color: #2563EB; background: #F7F8FA; }
QTableWidget#complianceTable {
    border: 1px solid #E5E7EB; gridline-color: #F1F3F5;
    background: #FFFFFF; border-radius: 6px; color: #374151;
}

/* ── AI COMPONENTS ───────────────────────────────────────────────────────── */
QFrame#aiColHeader { background-color: #F7F8FA; border-bottom: 1px solid #E5E7EB; }
QLabel#aiColTitle {
    font-size: 10px; font-weight: 700; color: #6B7280;
    letter-spacing: 0.6px; border: none; background: transparent;
}
QTextEdit#aiDocContent {
    background-color: #F7F8FA; padding: 14px;
    border: 1px solid #E5E7EB; border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #111827;
}
QFrame#chatBubbleUser {
    background-color: #2563EB; border: none; border-radius: 10px; margin-left: 48px;
}
QFrame#chatBubbleAI {
    background-color: #F7F8FA; border: 1px solid #E5E7EB;
    border-radius: 10px; margin-right: 48px;
}
QLabel#chatMsgUser  { font-size: 12px; border: none; color: #FFFFFF; background: transparent; }
QLabel#chatMsgAI    { font-size: 12px; border: none; color: #111827; background: transparent; }
QLabel#chatSenderUser { font-size: 10px; font-weight: 700; border: none; color: rgba(255,255,255,0.8); background: transparent; }
QLabel#chatSenderAI   { font-size: 10px; font-weight: 700; border: none; color: #6B7280; background: transparent; }
QTextEdit#chatInput {
    border: 1px solid #E5E7EB; border-radius: 6px;
    padding: 8px 12px; font-size: 12px;
    background-color: #FFFFFF; color: #111827;
}
QTextEdit#chatInput:focus { border-color: #2563EB; }
QPushButton#chatSendBtn {
    background-color: #2563EB; color: #FFFFFF; font-weight: 600;
    font-size: 12px; border-radius: 6px; border: none; padding: 8px 16px;
}
QPushButton#chatSendBtn:hover { background-color: #1D4ED8; }
QPushButton#aiPromptBtn {
    background-color: #F7F8FA; color: #374151; font-weight: 500;
    font-size: 12px; border: 1px solid #E5E7EB; border-radius: 6px;
    padding: 7px 12px; text-align: left;
}
QPushButton#aiPromptBtn:hover {
    background-color: #EFF6FF; border-color: #BFDBFE; color: #2563EB;
}
QFrame#findingCard {
    background-color: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 8px; margin-bottom: 8px;
}
QLabel#findingCardTitle { font-weight: 700; font-size: 13px; color: #111827; border: none; background: transparent; }
QLabel#findingCardDesc  { color: #374151; font-size: 12px; border: none; background: transparent; }
QFrame#evidenceBox { background-color: #F7F8FA; border: 1px solid #E5E7EB; border-radius: 6px; }
QLabel#evidenceData { color: #2563EB; font-size: 11px; font-weight: 600; font-family: monospace; border: none; background: transparent; }
QPushButton#btnIngestWP {
    background-color: #2563EB; color: #FFFFFF; border: none;
    font-size: 11px; font-weight: 600; border-radius: 5px; padding: 5px 12px;
}
QPushButton#btnIngestWP:hover { background-color: #1D4ED8; }

/* ── DOC DROP ZONE ───────────────────────────────────────────────────────── */
QFrame#docsDropZone {
    background-color: #F7F8FA;
    border: 1.5px dashed #D1D5DB;
    border-radius: 8px;
}
QFrame#docsDropZone:hover {
    background-color: #EFF6FF;
    border-color: #2563EB;
}

/* ── LOGIN ───────────────────────────────────────────────────────────────── */
QFrame#loginHeroPanel {
    background-color: #1C1E21;
    border-right: 1px solid #2A2D32;
}
QWidget#loginRightBg  { background-color: #F7F8FA; }
QFrame#loginFormContainer {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}

/* ── PROMPT CHIPS ────────────────────────────────────────────────────────── */
QPushButton#promptChipBtn {
    background-color: #FFFFFF; color: #374151;
    border: 1px solid #E5E7EB; border-radius: 20px;
    padding: 5px 12px; font-size: 11px; font-weight: 500;
}
QPushButton#promptChipBtn:hover {
    background-color: #EFF6FF; border-color: #BFDBFE; color: #2563EB;
}

/* ── MISC ────────────────────────────────────────────────────────────────── */
QChartView { background-color: transparent; border: none; }
QFrame#ollamaOnboardingPanel {
    background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px;
}
QComboBox#clientSelectorCombo {
    padding: 5px 10px; border: 1px solid #E5E7EB;
    border-radius: 6px; background-color: #F7F8FA;
    color: #111827; font-size: 12px; font-weight: 500;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# DARK MODE QSS — layered surfaces, no pure black, premium feel
# ─────────────────────────────────────────────────────────────────────────────
DARK_QSS = """
* { font-family: "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif; color: #F5F5F7; outline: none; }
QWidget { background-color: transparent; background: transparent; color: #F5F5F7; }
QLabel  { background-color: transparent; background: transparent; border: none; color: #F5F5F7; }
QFrame  { background-color: transparent; background: transparent; border: none; }

QMainWindow, QDialog { background-color: #18181A; }
#appBg, QWidget#dashboardMain, QFrame#dashboardMainBody, QScrollArea#dashboardMainScroll, QStackedWidget { background-color: #18181A; }
QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport,
QScrollArea#dashboardMainScroll, QScrollArea#dashboardMainScroll > QWidget, QScrollArea#dashboardMainScroll #qt_scrollarea_viewport {
    background-color: #18181A; border: none;
}

QScrollBar:vertical   { border:none; background:transparent; width:6px; margin:0; }
QScrollBar:horizontal { border:none; background:transparent; height:6px; margin:0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3A3A3C; border-radius: 3px; min-height:24px; min-width:24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #636366; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border:none; background:none; }

QToolTip {
    background-color: #2C2C2E; color: #F5F5F7;
    border: 1px solid #3A3A3C; border-radius: 6px;
    padding: 5px 9px; font-size: 11px;
}

QFrame#dashboardSidebar { background-color: #1E1E1E; border-right: 1px solid #2C2C2E; }
QLabel#sidebarAppTitle  { font-size: 15px; font-weight: 700; color: #FFFFFF; border: none; }
QLabel#userAvatar { background-color: #0A84FF; color: #FFFFFF; border-radius: 14px; font-weight: 700; border: none; }
QLabel#userName { color: #FFFFFF; font-size: 13px; font-weight: 600; border: none; }
QLabel#userRole { color: #8E8E93; font-size: 11px; border: none; }

QPushButton#navButton { background-color: transparent; color: #8E8E93; border: none; border-radius: 8px; text-align: left; padding-left: 12px; font-size: 13px; font-weight: 500; height: 34px; }
QPushButton#navButton:hover { background-color: rgba(255,255,255,0.05); color: #FFFFFF; }
QPushButton#navButton[active="true"] {
    background-color: rgba(10, 132, 255, 0.18); color: #0A84FF; font-weight: 600;
    border-radius: 8px; padding-left: 12px;
}

QFrame#dashboardHeader { background-color: #2C2C2E; border-bottom: 1px solid #3A3A3C; }
QFrame#globalSearchFrame { background-color: #1E1E1E; border: 1px solid #3A3A3C; border-radius: 8px; }
QFrame#globalSearchFrame:hover { border-color: #0A84FF; }
QLineEdit#globalSearchInput { border: none; background: transparent; font-size: 13px; color: #FFFFFF; }
QLineEdit#globalSearchInput:read-only, QLineEdit#globalSearchInput:disabled { color: #FFFFFF; background: transparent; }
QLabel#globalSearchIcon { border: none; background: transparent; color: #8E8E93; font-size: 13px; }
QLabel#globalShortcutBadge { border: 1px solid #3A3A3C; background-color: #2C2C2E; color: #8E8E93; font-size: 11px; font-weight: 600; border-radius: 4px; padding: 2px 6px; }

QComboBox#clientSelectorCombo {
    background-color: #1E1E1E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px; font-weight: 500;
    color: #FFFFFF;
}
QComboBox#clientSelectorCombo:hover { border-color: #48484A; background-color: #2C2C2E; }
QComboBox#clientSelectorCombo QAbstractItemView {
    background-color: #2C2C2E;
    border: 1px solid #3A3A3C;
    selection-background-color: rgba(10, 132, 255, 0.2);
    selection-color: #0A84FF;
    color: #FFFFFF;
}

QPushButton#iconToolBtn {
    background-color: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 8px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#iconToolBtn:hover {
    background-color: #3A3A3C;
    border-color: #48484A;
}

QPushButton {
    font-size: 13px; padding: 7px 14px; border-radius: 8px; font-weight: 500;
    border: 1px solid #3A3A3C; color: #FFFFFF; background-color: #2C2C2E;
}
QPushButton:hover  { background-color: #3A3A3C; }
QPushButton:pressed { background-color: #1E1E1E; }
QPushButton:disabled { background-color: #2C2C2E; color: #636366; }
QPushButton#primaryBtn, QPushButton#primaryButton {
    background-color: #0A84FF; color: #FFFFFF; font-weight: 600; border: none;
}
QPushButton#primaryBtn:hover, QPushButton#primaryButton:hover { background-color: #0070E0; }
QPushButton#saveBtn { background-color: #30D158; color: #FFFFFF; font-weight: 600; border: none; }
QPushButton#saveBtn:hover { background-color: #24B346; }
QPushButton#dangerBtn { background-color: rgba(255,69,58,0.15); color: #FF453A; border: 1px solid rgba(255,69,58,0.3); font-weight: 600; }
QPushButton#dangerBtn:hover { background-color: rgba(255,69,58,0.25); }

QLineEdit, QTextEdit {
    border: 1px solid #3A3A3C; border-radius: 8px; padding: 7px 11px;
    background-color: #2C2C2E; font-size: 13px; color: #FFFFFF;
    selection-background-color: rgba(10,132,255,0.3);
}
QLineEdit:focus, QTextEdit:focus { border-color: #0A84FF; background-color: #2C2C2E; }
QLineEdit:hover, QTextEdit:hover { border-color: #636366; }

QComboBox {
    border: 1px solid #3A3A3C; border-radius: 8px; padding: 7px 11px;
    background-color: #2C2C2E; color: #FFFFFF; font-size: 13px;
}
QComboBox:hover { border-color: #636366; }
QComboBox:focus { border-color: #0A84FF; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #2C2C2E; border: 1px solid #3A3A3C; border-radius: 8px;
    color: #FFFFFF; selection-background-color: #0A84FF; selection-color: #FFFFFF; outline: none; padding: 3px;
}

QTableWidget, QTableView, QTableView::viewport, QTableWidget::viewport {
    background-color: #2C2C2E; gridline-color: #3A3A3C; border: none; font-size: 13px; outline: none; color: #FFFFFF;
}
QHeaderView, QHeaderView::section {
    background-color: #1E1E1E; color: #8E8E93; padding: 9px 14px;
    font-weight: 600; font-size: 11px; border: none; border-bottom: 1px solid #3A3A3C;
}
QTableWidget::item, QTableView::item { padding: 9px 14px; border-bottom: 1px solid #3A3A3C; color: #FFFFFF; }
QTableWidget::item:selected, QTableView::item:selected { background-color: rgba(10,132,255,0.2); color: #FFFFFF; }
QTableWidget::item:hover, QTableView::item:hover { background-color: #3A3A3C; }

QTabWidget::pane { border: none; background: transparent; }
QTabBar { background: transparent; border: none; border-bottom: 1px solid #3A3A3C; }
QTabBar::tab { background: transparent; color: #8E8E93; padding: 8px 16px; font-weight: 500; font-size: 13px; border: none; border-bottom: 2px solid transparent; margin-right: 2px; }
QTabBar::tab:selected { color: #0A84FF; border-bottom: 2px solid #0A84FF; font-weight: 600; }
QTabBar::tab:hover:!selected { color: #FFFFFF; }

QProgressBar { border: none; background-color: #3A3A3C; border-radius: 3px; color: transparent; }
QProgressBar::chunk { background-color: #0A84FF; border-radius: 3px; }
QCheckBox { border: none; background: transparent; color: #FFFFFF; font-size: 12px; spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px; border: 1.5px solid #3A3A3C; background: #2C2C2E; }
QCheckBox::indicator:checked { background: #0A84FF; border-color: #0A84FF; }
QCheckBox::indicator:hover { border-color: #0A84FF; }

QSplitter::handle { background: #3A3A3C; width: 1px; height: 1px; }
QDialog { background-color: #2C2C2E; border: 1px solid #3A3A3C; border-radius: 12px; }

QFrame#contentCard, QFrame#cardFrame, QFrame#metricCard, QFrame#recentProjectsTableFrame,
QFrame#auditProgressCard, QFrame#riskMatrixWidget, QFrame#needsAttentionPanel, QFrame#auditWorkspacePanel,
QFrame#riskDistributionCard, QFrame#aiSummaryCard {
    background-color: #222224; border: 1px solid #2E2E32; border-radius: 10px;
}
QFrame#contentHeader { background-color: #222224; border-bottom: 1px solid #2E2E32; }
QFrame#leftContainer { background-color: #222224; border-right: 1px solid #2E2E32; }
QFrame#summaryStrip  { background-color: #222224; border-bottom: 1px solid #2E2E32; }
QLabel#metricTitle { color: #8E8E93; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent; }
QLabel#metricValue { color: #F5F5F7; font-size: 32px; font-weight: 700; letter-spacing: -0.8px; border: none; background: transparent; }
QLabel#heroTitle   { color: #F5F5F7; font-size: 28px; font-weight: 700; letter-spacing: -0.6px; border: none; background: transparent; }
QLabel#heroSub     { color: #8E8E93; font-size: 13px; font-weight: 400; border: none; background: transparent; }
QLabel#headerTitle { font-size: 17px; font-weight: 700; color: #F9FAFB; background: transparent; }
QLabel#headerSubtitle { font-size: 12px; color: #9CA3AF; background: transparent; }

QListWidget#clientListWidget {
    border: 1px solid #2E2E32;
    border-radius: 8px;
    background-color: #222224;
    color: #F5F5F7;
    outline: none;
}
QListWidget#clientListWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #2E2E32;
    border-radius: 6px;
    margin: 2px 4px;
}
QListWidget#clientListWidget::item:hover {
    background-color: #2C2C2E;
}
QListWidget#clientListWidget::item:selected {
    background-color: rgba(10, 132, 255, 0.25);
    color: #0A84FF;
    font-weight: 600;
}

QLabel#statusBadgeBlue  { background-color: rgba(59,130,246,0.12); color: #60A5FA; border-radius: 4px; font-size: 10px; font-weight: 600; padding: 2px 7px; border: 1px solid rgba(59,130,246,0.3); }
QLabel#statusBadgeGreen { background-color: rgba(16,185,129,0.12); color: #34D399; border-radius: 4px; font-size: 10px; font-weight: 600; padding: 2px 7px; border: 1px solid rgba(16,185,129,0.3); }
QLabel#statusBadgeAmber { background-color: rgba(245,158,11,0.12); color: #FBBF24; border-radius: 4px; font-size: 10px; font-weight: 600; padding: 2px 7px; border: 1px solid rgba(245,158,11,0.3); }
QLabel#statusBadgeRed   { background-color: rgba(239,68,68,0.12); color: #F87171; border-radius: 4px; font-size: 10px; font-weight: 600; padding: 2px 7px; border: 1px solid rgba(239,68,68,0.3); }

QFrame#attentionRow {
    background-color: #2A2A2D;
    border: 1px solid #3A3A3E;
    border-radius: 8px;
}
QFrame#attentionRow:hover {
    border-color: #0A84FF;
    background-color: #323236;
}
QFrame#attentionRow QLabel#attentionLabel {
    font-size: 12px; font-weight: 500; color: #F5F5F7; border: none; background: transparent;
}

QFrame#actionHeader, QFrame#clientsHeader, QFrame#docsHeader, QFrame#headerBar,
QFrame#historyHeader, QFrame#reportsHeader, QFrame#settingsHeader, QFrame#aiHeader {
    background-color: #1C1E23; border-bottom: 1px solid #2E3138;
}
QFrame#settingsSection, QFrame#clientFormCard, QFrame#wpSignoffBox {
    background: #1C1E23; border: 1px solid #2E3138; border-radius: 8px;
}
QFrame#clientsLeftPane { background-color: #111318; border-right: 1px solid #2E3138; }
QFrame#docsDropZone { background-color: #1E2026; border: 1.5px dashed #3A3E47; border-radius: 8px; }
QFrame#docsDropZone:hover { background-color: rgba(59,130,246,0.08); border-color: #3B82F6; }
QFrame#findingCard { background-color: #1C1E23; border: 1px solid #2E3138; border-radius: 8px; margin-bottom: 8px; }
QLabel#findingCardTitle { font-weight: 700; font-size: 13px; color: #F9FAFB; border: none; background: transparent; }
QLabel#findingCardDesc  { color: #D1D5DB; font-size: 12px; border: none; background: transparent; }
QPushButton#aiPromptBtn {
    background-color: #1E2026; color: #D1D5DB; font-weight: 500; font-size: 12px;
    border: 1px solid #2E3138; border-radius: 6px; padding: 7px 12px; text-align: left;
}
QPushButton#aiPromptBtn:hover { background-color: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.3); color: #60A5FA; }
QTextEdit#chatInput { border: 1px solid #3A3E47; border-radius: 6px; padding: 8px 12px; font-size: 12px; background-color: #1E2026; color: #F9FAFB; }
QTextEdit#chatInput:focus { border-color: #3B82F6; }
QFrame#chatBubbleUser { background-color: #2563EB; border: none; border-radius: 10px; margin-left: 48px; }
QFrame#chatBubbleAI { background-color: #1E2026; border: 1px solid #2E3138; border-radius: 10px; margin-right: 48px; }
QLabel#chatMsgUser { font-size: 12px; border: none; color: #FFFFFF; background: transparent; }
QLabel#chatMsgAI   { font-size: 12px; border: none; color: #F9FAFB; background: transparent; }
QFrame#loginHeroPanel { background-color: #0E1013; border-right: 1px solid #1C1E21; }
QWidget#loginRightBg  { background-color: #111318; }
QFrame#loginFormContainer { background-color: #1C1E23; border-radius: 12px; border: 1px solid #2E3138; }
QPushButton#loginSubmitBtn { background-color: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 600; border-radius: 6px; border: none; }
QPushButton#loginSubmitBtn:hover { background-color: #1D4ED8; }
QPushButton#promptChipBtn { background-color: #1E2026; color: #D1D5DB; border: 1px solid #3A3E47; border-radius: 20px; padding: 5px 12px; font-size: 11px; }
QPushButton#promptChipBtn:hover { background-color: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.3); color: #60A5FA; }
"""


def get_qss(dark: bool = False) -> str:
    return DARK_QSS if dark else GLOBAL_QSS


def apply_shadow(widget, blur: int = 16, dx: int = 0, dy: int = 3, alpha: int = 20):
    """Subtle card shadow."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


# ─────────────────────────────────────────────────────────────────────────────
# REUSABLE STATE WIDGETS
# ─────────────────────────────────────────────────────────────────────────────

class EmptyStateWidget(QWidget):
    """Empty state — clean, minimal, actionable."""
    def __init__(self, title="Nothing here yet",
                 description="No records found.",
                 icon="○", action_text=None, action_callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px; border: none; background: transparent; background-color: transparent; color: #86868B;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #1D1D1F; border: none; background: transparent; background-color: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("font-size: 12px; color: #86868B; border: none; background: transparent; background-color: transparent;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumWidth(480)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)

        if action_text and action_callback:
            btn = QPushButton(action_text)
            btn.setObjectName("primaryBtn")
            btn.setFixedWidth(160)
            btn.clicked.connect(action_callback)
            btn.setStyleSheet("margin-top: 8px;")
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


class LoadingStateWidget(QWidget):
    """Loading indicator — clean indeterminate bar."""
    def __init__(self, message="Loading…"):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setFixedWidth(260)
        container.setStyleSheet("QFrame { background: transparent; border: none; }")
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setSpacing(12)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #6B7280; border: none;")
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pbar = QProgressBar()
        pbar.setRange(0, 0)
        pbar.setFixedHeight(3)

        cl.addWidget(msg_lbl)
        cl.addWidget(pbar)
        layout.addWidget(container)


class ErrorStateWidget(QWidget):
    """Error state — clean, readable, with optional retry."""
    def __init__(self, title="Something went wrong",
                 details="An unexpected error occurred. Please try again.",
                 retry_callback=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setMaximumWidth(440)
        container.setStyleSheet("""
            QFrame {
                background: #FEF2F2;
                border: 1px solid #FECACA;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        cl = QVBoxLayout(container)
        cl.setSpacing(6)

        self.title_lbl = QLabel(f"⚠  {title}")
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #DC2626; border: none;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.details_lbl = QLabel(str(details))
        self.details_lbl.setStyleSheet("font-size: 12px; color: #991B1B; border: none; margin-top: 4px;")
        self.details_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_lbl.setWordWrap(True)

        cl.addWidget(self.title_lbl)
        cl.addWidget(self.details_lbl)

        if retry_callback:
            retry_btn = QPushButton("Try Again")
            retry_btn.setStyleSheet("""
                QPushButton { background: #DC2626; color: #FFFFFF; border: none;
                    border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; margin-top: 8px; }
                QPushButton:hover { background: #B91C1C; }
            """)
            retry_btn.clicked.connect(retry_callback)
            cl.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(container)


# ─────────────────────────────────────────────────────────────────────────────
# TOAST NOTIFICATION SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class ToastNotification(QFrame):
    """Non-blocking, auto-dismissing toast notification."""
    TYPES = {
        "success": ("#ECFDF5", "#059669", "#A7F3D0", "✓"),
        "error":   ("#FEF2F2", "#DC2626", "#FECACA", "✕"),
        "warning": ("#FFFBEB", "#D97706", "#FDE68A", "⚠"),
        "info":    ("#EFF6FF", "#2563EB", "#BFDBFE", "ℹ"),
    }

    def __init__(self, message: str, kind: str = "info", parent=None, duration_ms: int = 4000):
        super().__init__(parent)
        bg, fg, border, icon = self.TYPES.get(kind, self.TYPES["info"])

        self.setFixedWidth(300)
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
        """)
        apply_shadow(self, blur=20, dy=6, alpha=25)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 14px; color: {fg}; border: none; background: transparent;")
        icon_lbl.setFixedWidth(18)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {fg}; border: none; background: transparent;")
        msg_lbl.setWordWrap(False)

        layout.addWidget(icon_lbl)
        layout.addWidget(msg_lbl, 1)

        QTimer.singleShot(duration_ms, self.deleteLater)


class ToastManager:
    """Show toast notifications anchored to a parent widget's bottom-right corner."""
    _active: list = []

    @classmethod
    def show(cls, parent: QWidget, message: str, kind: str = "info", duration_ms: int = 4000):
        toast = ToastNotification(message, kind, parent, duration_ms)
        cls._active.append(toast)
        toast.destroyed.connect(lambda: cls._active.remove(toast) if toast in cls._active else None)

        # Stack from bottom-right, 16px margin, 8px gap between toasts
        offset_y = 16
        for t in cls._active[:-1]:
            if t.parent() == parent:
                offset_y += t.height() + 8

        parent_rect = parent.rect()
        x = parent_rect.width() - toast.width() - 16
        y = parent_rect.height() - toast.height() - offset_y
        toast.move(x, y)
        toast.raise_()
        toast.show()


# ─────────────────────────────────────────────────────────────────────────────
# INLINE NOTIFICATION (non-popup, embedded in forms)
# ─────────────────────────────────────────────────────────────────────────────

class InAppNotificationDialog(QFrame):
    """Embedded inline notification bar — not a popup dialog."""
    def __init__(self, title: str, message: str, kind: str = "info", parent=None):
        super().__init__(parent)
        bg_map = {
            "success": ("#ECFDF5", "#059669", "#A7F3D0"),
            "error":   ("#FEF2F2", "#DC2626", "#FECACA"),
            "warning": ("#FFFBEB", "#D97706", "#FDE68A"),
            "info":    ("#EFF6FF", "#2563EB", "#BFDBFE"),
        }
        bg, fg, border = bg_map.get(kind, bg_map["info"])
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 6px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        lbl = QLabel(f"<b>{title}</b>  {message}")
        lbl.setStyleSheet(f"color: {fg}; font-size: 12px; border: none; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
