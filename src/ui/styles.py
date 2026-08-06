"""
FinAuditPro — Sky Blue + White Audit Design System
Clean, professional, modern enterprise light UI for statutory financial auditors.
Pure white card surfaces (#ffffff) on pale ice blue background (#f0f6ff) with sky blue accents (#0284c7, #38bdf8).
"""
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from .theme import Colors, Fonts, Spacing

GLOBAL_QSS = """
/* ═══════════════════════════════════════════════════════════
   UNIVERSAL BASE RESETS & TYPOGRAPHY
═══════════════════════════════════════════════════════════ */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
}

QWidget {
    background-color: transparent;
    color: #0f172a;
}

QLabel {
    background-color: transparent;
    border: none;
    color: #0f172a;
}

QFrame {
    background-color: transparent;
    border: none;
}

QScrollArea, QScrollArea > QWidget, QScrollArea #qt_scrollarea_viewport {
    background-color: #f0f6ff;
    border: none;
}

QChartView {
    background-color: transparent;
    background: transparent;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   PAGE BACKGROUNDS — Slate Dark Palette
═══════════════════════════════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #f0f6ff;
}
QWidget#appBg {
    background-color: #f0f6ff;
}

/* ═══════════════════════════════════════════════════════════
   SCROLLBARS — Sleek Dark Scrollbars
═══════════════════════════════════════════════════════════ */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { border: none; background: none; }

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { border: none; background: none; }

/* ═══════════════════════════════════════════════════════════
   TOOLTIP
═══════════════════════════════════════════════════════════ */
QToolTip {
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #0284c7;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════
   LOGIN — HERO PANEL & CARD
═══════════════════════════════════════════════════════════ */
QFrame#loginHeroPanel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0f172a, stop:1 #1e293b);
    border-right: 1px solid #1e293b;
}

QWidget#loginRightBg {
    background-color: #f0f6ff;
}

QFrame#loginFormContainer {
    background-color: #ffffff;
    border-radius: 16px;
    border: 1px solid #e1e8f4;
}

QPushButton#loginSubmitBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    border: 1px solid #0284c7;
    letter-spacing: 0.3px;
}
QPushButton#loginSubmitBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0369a1, stop:1 #075985);
    border-color: #38bdf8;
}
QPushButton#loginSubmitBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #075985, stop:1 #0369a1);
}
QPushButton#loginSubmitBtn:disabled {
    background: #e2e8f0;
    color: #94a3b8;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR — Slate Premium Sidebar
═══════════════════════════════════════════════════════════ */
QFrame#dashboardSidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}
QFrame#sidebarLogoContainer {
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
QLabel#sidebarLogoBadge {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 800;
}
QLabel#sidebarAppTitle {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    border: none;
    letter-spacing: -0.3px;
}
QScrollArea#sidebarNavScroll {
    background: transparent;
    border: none;
}
QWidget#sidebarNavWidget {
    background: transparent;
}
QLabel#sidebarSectionLabel {
    font-size: 10px;
    font-weight: 800;
    color: #38bdf8;
    padding-left: 14px;
    margin-top: 18px;
    margin-bottom: 6px;
    border: none;
    letter-spacing: 1.4px;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background-color: #060911;
}
QLabel#userAvatar {
    background-color: #0284c7;
    color: #ffffff;
    border-radius: 15px;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid #38bdf8;
}
QLabel#userName {
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    border: none;
}
QLabel#userRole {
    font-size: 11px;
    color: #94a3b8;
    border: none;
}

/* Sidebar nav buttons */
QPushButton#navButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding-left: 12px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}
QPushButton#navButton[active="true"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(56, 189, 248, 0.22), stop:1 transparent);
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-left: 3px solid #38bdf8;
    border-radius: 8px;
    padding-left: 9px;
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD HEADER BAR
═══════════════════════════════════════════════════════════ */
QFrame#dashboardHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e1e8f4;
}
QComboBox#clientSelectorCombo {
    padding: 6px 12px;
    border: 1px solid #e1e8f4;
    border-radius: 8px;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 12px;
    font-weight: 500;
}
QComboBox#clientSelectorCombo:focus {
    background-color: #ffffff;
    border-color: #0284c7;
}
QPushButton#iconToolBtn {
    background-color: transparent;
    color: #64748b;
    border-radius: 6px;
    font-size: 14px;
    border: none;
}
QPushButton#iconToolBtn:hover {
    background-color: #e0f2fe;
    color: #0284c7;
}
QLabel#heroTitle {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    border: none;
    letter-spacing: -0.4px;
}
QLabel#heroSub {
    font-size: 13px;
    color: #64748b;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   METRIC CARDS
═══════════════════════════════════════════════════════════ */
QFrame#metricCard {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 14px;
}
QFrame#metricCard:hover {
    border-color: #0284c7;
    background-color: #f8fafc;
}
QLabel#metricTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    border: none;
    background: transparent;
    letter-spacing: 0.6px;
}
QLabel#metricValue {
    color: #0f172a;
    font-size: 30px;
    font-weight: 700;
    border: none;
    background: transparent;
    letter-spacing: -0.6px;
}

/* ═══════════════════════════════════════════════════════════
   CONTENT CARDS
═══════════════════════════════════════════════════════════ */
QFrame#contentCard,
QFrame#recentProjectsTableFrame,
QFrame#aiSummaryCard,
QFrame#auditProgressCard,
QFrame#riskDistributionCard,
QFrame#cardFrame {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 14px;
}

/* ═══════════════════════════════════════════════════════════
   AI SUMMARY CARD
═══════════════════════════════════════════════════════════ */
QLabel#aiSummaryTitle {
    font-weight: 700;
    font-size: 15px;
    color: #f8fafc;
    border: none;
    background: transparent;
}
QFrame#aiFindingsBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
}
QLabel#aiFindingsHeader {
    font-size: 10px;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 1px;
    border: none;
    background: transparent;
}
QLabel#aiFindingItem {
    font-size: 12px;
    color: #cbd5e1;
    border: none;
    background: transparent;
}
QLabel#aiNoFindings {
    font-size: 12px;
    color: #94a3b8;
    border: none;
    background: transparent;
}

/* ═══════════════════════════════════════════════════════════
   AI COPILOT PANEL
═══════════════════════════════════════════════════════════ */
QFrame#aiHeader {
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
}
QFrame#aiCardFrame {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
}
QPushButton#aiPromptBtn {
    background-color: #0f172a;
    color: #cbd5e1;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
}
QPushButton#aiPromptBtn:hover {
    background-color: rgba(2, 132, 199, 0.2);
    border-color: #38bdf8;
    color: #38bdf8;
}

/* ═══════════════════════════════════════════════════════════
   SECTION / ACTION HEADER BARS & BOOTSTRAP PANELS
═══════════════════════════════════════════════════════════ */
QFrame#actionHeader,
QFrame#clientsHeader,
QFrame#docsHeader,
QFrame#headerBar,
QFrame#historyHeader,
QFrame#reportsHeader,
QFrame#settingsHeader {
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
}
QFrame#ollamaOnboardingPanel {
    background-color: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 10px;
}
QLabel#headerTitle {
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.3px;
    background: transparent;
}
QLabel#headerSubtitle {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 400;
    background: transparent;
}

/* ═══════════════════════════════════════════════════════════
   CLIENTS PANE
═══════════════════════════════════════════════════════════ */
QFrame#clientsLeftPane {
    background-color: #1e293b;
    border-right: 1px solid #334155;
}

/* ═══════════════════════════════════════════════════════════
   DOCUMENT DROP ZONE
═══════════════════════════════════════════════════════════ */
QFrame#docsDropZone {
    background-color: #0f172a;
    border: 1px dashed #475569;
    border-radius: 10px;
}
QFrame#docsDropZone:hover {
    background-color: rgba(2, 132, 199, 0.15);
    border-color: #38bdf8;
}

/* ═══════════════════════════════════════════════════════════
   GLOBAL SEARCH
═══════════════════════════════════════════════════════════ */
QFrame#globalSearchFrame {
    background-color: #f8fafc;
    border: 1px solid #e1e8f4;
    border-radius: 8px;
}
QLineEdit#globalSearchInput {
    border: none;
    background: transparent;
    font-size: 12px;
    color: #0f172a;
}
QLabel#globalSearchIcon {
    border: none;
    font-size: 13px;
    color: #64748b;
    background: transparent;
}
QLabel#globalShortcutBadge {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
    border-radius: 4px;
    padding: 1px 5px;
}
QMenu#globalSearchMenu {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    color: #0f172a;
}
    border-radius: 8px;
    font-size: 12px;
    padding: 4px;
}
QMenu#globalSearchMenu::item {
    padding: 8px 14px;
    border-radius: 5px;
    color: #cbd5e1;
}
QMenu#globalSearchMenu::item:selected {
    background-color: #0284c7;
    color: #ffffff;
}

/* ═══════════════════════════════════════════════════════════
   BUTTONS — Vibrant Dark Accent CTAs
═══════════════════════════════════════════════════════════ */
QPushButton {
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 500;
    border: none;
    color: #f8fafc;
    background-color: #1e293b;
}

/* Primary CTA Button */
QPushButton#primaryBtn,
QPushButton#primaryButton {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}
QPushButton#primaryBtn:hover,
QPushButton#primaryButton:hover {
    background-color: #0369a1;
}
QPushButton#primaryBtn:pressed,
QPushButton#primaryButton:pressed {
    background-color: #075985;
}

/* Secondary Button */
QPushButton#secondaryBtn,
QPushButton#secondaryButton {
    background-color: #1e293b;
    color: #f8fafc;
    font-weight: 500;
    border: 1px solid #334155;
    padding: 7px 14px;
    border-radius: 8px;
}
QPushButton#secondaryBtn:hover,
QPushButton#secondaryButton:hover {
    background-color: #334155;
    border-color: #475569;
}

/* Outline Button */
QPushButton#outlineButton {
    background-color: transparent;
    color: #cbd5e1;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton#outlineButton:hover {
    background-color: #1e293b;
    color: #f8fafc;
    border-color: #475569;
}

/* Danger Button */
QPushButton#dangerBtn {
    background-color: rgba(244, 63, 94, 0.15);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.4);
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton#dangerBtn:hover {
    background-color: rgba(244, 63, 94, 0.3);
}

/* ═══════════════════════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════════════════════ */
QLineEdit,
QTextEdit {
    border: 1.5px solid #e1e8f4;
    border-radius: 8px;
    padding: 8px 12px;
    background-color: #ffffff;
    font-size: 13px;
    color: #0f172a;
    selection-background-color: rgba(2, 132, 199, 0.2);
}
QLineEdit:focus,
QTextEdit:focus {
    border-color: #0284c7;
    background-color: #ffffff;
    outline: none;
}
QLineEdit:hover,
QTextEdit:hover {
    border-color: #93c5fd;
}
QLineEdit::placeholder {
    color: #94a3b8;
}
QLineEdit#searchField {
    padding: 7px 12px;
    border: 1.5px solid #e1e8f4;
    border-radius: 8px;
    background-color: #f8fafc;
    font-size: 12px;
}
QLineEdit#searchField:focus {
    background-color: #ffffff;
    border-color: #0284c7;
}
QLineEdit#formInput {
    padding: 8px 12px;
    border: 1.5px solid #e1e8f4;
    border-radius: 8px;
    background-color: #ffffff;
    color: #0f172a;
}

/* ═══════════════════════════════════════════════════════════
   COMBOBOX
═══════════════════════════════════════════════════════════ */
QComboBox {
    border: 1.5px solid #e1e8f4;
    border-radius: 8px;
    padding: 7px 12px;
    background-color: #ffffff;
    color: #0f172a;
    font-size: 13px;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #93c5fd;
}
QComboBox:focus {
    border-color: #0284c7;
    background-color: #ffffff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 8px;
    color: #0f172a;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    outline: none;
    padding: 4px;
}
QComboBox#formCombo {
    padding: 8px 12px;
}
QComboBox#periodCombo {
    font-size: 11px;
    padding: 5px 10px;
}

/* ═══════════════════════════════════════════════════════════
   TABLES — Light Sky Grid
═══════════════════════════════════════════════════════════ */
QTableWidget,
QTableView,
QTableView::viewport,
QTableWidget::viewport {
    background-color: #ffffff;
    gridline-color: #f0f6ff;
    border-radius: 12px;
    border: none;
    font-size: 13px;
    outline: none;
    color: #334155;
}
QHeaderView,
QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    padding: 10px 14px;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 0.8px;
    border: none;
    border-bottom: 1px solid #e1e8f4;
}
QTableWidget::item,
QTableView::item {
    padding: 10px 14px;
    border-bottom: 1px solid #f0f6ff;
    color: #334155;
}
QTableWidget::item:selected,
QTableView::item:selected {
    background-color: rgba(2, 132, 199, 0.12);
    color: #0f172a;
}
QTableWidget::item:hover,
QTableView::item:hover {
    background-color: #f8fafc;
}

/* ═══════════════════════════════════════════════════════════
   TAB WIDGET — Dark Segmented Tabs
═══════════════════════════════════════════════════════════ */
QTabWidget::pane {
    border: 1px solid #e1e8f4;
    background: #ffffff;
    border-radius: 14px;
}
QTabWidget#styledTabWidget::pane {
    border: 1px solid #e1e8f4;
    background: #ffffff;
    border-radius: 14px;
}
QTabBar::tab,
QTabWidget#styledTabWidget QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 9px 18px;
    font-weight: 500;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}
QTabBar::tab:selected,
QTabWidget#styledTabWidget QTabBar::tab:selected {
    color: #0284c7;
    border-bottom: 2px solid #0284c7;
    font-weight: 600;
}
QTabBar::tab:hover:!selected,
QTabWidget#styledTabWidget QTabBar::tab:hover:!selected {
    color: #0f172a;
}
QTabBar {
    background: transparent;
    border: none;
    border-bottom: 1px solid #e1e8f4;
}

/* ═══════════════════════════════════════════════════════════
   PROGRESS BARS
═══════════════════════════════════════════════════════════ */
QProgressBar {
    border: none;
    background-color: #e1e8f4;
    border-radius: 3px;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #0284c7;
    border-radius: 3px;
}

/* ═══════════════════════════════════════════════════════════
   CHECKBOXES
═══════════════════════════════════════════════════════════ */
QCheckBox {
    border: none;
    background: transparent;
    color: #334155;
    font-size: 12px;
    font-weight: 400;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #e1e8f4;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #0284c7;
    border-color: #0284c7;
}
QCheckBox::indicator:hover {
    border-color: #0284c7;
}

/* ═══════════════════════════════════════════════════════════
   DIALOG / MESSAGE BOX
═══════════════════════════════════════════════════════════ */
QDialog {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 12px;
}
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #0f172a;
    font-size: 13px;
    background: transparent;
}
QMessageBox QPushButton {
    background-color: #f8fafc;
    color: #334155;
    border: 1px solid #e1e8f4;
    border-radius: 7px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
    min-width: 70px;
}
QMessageBox QPushButton:hover {
    background-color: #e1e8f4;
    color: #0f172a;
}
QMessageBox QPushButton:default {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
}
QMessageBox QPushButton:default:hover {
    background-color: #0369a1;
}

/* ═══════════════════════════════════════════════════════════
   STATUS BADGES — Slate Dark
═══════════════════════════════════════════════════════════ */
QLabel#statusBadgeBlue {
    background-color: rgba(2, 132, 199, 0.1);
    color: #0284c7;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid rgba(2, 132, 199, 0.3);
}
QLabel#statusBadgeGreen {
    background-color: rgba(16, 185, 129, 0.12);
    color: #047857;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
QLabel#statusBadgeAmber {
    background-color: rgba(217, 119, 6, 0.1);
    color: #d97706;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid rgba(217, 119, 6, 0.3);
}
QLabel#statusBadgeRed {
    background-color: rgba(220, 38, 38, 0.1);
    color: #dc2626;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid rgba(220, 38, 38, 0.3);
}

/* ═══════════════════════════════════════════════════════════
   SETTINGS SECTIONS & COMPLIANCE CARDS
═══════════════════════════════════════════════════════════ */
QFrame#settingsSection,
QFrame#complianceTaskRow,
QFrame#wpSignoffBox,
QFrame#clientFormCard {
    background: #ffffff;
    border: 1px solid #d1fae5;
    border-radius: 10px;
}
QFrame#complianceTaskRow:hover {
    border-color: #059669;
    background: #f0fdf4;
}
QLabel#settingsSectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #064e3b;
    border: none;
    background: transparent;
}
QPushButton#saveBtn {
    background-color: #059669;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}
QPushButton#saveBtn:hover {
    background-color: #059669;
}
QTabWidget#complianceTabPane::pane {
    border: 1px solid #e1e8f4;
    background: #ffffff;
    border-radius: 14px;
    margin: 16px 24px 24px 24px;
}
QTableWidget#complianceTable {
    border: 1px solid #e1e8f4;
    gridline-color: #f0f6ff;
    background: #ffffff;
    border-radius: 6px;
    color: #334155;
}
QTableWidget#complianceTable QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e1e8f4;
}

/* ═══════════════════════════════════════════════════════════
   OLLAMA ONBOARDING PANEL & AI COPILOT COMPONENTS
═══════════════════════════════════════════════════════════ */
QFrame#ollamaOnboardingPanel {
    background-color: #fffbe6;
    border: 1px solid #ffe58f;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
}
QLabel#onboardingTitle {
    font-weight: 700;
    font-size: 13px;
    color: #d97706;
    border: none;
    background: transparent;
}
QLabel#onboardingDesc {
    font-size: 11px;
    color: #92400e;
    line-height: 1.5;
    border: none;
    background: transparent;
}
QLabel#onboardingFallbackNote {
    font-size: 10px;
    color: #d97706;
    font-style: italic;
    border: none;
    margin-top: 4px;
    background: transparent;
}

/* ═══════════════════════════════════════════════════════════
   AI COPILOT & ANOMALY INSPECTOR COMPONENTS
═══════════════════════════════════════════════════════════ */
QFrame#aiHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e1e8f4;
}
QLabel#aiTitle {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.3px;
    border: none;
    background: transparent;
}
QLabel#aiSubtitle {
    font-size: 11px;
    color: #64748b;
    border: none;
    background: transparent;
}
QFrame#aiColHeader {
    background-color: #e0f2fe;
    border-bottom: 1px solid #e1e8f4;
}
QLabel#aiColTitle {
    font-size: 10px;
    font-weight: 700;
    color: #0284c7;
    letter-spacing: 0.8px;
    border: none;
    background: transparent;
}
QTextEdit#aiDocContent {
    background-color: #f8fafc;
    margin: 10px;
    padding: 14px;
    border: 1px solid #e1e8f4;
    border-radius: 8px;
    font-family: monospace;
    font-size: 11px;
    color: #0f172a;
}
QFrame#chatBubbleUser {
    background-color: #0284c7;
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 12px;
    margin-left: 40px;
}
QFrame#chatBubbleAI {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #e1e8f4;
    border-radius: 12px;
    margin-right: 40px;
}
QLabel#chatSenderUser {
    font-size: 10px;
    font-weight: 700;
    border: none;
    color: rgba(255, 255, 255, 0.9);
    background: transparent;
}
QLabel#chatSenderAI {
    font-size: 10px;
    font-weight: 700;
    border: none;
    color: #0284c7;
    background: transparent;
}
QLabel#chatMsgUser {
    font-size: 12px;
    border: none;
    color: #ffffff;
    background: transparent;
}
QLabel#chatMsgAI {
    font-size: 12px;
    border: none;
    color: #0f172a;
    background: transparent;
}
QTextEdit#chatInput {
    border: 1px solid #e1e8f4;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    background-color: #ffffff;
    color: #0f172a;
}
QTextEdit#chatInput:focus {
    border-color: #0284c7;
}
QPushButton#chatSendBtn {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    border-radius: 8px;
    border: 1px solid #0284c7;
    padding: 8px 16px;
}
QPushButton#chatSendBtn:hover {
    background-color: #0369a1;
    border-color: #0369a1;
}

QFrame#findingCard {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 10px;
    margin-bottom: 10px;
}
QLabel#findingCardTitle {
    font-weight: 700;
    font-size: 13px;
    color: #0f172a;
    border: none;
    background: transparent;
}
QLabel#findingCardDesc {
    color: #334155;
    font-size: 12px;
    line-height: 1.4;
    border: none;
    background: transparent;
}
QFrame#evidenceBox {
    background-color: #f8fafc;
    border: 1px solid #e1e8f4;
    border-radius: 6px;
}
QLabel#evidenceTitle {
    color: #64748b;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.6px;
    border: none;
    background: transparent;
}
QLabel#evidenceData {
    color: #0284c7;
    font-size: 11px;
    font-weight: 600;
    font-family: monospace;
    border: none;
    background: transparent;
}
QPushButton#btnIngestWP {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    font-size: 11px;
    font-weight: 600;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton#btnIngestWP:hover {
    background-color: #0369a1;
}

/* ═══════════════════════════════════════════════════════════
   WORKING PAPERS & CLIENT CRM PANELS
═══════════════════════════════════════════════════════════ */
QFrame#wpSignoffBox {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 8px;
}
QFrame#clientFormCard {
    background-color: #ffffff;
    border: 1px solid #e1e8f4;
    border-radius: 12px;
    padding: 16px;
}

/* ═══════════════════════════════════════════════════════════
   SPLITTER
═══════════════════════════════════════════════════════════ */
QSplitter::handle {
    background: #e1e8f4;
    width: 1px;
    height: 1px;
}

/* ═══════════════════════════════════════════════════════════
   AI COPILOT CHIPS & BADGES
═══════════════════════════════════════════════════════════ */
QPushButton#promptChipBtn {
    background-color: #ffffff;
    color: #0284c7;
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#promptChipBtn:hover {
    background-color: #e0f2fe;
    border-color: #0284c7;
}
"""


