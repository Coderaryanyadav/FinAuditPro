"""Workspace Sub-Navigation & Breadcrumb Context Bar for FinAuditPro shell."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class WorkspaceContextBar(QFrame):
    """Secondary workspace navigation bar rendering module tabs and location breadcrumbs."""

    sub_tab_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceContextBar")
        self.setFixedHeight(38)
        self.setStyleSheet(
            "QFrame#workspaceContextBar { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; }"
        )
        self.tab_buttons: dict[str, QPushButton] = {}
        self.btn_group = QButtonGroup(self)
        self._init_ui()

    def _init_ui(self) -> None:
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 0, 16, 0)
        self.main_layout.setSpacing(6)

        # Breadcrumb / Section Label
        self.lbl_breadcrumb = QLabel("WORKSPACE:")
        self.lbl_breadcrumb.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self.main_layout.addWidget(self.lbl_breadcrumb)

        # Container layout for tabs
        self.tabs_container = QWidget()
        self.tabs_layout = QHBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(4)
        self.main_layout.addWidget(self.tabs_container)

        self.main_layout.addStretch()

    def set_sub_tabs(self, tabs: list[tuple[str, str]], active_key: str = "") -> None:
        """Populates sub-tabs dynamically. `tabs` is a list of (route_key, display_title)."""
        # Clear existing tab buttons
        for btn in self.tab_buttons.values():
            self.btn_group.removeButton(btn)
            btn.deleteLater()
        self.tab_buttons.clear()

        # Remove old items from tabs_layout
        while self.tabs_layout.count() > 0:
            item = self.tabs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tabs:
            self.tabs_container.setVisible(False)
            return

        self.tabs_container.setVisible(True)
        for idx, (key, title) in enumerate(tabs):
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: 500; }"
                "QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }"
                "QPushButton:checked { background: #0284C7; color: #FFFFFF; border-color: #0284C7; font-weight: 600; }"
            )
            btn.clicked.connect(lambda _, k=key: self.sub_tab_selected.emit(k))
            self.tab_buttons[key] = btn
            self.btn_group.addButton(btn, idx)
            self.tabs_layout.addWidget(btn)

        # Select initial active tab
        if active_key in self.tab_buttons:
            self.tab_buttons[active_key].setChecked(True)
        elif tabs:
            self.tab_buttons[tabs[0][0]].setChecked(True)

    def set_breadcrumb(self, text: str) -> None:
        self.lbl_breadcrumb.setText(text.upper())
