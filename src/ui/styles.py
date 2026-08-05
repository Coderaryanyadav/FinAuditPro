"""
FinAuditPro — Trustworthy Light Sky Blue Design System
Clean, professional, typography-first enterprise UI for statutory financial auditors.
Focus on clarity, trust, high-contrast readability, and subtle sky blue accents.
"""
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from .theme import Colors, Fonts, Spacing

GLOBAL_QSS = """
/* ═══════════════════════════════════════════════════════════
   RESET & BASE TYPOGRAPHY
═══════════════════════════════════════════════════════════ */
* {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont,
                 'Inter', Roboto, sans-serif;
    color: #334155;
}

/* ═══════════════════════════════════════════════════════════
   PAGE BACKGROUNDS — macOS System Light Palette
═══════════════════════════════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #f5f5f7;
}
QWidget#appBg {
    background-color: #f5f5f7;
}

/* ═══════════════════════════════════════════════════════════
   SCROLLBARS — subtle, light, clean macOS scrollbars
═══════════════════════════════════════════════════════════ */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d1d1d6;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #a1a1a6;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { border: none; background: none; }

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #d1d1d6;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #a1a1a6;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { border: none; background: none; }

/* ═══════════════════════════════════════════════════════════
   TOOLTIP
═══════════════════════════════════════════════════════════ */
QToolTip {
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════
   LOGIN — HERO PANEL & CARD
═══════════════════════════════════════════════════════════ */
QFrame#loginHeroPanel {
    background-color: #f5f5f7;
    border-right: 1px solid #e5e5ea;
}

QWidget#loginRightBg {
    background-color: #f5f5f7;
}

QFrame#loginFormContainer {
    background-color: #ffffff;
    border-radius: 16px;
    border: 1px solid #e5e5ea;
}

QPushButton#loginSubmitBtn {
    background-color: #007aff;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    border: none;
}
QPushButton#loginSubmitBtn:hover {
    background-color: #0062cc;
}
QPushButton#loginSubmitBtn:pressed {
    background-color: #004999;
}
QPushButton#loginSubmitBtn:disabled {
    background-color: #e5e5ea;
    color: #a1a1a6;
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR — Apple macOS Minimalist Sidebar
═══════════════════════════════════════════════════════════ */
QFrame#dashboardSidebar {
    background-color: #ffffff;
    border-right: 1px solid #e5e5ea;
}
QFrame#sidebarLogoContainer {
    background-color: transparent;
    border-bottom: 1px solid #e5e5ea;
}
QLabel#sidebarLogoBadge {
    background-color: #1d1d1f;
    color: #ffffff;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#sidebarAppTitle {
    font-size: 15px;
    font-weight: 600;
    color: #1d1d1f;
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
    font-weight: 600;
    color: #86868b;
    padding-left: 14px;
    margin-top: 18px;
    margin-bottom: 6px;
    border: none;
    letter-spacing: 1px;
}
QFrame#sidebarProfileFrame {
    border-top: 1px solid #e5e5ea;
    background-color: #fafafa;
}
QLabel#userAvatar {
    background-color: #e8f2ff;
    color: #007aff;
    border-radius: 15px;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid #cce4ff;
}
QLabel#userName {
    font-size: 13px;
    font-weight: 600;
    color: #1d1d1f;
    border: none;
}
QLabel#userRole {
    font-size: 11px;
    color: #6e6e73;
    border: none;
}

/* Sidebar nav buttons — Apple soft highlight */
QPushButton#navButton {
    background-color: transparent;
    color: #6e6e73;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding-left: 12px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background-color: #f5f5f7;
    color: #1d1d1f;
}
QPushButton#navButton[active="true"] {
    background-color: #f2f7ff;
    color: #007aff;
    font-weight: 600;
    border: none;
    border-left: 3px solid #0284c7;
    border-radius: 8px;
    padding-left: 9px;
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD HEADER BAR — macOS Window Header
═══════════════════════════════════════════════════════════ */
QFrame#dashboardHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5ea;
}
QComboBox#clientSelectorCombo {
    padding: 6px 12px;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    background-color: #f2f2f7;
    color: #1d1d1f;
    font-size: 12px;
    font-weight: 500;
}
QComboBox#clientSelectorCombo:focus {
    background-color: #ffffff;
    border-color: #007aff;
}
QPushButton#iconToolBtn {
    background-color: transparent;
    color: #64748b;
    border-radius: 6px;
    font-size: 14px;
    border: none;
}
QPushButton#iconToolBtn:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}
QLabel#heroTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    border: none;
    letter-spacing: -0.3px;
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
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}
QFrame#metricCard:hover {
    border-color: #cbd5e1;
    background-color: #f8fafc;
}
QLabel#metricTitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    border: none;
    letter-spacing: 0.4px;
}
QLabel#metricValue {
    color: #0f172a;
    font-size: 28px;
    font-weight: 700;
    border: none;
    letter-spacing: -0.5px;
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
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

/* ═══════════════════════════════════════════════════════════
   AI SUMMARY CARD
═══════════════════════════════════════════════════════════ */
QLabel#aiSummaryTitle {
    font-weight: 700;
    font-size: 14px;
    color: #0f172a;
    border: none;
}
QFrame#aiFindingsBox {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QLabel#aiFindingsHeader {
    font-size: 10px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 1px;
    border: none;
}
QLabel#aiFindingItem {
    font-size: 12px;
    color: #334155;
    border: none;
}
QLabel#aiNoFindings {
    font-size: 12px;
    color: #64748b;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   AI COPILOT PANEL
═══════════════════════════════════════════════════════════ */
QFrame#aiHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}
QFrame#aiCardFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
QPushButton#aiPromptBtn {
    background-color: #f8fafc;
    color: #334155;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid #e2e8f0;
    border-radius: 7px;
    padding: 8px 12px;
    text-align: left;
}
QPushButton#aiPromptBtn:hover {
    background-color: #e0f2fe;
    border-color: #bae6fd;
    color: #0284c7;
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
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5ea;
}
QFrame#ollamaOnboardingPanel {
    background-color: #fff8e6;
    border: 1px solid #ffe0b2;
    border-radius: 10px;
}
QLabel#headerTitle {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.2px;
}
QLabel#headerSubtitle {
    font-size: 12px;
    color: #64748b;
    font-weight: 400;
}

/* ═══════════════════════════════════════════════════════════
   CLIENTS PANE
═══════════════════════════════════════════════════════════ */
QFrame#clientsLeftPane {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

/* ═══════════════════════════════════════════════════════════
   DOCUMENT DROP ZONE
═══════════════════════════════════════════════════════════ */
QFrame#docsDropZone {
    background-color: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 10px;
}
QFrame#docsDropZone:hover {
    background-color: #e0f2fe;
    border-color: #0284c7;
}

/* ═══════════════════════════════════════════════════════════
   GLOBAL SEARCH
═══════════════════════════════════════════════════════════ */
QFrame#globalSearchFrame {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
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
    border: 1px solid #e2e8f0;
    background-color: #f1f5f9;
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
    border-radius: 4px;
    padding: 1px 5px;
}
QMenu#globalSearchMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 12px;
    padding: 4px;
}
QMenu#globalSearchMenu::item {
    padding: 8px 14px;
    border-radius: 5px;
    color: #334155;
}
QMenu#globalSearchMenu::item:selected {
    background-color: #e0f2fe;
    color: #0284c7;
}

/* ═══════════════════════════════════════════════════════════
   BUTTONS — Apple macOS Minimalist Design
═══════════════════════════════════════════════════════════ */
QPushButton {
    font-size: 13px;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 500;
    border: none;
    color: #1d1d1f;
    background-color: #ffffff;
}

/* Primary CTA Button */
QPushButton#primaryBtn,
QPushButton#primaryButton {
    background-color: #007aff;
    color: #ffffff;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}
QPushButton#primaryBtn:hover,
QPushButton#primaryButton:hover {
    background-color: #0062cc;
}
QPushButton#primaryBtn:pressed,
QPushButton#primaryButton:pressed {
    background-color: #004999;
}

/* Secondary Button */
QPushButton#secondaryBtn,
QPushButton#secondaryButton {
    background-color: #ffffff;
    color: #1d1d1f;
    font-weight: 500;
    border: 1px solid #e5e5ea;
    padding: 7px 14px;
    border-radius: 8px;
}
QPushButton#secondaryBtn:hover,
QPushButton#secondaryButton:hover {
    background-color: #f5f5f7;
    color: #1d1d1f;
    border-color: #d1d1d6;
}

/* Outline Button */
QPushButton#outlineButton {
    background-color: transparent;
    color: #6e6e73;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton#outlineButton:hover {
    background-color: #f5f5f7;
    color: #1d1d1f;
    border-color: #d1d1d6;
}

/* Danger Button */
QPushButton#dangerBtn {
    background-color: #ffebeb;
    color: #ff3b30;
    border: 1px solid #ffcdd2;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
}
QPushButton#dangerBtn:hover {
    background-color: #ffcdd2;
}

/* ═══════════════════════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════════════════════ */
QLineEdit,
QTextEdit {
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 8px 12px;
    background-color: #ffffff;
    font-size: 13px;
    color: #1d1d1f;
    selection-background-color: rgba(0, 122, 255, 0.2);
}
QLineEdit:focus,
QTextEdit:focus {
    border-color: #007aff;
    outline: none;
}
QLineEdit:hover,
QTextEdit:hover {
    border-color: #d1d1d6;
}
QLineEdit::placeholder,
QLineEdit[text=""] {
    color: #86868b;
}
QLineEdit#searchField {
    padding: 7px 12px;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    background-color: #f2f2f7;
    font-size: 12px;
}
QLineEdit#searchField:focus {
    background-color: #ffffff;
    border-color: #007aff;
}
QLineEdit#formInput {
    padding: 8px 12px;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    background-color: #ffffff;
    color: #1d1d1f;
}

/* ═══════════════════════════════════════════════════════════
   COMBOBOX
═══════════════════════════════════════════════════════════ */
QComboBox {
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 7px 12px;
    background-color: #ffffff;
    color: #1d1d1f;
    font-size: 13px;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #d1d1d6;
}
QComboBox:focus {
    border-color: #007aff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    color: #1d1d1f;
    selection-background-color: #f2f7ff;
    selection-color: #007aff;
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
   TABLES — Apple Minimalist Grid
═══════════════════════════════════════════════════════════ */
QTableWidget,
QTableView {
    background-color: #ffffff;
    gridline-color: #f2f2f7;
    border-radius: 12px;
    border: 1px solid #e5e5ea;
    font-size: 13px;
    outline: none;
    alternate-background-color: #fafafa;
}
QHeaderView::section {
    background-color: #fafafa;
    color: #86868b;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 10px;
    letter-spacing: 0.8px;
    border: none;
    border-bottom: 1px solid #e5e5ea;
}
QTableWidget::item,
QTableView::item {
    padding: 10px 14px;
    border-bottom: 1px solid #f2f2f7;
    color: #1d1d1f;
}
QTableWidget::item:selected,
QTableView::item:selected {
    background-color: #f2f7ff;
    color: #007aff;
}
QTableWidget::item:hover,
QTableView::item:hover {
    background-color: #f5f5f7;
}

/* ═══════════════════════════════════════════════════════════
   TAB WIDGET — Universal Apple Underline / Segmented
═══════════════════════════════════════════════════════════ */
QTabWidget::pane {
    border: 1px solid #e5e5ea;
    background: #ffffff;
    border-radius: 14px;
}
QTabWidget#styledTabWidget::pane {
    border: 1px solid #e5e5ea;
    background: #ffffff;
    border-radius: 14px;
}
QTabBar::tab,
QTabWidget#styledTabWidget QTabBar::tab {
    background: transparent;
    color: #6e6e73;
    padding: 9px 18px;
    font-weight: 500;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}
QTabBar::tab:selected,
QTabWidget#styledTabWidget QTabBar::tab:selected {
    color: #007aff;
    border-bottom: 2px solid #007aff;
    font-weight: 600;
}
QTabBar::tab:hover:!selected,
QTabWidget#styledTabWidget QTabBar::tab:hover:!selected {
    color: #1d1d1f;
}
QTabBar {
    background: transparent;
    border: none;
    border-bottom: 1px solid #e5e5ea;
}

/* ═══════════════════════════════════════════════════════════
   PROGRESS BARS
═══════════════════════════════════════════════════════════ */
QProgressBar {
    border: none;
    background-color: #e2e8f0;
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
    color: #475569;
    font-size: 12px;
    font-weight: 400;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
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
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #0f172a;
    font-size: 13px;
}
QMessageBox QPushButton {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
    min-width: 70px;
}
QMessageBox QPushButton:hover {
    background-color: #f8fafc;
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
   MISC LABELS
═══════════════════════════════════════════════════════════ */
QLabel#barTitle {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
    border: none;
}
QLabel#donutCenterLabel {
    border: none;
    background: transparent;
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
}
QLabel#legendText {
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   STATUS BADGES — LIGHT THEME
═══════════════════════════════════════════════════════════ */
QLabel#statusBadgeBlue {
    background-color: #e0f2fe;
    color: #0284c7;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid #bae6fd;
}
QLabel#statusBadgeGreen {
    background-color: #dcfce7;
    color: #15803d;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid #bbf7d0;
}
QLabel#statusBadgeAmber {
    background-color: #fef3c7;
    color: #b45309;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid #fde68a;
}
QLabel#statusBadgeRed {
    background-color: #fee2e2;
    color: #b91c1c;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid #fecaca;
}

/* ═══════════════════════════════════════════════════════════
   SETTINGS SECTIONS
═══════════════════════════════════════════════════════════ */
QFrame#settingsSection {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
QLabel#settingsSectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    border: none;
}

/* ═══════════════════════════════════════════════════════════
   COMPLIANCE / HISTORY ROW CARDS & TABLES
═══════════════════════════════════════════════════════════ */
QFrame#complianceTaskRow {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QFrame#complianceTaskRow:hover {
    border-color: #cbd5e1;
    background: #f8fafc;
}
QPushButton#saveBtn {
    background-color: #34c759;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}
QPushButton#saveBtn:hover {
    background-color: #28a745;
}
QTabWidget#complianceTabPane::pane {
    border: 1px solid #e5e5ea;
    background: #ffffff;
    border-radius: 14px;
    margin: 16px 24px 24px 24px;
}
QTableWidget#complianceTable {
    border: 1px solid #e2e8f0;
    gridline-color: #f1f5f9;
    background: #ffffff;
    border-radius: 6px;
}
QTableWidget#complianceTable QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}

/* ═══════════════════════════════════════════════════════════
   OLLAMA ONBOARDING PANEL & AI COPILOT COMPONENTS
═══════════════════════════════════════════════════════════ */
QFrame#ollamaOnboardingPanel {
    background-color: #fff8e6;
    border: 1px solid #ffe0b2;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
}
QLabel#onboardingTitle {
    font-weight: 700;
    font-size: 13px;
    color: #9a3412;
    border: none;
}
QLabel#onboardingDesc {
    font-size: 11px;
    color: #7c2d12;
    line-height: 1.5;
    border: none;
}
QLabel#onboardingFallbackNote {
    font-size: 10px;
    color: #9a3412;
    font-style: italic;
    border: none;
    margin-top: 4px;
}
/* ═══════════════════════════════════════════════════════════
   AI COPILOT & ANOMALY INSPECTOR COMPONENTS
═══════════════════════════════════════════════════════════ */
QFrame#aiHeader {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}
QLabel#aiTitle {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.3px;
    border: none;
}
QLabel#aiSubtitle {
    font-size: 11px;
    color: #64748b;
    border: none;
}
QFrame#aiColHeader {
    background-color: #f1f5f9;
    border-bottom: 1px solid #e2e8f0;
}
QLabel#aiColTitle {
    font-size: 10px;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.8px;
    border: none;
}
QTextEdit#aiDocContent {
    background-color: #ffffff;
    margin: 10px;
    padding: 14px;
    border: 1px solid #cbd5e1;
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
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-right: 40px;
}
QLabel#chatSenderUser {
    font-size: 10px;
    font-weight: 700;
    border: none;
    color: rgba(255, 255, 255, 0.9);
}
QLabel#chatSenderAI {
    font-size: 10px;
    font-weight: 700;
    border: none;
    color: #64748b;
}
QLabel#chatMsgUser {
    font-size: 12px;
    border: none;
    color: #ffffff;
}
QLabel#chatMsgAI {
    font-size: 12px;
    border: none;
    color: #0f172a;
}
QTextEdit#chatInput {
    border: 1px solid #cbd5e1;
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
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-bottom: 10px;
}
QLabel#findingCardTitle {
    font-weight: 700;
    font-size: 13px;
    color: #0f172a;
    border: none;
}
QLabel#findingCardDesc {
    color: #475569;
    font-size: 12px;
    line-height: 1.4;
    border: none;
}
QFrame#evidenceBox {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}
QLabel#evidenceTitle {
    color: #94a3b8;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.6px;
    border: none;
}
QLabel#evidenceData {
    color: #0f172a;
    font-size: 11px;
    font-weight: 600;
    font-family: monospace;
    border: none;
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
QPushButton#btnIngestWP:disabled {
    background-color: #10b981;
    color: #ffffff;
}

/* ═══════════════════════════════════════════════════════════
   WORKING PAPERS & CLIENT CRM PANELS
═══════════════════════════════════════════════════════════ */
QFrame#wpSignoffBox {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
}
QFrame#clientFormCard {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 12px;
    padding: 16px;
}

/* ═══════════════════════════════════════════════════════════
   LOGIN WINDOW COMPONENTS
═══════════════════════════════════════════════════════════ */
QFrame#loginHeroPanel {
    background-color: #ffffff;
    border-right: 1px solid #e5e5ea;
}
QWidget#loginRightBg {
    background-color: #f5f5f7;
}
QFrame#loginFormContainer {
    background-color: #ffffff;
    border-radius: 14px;
    border: 1px solid #e5e5ea;
}
QPushButton#loginSubmitBtn {
    background-color: #0284c7;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    border: none;
}
QPushButton#loginSubmitBtn:hover {
    background-color: #0369a1;
}
QPushButton#loginSubmitBtn:pressed {
    background-color: #075985;
}
QPushButton#loginSubmitBtn:disabled {
    background-color: #f1f5f9;
    color: #cbd5e1;
}

/* ═══════════════════════════════════════════════════════════
   DROP ZONE & DOCUMENT INGESTION
═══════════════════════════════════════════════════════════ */
QFrame#dropZone {
    background-color: #f0f9ff;
    border: 2px dashed #0ea5e9;
    border-radius: 8px;
}
QFrame#dropZoneHover {
    background-color: #e0f2fe;
    border: 2px dashed #0284c7;
    border-radius: 8px;
}

/* ═══════════════════════════════════════════════════════════
   SPLITTER
═══════════════════════════════════════════════════════════ */
QSplitter::handle {
    background: #e2e8f0;
    width: 1px;
    height: 1px;
}

/* ═══════════════════════════════════════════════════════════
   AI COPILOT CHIPS & BADGES
═══════════════════════════════════════════════════════════ */
QPushButton#promptChipBtn {
    background-color: #f1f5f9;
    color: #0284c7;
    border: 1px solid #bae6fd;
    border-radius: 12px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#promptChipBtn:hover {
    background-color: #e0f2fe;
    border-color: #7dd3fc;
}
QLabel#statusBadgeGreen {
    background-color: #ecfdf5;
    color: #059669;
    border: 1px solid #a7f3d0;
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: bold;
}
QLabel#statusBadgeAmber {
    background-color: #fffbeb;
    color: #d97706;
    border: 1px solid #fde68a;
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: bold;
}
QLabel#statusBadgeRed {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: bold;
}
"""


