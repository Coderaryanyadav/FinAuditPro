"""Navigation Sidebar component for FinAuditPro application shell."""


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.ui.theme import FinAuditLogoWidget

PRIMARY_NAV_ITEMS = [
    ("btn_dashboard", "Command Center", "Overview", "📊"),
    ("btn_inbox", "Inbox", "Requests & Queries", "📥"),
    ("btn_clients_hub", "Clients & Firms", "Practice Admin", "👥"),
    ("btn_work", "Work & Compliance", "Fieldwork Tools", "📋"),
    ("btn_audit", "Audit Engagement", "Active Audit", "📁"),
    ("btn_ai_assistant", "AI Assistant", "Copilot Lab", "✨"),
    ("btn_system", "System", "Settings & Archival", "⚙️"),
]


class NavigationSidebar(QFrame):
    """Primary navigation sidebar adhering to the CA Practice Information Architecture."""

    category_changed = Signal(int)
    toggle_collapsed = Signal(bool)
    profile_menu_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardSidebar")
        self.setFixedWidth(220)
        self.is_collapsed = False
        self.buttons: dict[str, QPushButton] = {}
        self.btn_group = QButtonGroup(self)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(4)

        # Logo / Brand Header Row
        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(4, 0, 4, 0)
        self.logo_box = FinAuditLogoWidget(size=28)
        self.logo_name = QLabel("FinAuditPro")
        self.logo_name.setObjectName("sidebarAppTitle")
        self.logo_name.setStyleSheet("font-weight: 700; font-size: 15px; color: #F1F5F9;")

        self.btn_collapse = QPushButton("◀")
        self.btn_collapse.setFixedSize(24, 24)
        self.btn_collapse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapse.setStyleSheet(
            "QPushButton { border: 1px solid #334155; border-radius: 4px; background: #1E293B; color: #94A3B8; font-size: 10px; font-weight: 600; }"
            "QPushButton:hover { background: #334155; color: #F8FAFC; }"
        )
        self.btn_collapse.clicked.connect(self.toggle_collapse_state)

        logo_row.addWidget(self.logo_box)
        logo_row.addWidget(self.logo_name)
        logo_row.addStretch()
        logo_row.addWidget(self.btn_collapse)
        layout.addLayout(logo_row)

        layout.addSpacing(10)

        # Primary Navigation Category Buttons
        for idx, (key, title, subtitle, icon) in enumerate(PRIMARY_NAV_ITEMS):
            btn = QPushButton(f"{icon}  {title}")
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{title} — {subtitle}")
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding: 8px 12px; font-size: 12px; font-weight: 500; border-radius: 6px; color: #94A3B8; background: transparent; border: none; }"
                "QPushButton:hover { background: #1E293B; color: #F8FAFC; }"
                "QPushButton:checked { background: #0284C7; color: #FFFFFF; font-weight: 600; }"
            )
            self.buttons[key] = btn
            self.btn_group.addButton(btn, idx)
            layout.addWidget(btn)

        self.buttons["btn_dashboard"].setChecked(True)
        self.btn_group.idClicked.connect(lambda cat_idx: self.category_changed.emit(cat_idx))

        layout.addStretch()

        # User Profile Frame at Bottom
        self.prof_frame = QFrame()
        self.prof_frame.setObjectName("sidebarProfileFrame")
        self.prof_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prof_frame.setStyleSheet(
            "QFrame#sidebarProfileFrame { background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 6px; }"
            "QFrame#sidebarProfileFrame:hover { background: #334155; }"
        )

        pf_layout = QHBoxLayout(self.prof_frame)
        pf_layout.setContentsMargins(4, 4, 4, 4)
        pf_layout.setSpacing(8)

        self.av_label = QLabel("CA")
        self.av_label.setObjectName("userAvatar")
        self.av_label.setFixedSize(28, 28)
        self.av_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.av_label.setStyleSheet(
            "QLabel#userAvatar { background: #0284C7; color: #FFFFFF; font-weight: 700; font-size: 11px; border-radius: 14px; }"
        )

        u_info = QVBoxLayout()
        u_info.setSpacing(1)
        self.lbl_user_name = QLabel("Partner")
        self.lbl_user_name.setObjectName("userName")
        self.lbl_user_name.setStyleSheet("color: #F8FAFC; font-weight: 600; font-size: 12px;")

        self.lbl_user_role = QLabel("Chartered Accountant")
        self.lbl_user_role.setObjectName("userRole")
        self.lbl_user_role.setStyleSheet("color: #94A3B8; font-size: 10px;")

        u_info.addWidget(self.lbl_user_name)
        u_info.addWidget(self.lbl_user_role)

        self.btn_more = QPushButton("•••")
        self.btn_more.setFixedSize(22, 22)
        self.btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_more.setStyleSheet(
            "QPushButton { border: none; background: transparent; color: #94A3B8; font-weight: 700; font-size: 12px; }"
            "QPushButton:hover { color: #F8FAFC; }"
        )
        self.btn_more.clicked.connect(lambda: self.profile_menu_requested.emit())

        pf_layout.addWidget(self.av_label)
        pf_layout.addLayout(u_info)
        pf_layout.addStretch()
        pf_layout.addWidget(self.btn_more)

        layout.addWidget(self.prof_frame)

    def toggle_collapse_state(self) -> None:
        self.is_collapsed = not self.is_collapsed
        self.setFixedWidth(60 if self.is_collapsed else 220)
        self.logo_name.setVisible(not self.is_collapsed)
        self.btn_collapse.setText("▶" if self.is_collapsed else "◀")

        for key, title, _, icon in PRIMARY_NAV_ITEMS:
            btn = self.buttons[key]
            btn.setText(icon if self.is_collapsed else f"{icon}  {title}")

        self.lbl_user_name.setVisible(not self.is_collapsed)
        self.lbl_user_role.setVisible(not self.is_collapsed)
        self.btn_more.setVisible(not self.is_collapsed)
        self.toggle_collapsed.emit(self.is_collapsed)

    def set_user_info(self, name: str, role: str) -> None:
        self.lbl_user_name.setText(name)
        self.lbl_user_role.setText(role)
        initials = "".join([part[0].upper() for part in name.split() if part])[:2] or "CA"
        self.av_label.setText(initials)

    def set_active_category_by_index(self, index: int) -> None:
        if 0 <= index < len(PRIMARY_NAV_ITEMS):
            key = PRIMARY_NAV_ITEMS[index][0]
            if key in self.buttons:
                self.buttons[key].setChecked(True)
