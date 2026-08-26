"""
FinAuditPro Enterprise — Command Palette Overlay (⌘K)
Keyboard-driven modal dialog for instant navigation, search, and audit actions.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CommandItemWidget(QWidget):
    """Clean command row with category, label, and keyboard shortcut badge."""

    def __init__(
        self, title: str, category: str, shortcut: str | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        cat_lbl = QLabel(category.upper())
        cat_lbl.setStyleSheet("""
            font-size: 9px; font-weight: 700; color: #6B7280;
            background: #F1F3F5; padding: 2px 6px; border-radius: 4px; border: none;
        """)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #111827; border: none;")

        layout.addWidget(cat_lbl)
        layout.addWidget(title_lbl, 1)

        if shortcut:
            sc_lbl = QLabel(shortcut)
            sc_lbl.setStyleSheet("""
                font-size: 10px; font-weight: 600; color: #9CA3AF;
                border: 1px solid #E5E7EB; background: #FFFFFF;
                border-radius: 4px; padding: 1px 5px;
            """)
            layout.addWidget(sc_lbl)


class CommandPaletteDialog(QDialog):
    """Raycast / Linear style modal overlay command palette (⌘K)."""

    action_triggered = Signal(str, object)  # (action_key, action_payload)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(620)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(8)

        # Search bar
        search_box = QHBoxLayout()
        search_icon = QLabel("")
        search_icon.setStyleSheet("font-size: 14px; border: none; background: transparent;")

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or search workspace... (⌘K)")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none; background: transparent;
                font-size: 14px; font-weight: 500; color: #111827;
                padding: 6px 4px;
            }
        """)
        self.input_field.textChanged.connect(self._on_search_text_changed)

        esc_hint = QLabel("ESC to close")
        esc_hint.setStyleSheet("""
            font-size: 10px; font-weight: 600; color: #9CA3AF;
            border: 1px solid #E5E7EB; border-radius: 4px; padding: 2px 6px;
        """)

        search_box.addWidget(search_icon)
        search_box.addWidget(self.input_field, 1)
        search_box.addWidget(esc_hint)
        c_layout.addLayout(search_box)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #E5E7EB; border: none;")
        c_layout.addWidget(div)

        # Command list
        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(280)
        self.list_widget.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; }
            QListWidget::item { border-radius: 6px; padding: 0px; margin-bottom: 2px; }
            QListWidget::item:selected { background-color: #EFF6FF; }
        """)
        self.list_widget.itemActivated.connect(self._on_item_activated)
        c_layout.addWidget(self.list_widget)

        self._all_commands: list[dict[str, Any]] = []
        self._register_default_commands()

        self._populate_list(self._all_commands)

    def _register_default_commands(self) -> None:
        self._all_commands = [
            {
                "title": "Go to Dashboard Overview",
                "category": "Navigation",
                "shortcut": "Alt+1",
                "key": "nav",
                "payload": 0,
            },
            {
                "title": "Go to Audit Firms Management",
                "category": "Navigation",
                "shortcut": "Alt+2",
                "key": "nav",
                "payload": 1,
            },
            {
                "title": "Go to Client Management",
                "category": "Navigation",
                "shortcut": "Alt+3",
                "key": "nav",
                "payload": 2,
            },
            {
                "title": "Go to Engagement Manager",
                "category": "Navigation",
                "shortcut": "Alt+4",
                "key": "nav",
                "payload": 3,
            },
            {
                "title": "Go to Document Intelligence Vault",
                "category": "Navigation",
                "shortcut": "Alt+5",
                "key": "nav",
                "payload": 4,
            },
            {
                "title": "Go to Financial Statements",
                "category": "Navigation",
                "shortcut": "Alt+6",
                "key": "nav",
                "payload": 5,
            },
            {
                "title": "Go to GST Reconciliation & 2B Match",
                "category": "Navigation",
                "shortcut": "Alt+7",
                "key": "nav",
                "payload": 6,
            },
            {
                "title": "Go to Statutory Compliance Matrix",
                "category": "Navigation",
                "shortcut": "Alt+8",
                "key": "nav",
                "payload": 7,
            },
            {
                "title": "Go to AI Audit Analysis Copilot",
                "category": "Navigation",
                "shortcut": "Alt+9",
                "key": "nav",
                "payload": 9,
            },
            {
                "title": "Go to SA 230 Working Papers",
                "category": "Navigation",
                "shortcut": "",
                "key": "nav",
                "payload": 10,
            },
            {
                "title": "Go to Independent Audit Reports",
                "category": "Navigation",
                "shortcut": "",
                "key": "nav",
                "payload": 11,
            },
            {
                "title": "Go to System Settings & CA Profile",
                "category": "Navigation",
                "shortcut": "Ctrl+,",
                "key": "nav",
                "payload": 14,
            },
        ]

    def _populate_list(self, commands: list[dict[str, Any]]) -> None:
        self.list_widget.clear()

        for cmd in commands:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            widget = CommandItemWidget(cmd["title"], cmd["category"], cmd.get("shortcut"))
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_text_changed(self, text: str) -> None:
        if not text.strip():
            self._populate_list(self._all_commands)
            return

        query = text.lower().strip()
        filtered = [
            c
            for c in self._all_commands
            if query in c["title"].lower() or query in c["category"].lower()
        ]
        self._populate_list(filtered)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.action_triggered.emit(data["key"], data["payload"])
            self.accept()
