"""
FinAuditPro V2 — Raycast/Linear Style Command Palette (⌘K)
Keyboard-driven overlay for instant navigation, search, actions, and settings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QFont
from .theme import ThemeManager


class CommandItemWidget(QWidget):
    """Clean command row with category, label, and keyboard shortcut badge."""

    def __init__(self, title: str, category: str, shortcut: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Category tag
        cat_lbl = QLabel(category.upper())
        cat_lbl.setStyleSheet("""
            font-size: 9px; font-weight: 700; color: #6B7280;
            background: #F1F3F5; padding: 2px 6px; border-radius: 4px; border: none;
        """)

        # Command title
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(620)

        # Main container with rounded border & shadow
        container = QFrame(self)
        container.setObjectName("commandPaletteContainer")
        container.setStyleSheet("""
            QFrame#commandPaletteContainer {
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

        # Top search bar
        search_box = QHBoxLayout()
        search_icon = QLabel("🔍")
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
        self.list_widget.setFixedHeight(300)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none; background: transparent; outline: none;
            }
            QListWidget::item {
                border-radius: 6px; padding: 0px; margin-bottom: 2px;
            }
            QListWidget::item:selected {
                background-color: #EFF6FF;
            }
            QListWidget::item:hover {
                background-color: #F7F8FA;
            }
        """)
        self.list_widget.itemActivated.connect(self._on_item_activated)
        c_layout.addWidget(self.list_widget)

        self._all_commands = []
        self._register_default_commands()
        self._populate_list(self._all_commands)

    def _register_default_commands(self):
        self._all_commands = [
            # Navigation
            {"title": "Go to Dashboard Overview", "category": "Navigation", "shortcut": "Alt+1", "key": "nav", "payload": 0},
            {"title": "Go to Client Management", "category": "Navigation", "shortcut": "Alt+2", "key": "nav", "payload": 1},
            {"title": "Go to Document Upload & OCR", "category": "Navigation", "shortcut": "Alt+3", "key": "nav", "payload": 2},
            {"title": "Go to AI Audit Analysis Copilot", "category": "Navigation", "shortcut": "Alt+4", "key": "nav", "payload": 3},
            {"title": "Go to Audit Findings Workspace", "category": "Navigation", "shortcut": "Alt+5", "key": "nav", "payload": 4},
            {"title": "Go to Financial Statements", "category": "Navigation", "shortcut": "Alt+6", "key": "nav", "payload": 5},
            {"title": "Go to GST Verification & 2B Match", "category": "Navigation", "shortcut": "Alt+7", "key": "nav", "payload": 6},
            {"title": "Go to Compliance Matrix (CARO 2020)", "category": "Navigation", "shortcut": "Alt+8", "key": "nav", "payload": 7},
            {"title": "Go to Risk Analysis Matrix", "category": "Navigation", "shortcut": "Alt+9", "key": "nav", "payload": 8},
            {"title": "Go to SA 230 Working Papers", "category": "Navigation", "shortcut": "", "key": "nav", "payload": 9},
            {"title": "Go to Independent Audit Reports", "category": "Navigation", "shortcut": "", "key": "nav", "payload": 10},
            {"title": "Go to Audit History & Activity Log", "category": "Navigation", "shortcut": "", "key": "nav", "payload": 11},
            {"title": "Go to System Settings & CA Profile", "category": "Navigation", "shortcut": "Ctrl+,", "key": "nav", "payload": 12},

            # Actions
            {"title": "Create New Audit Project", "category": "Action", "shortcut": "", "key": "action", "payload": "new_audit"},
            {"title": "Toggle Dark / Light Theme Mode", "category": "Settings", "shortcut": "", "key": "action", "payload": "toggle_theme"},
            {"title": "Export Database Backup", "category": "Database", "shortcut": "", "key": "action", "payload": "export_db"},
            {"title": "Test Local Ollama AI Engine Pings", "category": "AI Engine", "shortcut": "", "key": "action", "payload": "test_ollama"},
            {"title": "Refresh Realtime Audit Metrics", "category": "Action", "shortcut": "F5", "key": "action", "payload": "refresh"},
        ]

    def _populate_list(self, commands: list):
        self.list_widget.clear()
        for cmd in commands:
            item = QListWidgetItem()
            widget = CommandItemWidget(cmd["title"], cmd["category"], cmd["shortcut"])
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_text_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            filtered = self._all_commands
        else:
            filtered = [
                c for c in self._all_commands
                if query in c["title"].lower() or query in c["category"].lower()
            ]
        self._populate_list(filtered)

    def _on_item_activated(self, item: QListWidgetItem):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd:
            self.action_triggered.emit(cmd["key"], cmd["payload"])
            self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            curr = self.list_widget.currentRow()
            if curr < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr + 1)
        elif event.key() == Qt.Key.Key_Up:
            curr = self.list_widget.currentRow()
            if curr > 0:
                self.list_widget.setCurrentRow(curr - 1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr_item = self.list_widget.currentItem()
            if curr_item:
                self._on_item_activated(curr_item)
        else:
            super().keyPressEvent(event)