def apply_shadow(widget, blur: int = 20, dx: int = 0, dy: int = 4, alpha: int = 30):
    """Subtle shadow for light theme."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(dx)
    shadow.setYOffset(dy)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)


class EmptyStateWidget(QWidget):
    """Empty state for tables / lists — clean, light."""
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
        icon_lbl.setStyleSheet("font-size: 32px; border: none; background: transparent; color: #94a3b8;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #334155; border: none; margin-top: 8px;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            "font-size: 12px; color: #64748b; border: none; margin-top: 2px;"
        )
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)

        cl.addWidget(icon_lbl)
        cl.addWidget(title_lbl)
        cl.addWidget(desc_lbl)
        layout.addWidget(container)


class LoadingStateWidget(QWidget):
    """Loading indicator — clean light bar."""
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
            "font-size: 13px; font-weight: 500; color: #475569; border: none;"
        )
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pbar = QProgressBar()
        pbar.setRange(0, 0)
        pbar.setFixedHeight(3)
        pbar.setStyleSheet("""
            QProgressBar { border: none; background-color: #e2e8f0; border-radius: 1px; }
            QProgressBar::chunk { background-color: #0284c7; border-radius: 1px; }
        """)

        cl.addWidget(msg_lbl)
        cl.addWidget(pbar)
        layout.addWidget(container)


class ErrorStateWidget(QWidget):
    """Error state — clean light warning badge."""
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
                background: #fff5f5;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 24px;
            }
        """)
        cl = QVBoxLayout(container)
        cl.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #dc2626; border: none;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        details_lbl = QLabel(str(details))
        details_lbl.setStyleSheet(
            "font-size: 12px; color: #991b1b; border: none; margin-top: 4px;"
        )
        details_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_lbl.setWordWrap(True)

        cl.addWidget(title_lbl)
        cl.addWidget(details_lbl)
        layout.addWidget(container)
