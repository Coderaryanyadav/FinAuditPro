"""Global Header Bar component for FinAuditPro application shell."""


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from finauditpro.ui.widgets.custom_combo import CustomComboBox


class GlobalHeaderBar(QFrame):
    """Persistent top header bar showing active firm, client, FY, engagement, search, AI toggle, and new engagement."""

    search_clicked = Signal()
    new_engagement_clicked = Signal()
    copilot_toggled = Signal()
    engagement_changed = Signal(int)
    empty_engagement_clicked = Signal()
    profile_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardHeader")
        self.setFixedHeight(60)
        self.setStyleSheet(
            "QFrame#dashboardHeader { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; }"
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        # Global Search Frame (⌘P)
        search_frame = QFrame()
        search_frame.setObjectName("globalSearchFrame")
        search_frame.setStyleSheet(
            "QFrame#globalSearchFrame { background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; }"
            "QFrame#globalSearchFrame:hover { border-color: #0284C7; background: #FFFFFF; }"
        )
        sf_layout = QHBoxLayout(search_frame)
        sf_layout.setContentsMargins(10, 4, 10, 4)
        sf_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("globalSearchInput")
        self.search_input.setPlaceholderText("Search engagements, clients, tools (⌘P)...")
        self.search_input.setReadOnly(True)
        self.search_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_input.setStyleSheet(
            "QLineEdit { border: none; background: transparent; font-size: 12px; color: #334155; }"
        )
        self.search_input.mousePressEvent = lambda e: self.search_clicked.emit()

        shortcut_badge = QLabel("⌘P")
        shortcut_badge.setObjectName("globalShortcutBadge")
        shortcut_badge.setStyleSheet(
            "QLabel { background: #E2E8F0; color: #475569; font-size: 10px; font-weight: 700; border-radius: 3px; padding: 2px 6px; }"
        )

        sf_layout.addWidget(self.search_input)
        sf_layout.addWidget(shortcut_badge)
        layout.addWidget(search_frame, stretch=0)

        layout.addStretch(1)

        # Active Context Pills Frame (Firm / Client / FY / Engagement)
        context_frame = QFrame()
        context_frame.setStyleSheet(
            "QFrame { background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 6px; padding: 2px 6px; }"
        )
        cf_layout = QHBoxLayout(context_frame)
        cf_layout.setContentsMargins(6, 2, 6, 2)
        cf_layout.setSpacing(8)

        lbl_active_tag = QLabel("ACTIVE AUDIT:")
        lbl_active_tag.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B;")

        self.eng_selector_combo = CustomComboBox()
        self.eng_selector_combo.setObjectName("clientSelectorCombo")
        self.eng_selector_combo.setMinimumWidth(260)
        self.eng_selector_combo.setStyleSheet(
            "QComboBox { border: 1px solid #CBD5E1; border-radius: 4px; background: #FFFFFF; font-size: 12px; font-weight: 600; color: #0F172A; padding: 4px 8px; }"
            "QComboBox::drop-down { border: none; }"
        )
        self.eng_selector_combo.currentIndexChanged.connect(
            lambda idx: self.engagement_changed.emit(idx)
        )
        self.eng_selector_combo.empty_clicked.connect(
            lambda: self.empty_engagement_clicked.emit()
        )

        cf_layout.addWidget(lbl_active_tag)
        cf_layout.addWidget(self.eng_selector_combo)
        layout.addWidget(context_frame)

        # Actions: + New Engagement
        self.btn_new_audit = QPushButton("+ New Engagement")
        self.btn_new_audit.setObjectName("primaryBtn")
        self.btn_new_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_audit.setStyleSheet(
            "QPushButton { background-color: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }"
            "QPushButton:hover { background-color: #0369A1; }"
            "QPushButton:pressed { background-color: #075985; }"
        )
        self.btn_new_audit.clicked.connect(lambda: self.new_engagement_clicked.emit())
        layout.addWidget(self.btn_new_audit)

        # AI Copilot Toggle Button (⌘K)
        self.btn_copilot_toggle = QPushButton("✨ AI Copilot (⌘K)")
        self.btn_copilot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copilot_toggle.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }"
            "QPushButton:hover { background-color: #1E293B; color: #7DD3FC; border-color: #0284C7; }"
            "QPushButton:pressed { background-color: #0284C7; color: #FFFFFF; }"
        )
        self.btn_copilot_toggle.clicked.connect(lambda: self.copilot_toggled.emit())
        layout.addWidget(self.btn_copilot_toggle)