def apply_shadow(widget, blur: int = 20, dx: int = 0, dy: int = 4, alpha: int = 40):
    """Subtle shadow for dark theme."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class EmptyStateWidget(QWidget):
    """Empty state for tables / lists — clean dark."""
    def __init__(
        self,
        title: str = "Nothing here yet",
        description: str = "No records match the current filters.",
        icon: str = "·",
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 24px;
            }
        """)
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 32px; border: none; background: transparent; color: #64748b;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #f8fafc; border: none; margin-top: 8px;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            "font-size: 12px; color: #94a3b8; border: none; margin-top: 2px;"
        )
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)

        cl.addWidget(icon_lbl)
        cl.addWidget(title_lbl)
        cl.addWidget(desc_lbl)
        layout.addWidget(container)


class LoadingStateWidget(QWidget):
    """Loading indicator — clean dark bar."""
    def __init__(self, message: str = "Loading…"):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setFixedWidth(280)
        container.setStyleSheet("QFrame { background: transparent; border: none; }")
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setSpacing(14)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 500; color: #cbd5e1; border: none;"
        )
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pbar = QProgressBar()
        pbar.setRange(0, 0)
        pbar.setFixedHeight(3)
        pbar.setStyleSheet("""
            QProgressBar { border: none; background-color: #334155; border-radius: 1px; }
            QProgressBar::chunk { background-color: #38bdf8; border-radius: 1px; }
        """)

        cl.addWidget(msg_lbl)
        cl.addWidget(pbar)
        layout.addWidget(container)


class ErrorStateWidget(QWidget):
    """Error state — clean dark warning badge."""
    def __init__(
        self,
        title: str = "Something went wrong",
        details: str = "An unexpected error occurred. Please try again.",
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        container = QFrame()
        container.setMaximumWidth(480)
        container.setStyleSheet("""
            QFrame {
                background: rgba(244, 63, 94, 0.1);
                border: 1px solid rgba(244, 63, 94, 0.3);
                border-radius: 10px;
                padding: 24px;
            }
        """)
        cl = QVBoxLayout(container)
        cl.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #fb7185; border: none;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        details_lbl = QLabel(str(details))
        details_lbl.setStyleSheet(
            "font-size: 12px; color: #fca5a5; border: none; margin-top: 4px;"
        )
        details_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_lbl.setWordWrap(True)

        cl.addWidget(title_lbl)
        cl.addWidget(details_lbl)
        layout.addWidget(container)
