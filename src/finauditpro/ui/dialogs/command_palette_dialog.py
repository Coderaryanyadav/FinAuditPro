"""
FinAuditPro Enterprise — Command Palette & Unified Search (⌘P / ⌘K)
Modal dialog providing instant multi-entity search, FTS text matching, and workspace navigation.
"""

from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
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

from finauditpro.application.services.unified_search_service import UnifiedSearchService
from finauditpro.domain.unified_search_engine import SearchResultDTO, SearchScopeContext


class SearchResultWidget(QWidget):
    """Custom list row widget for unified search results showing title, subtitle, and context badge."""

    def __init__(self, title: str, subtitle: str, category: str, context_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        top_l = QHBoxLayout()
        cat_lbl = QLabel(category.upper())
        cat_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #1D4ED8; background: #DBEAFE; padding: 2px 6px; border-radius: 4px; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A; border: none;")
        top_l.addWidget(cat_lbl)
        top_l.addWidget(title_lbl, 1)

        ctx_lbl = QLabel(context_text)
        ctx_lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #475569; border: none;")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 10px; color: #94A3B8; border: none;")

        layout.addLayout(top_l)
        layout.addWidget(ctx_lbl)
        if subtitle.strip():
            layout.addWidget(sub_lbl)


class GroupHeaderWidget(QWidget):
    """Visual section divider header for search result categories."""

    def __init__(self, group_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 4)
        lbl = QLabel(f"─── {group_name.upper()} ───")
        lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; border: none; background: transparent;")
        layout.addWidget(lbl)


class CommandPaletteDialog(QDialog):
    """Raycast / Linear style modal overlay for Command Palette & Unified Search (⌘P / ⌘K)."""

    action_triggered = Signal(str, object)  # (route_key, payload)

    def __init__(
        self,
        parent: QWidget | None = None,
        db_manager: Any = None,
        scope: SearchScopeContext | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(660)

        self.db_manager = db_manager
        self.search_service = UnifiedSearchService(db_manager) if db_manager else None
        self.search_scope = scope or SearchScopeContext()

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._execute_search)

        container = QFrame(self)
        container.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; }")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(14, 14, 14, 14)
        c_layout.setSpacing(8)

        search_box = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search clients, documents, workpapers, tasks, findings, GL... (⌘P / ⌘K)")
        self.input_field.setStyleSheet("QLineEdit { border: none; background: transparent; font-size: 14px; font-weight: 500; color: #0F172A; padding: 6px 4px; }")
        self.input_field.textChanged.connect(self._on_search_text_changed)

        esc_hint = QLabel("ESC to close")
        esc_hint.setStyleSheet("font-size: 10px; font-weight: 600; color: #94A3B8; border: 1px solid #E2E8F0; border-radius: 4px; padding: 2px 6px;")

        search_box.addWidget(self.input_field, 1)
        search_box.addWidget(esc_hint)
        c_layout.addLayout(search_box)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #E2E8F0; border: none;")
        c_layout.addWidget(div)

        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(340)
        self.list_widget.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; }
            QListWidget::item { border-radius: 6px; padding: 0px; margin-bottom: 2px; }
            QListWidget::item:selected { background-color: #EFF6FF; }
        """)
        self.list_widget.itemActivated.connect(self._on_item_activated)
        self.list_widget.itemClicked.connect(self._on_item_activated)
        self.input_field.returnPressed.connect(self._on_enter_pressed)
        c_layout.addWidget(self.list_widget)

        self._default_nav_items = [
            {"title": "Command Center / Operational Overview", "category": "Pipeline", "route": "dashboard", "payload": 0},
            {"title": "Intake & PBC Practice Inbox", "category": "Pipeline", "route": "inbox", "payload": 1},
            {"title": "Planning & SA 320 Materiality Matrix", "category": "Pipeline", "route": "audit_matrix", "payload": 2},
            {"title": "TB / GL Financial Datasets", "category": "Pipeline", "route": "financial_data", "payload": 3},
            {"title": "Schedule III Working Papers Workspace", "category": "Pipeline", "route": "working_paper", "payload": 4},
            {"title": "Statutory Audit Reports & Finalization", "category": "Pipeline", "route": "audit_report", "payload": 5},
            {"title": "Unified Work Center (Tasks & Findings)", "category": "Fieldwork", "route": "work_center", "payload": 6},
            {"title": "Document Vault & Intelligence", "category": "Fieldwork", "route": "documents", "payload": 7},
            {"title": "Unified Reconciliation Center", "category": "Fieldwork", "route": "unified_reconciliation", "payload": 8},
            {"title": "Statutory Compliance Workflow Matrix", "category": "Fieldwork", "route": "compliance", "payload": 9},
            {"title": "Audit Clients Workspace Directory", "category": "Admin", "route": "clients", "payload": 11},
            {"title": "Engagement Manager", "category": "Admin", "route": "engagements", "payload": 12},
        ]
        self._populate_default_commands()

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Down:
            curr = self.list_widget.currentRow()
            if curr < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr + 1)
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Up:
            curr = self.list_widget.currentRow()
            if curr > 0:
                self.list_widget.setCurrentRow(curr - 1)
            event.accept()
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_enter_pressed()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_enter_pressed(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self._on_item_activated(item)

    def _populate_default_commands(self) -> None:
        self.list_widget.clear()
        for cmd in self._default_nav_items:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, {"route": cmd["route"], "payload": cmd["payload"], "is_header": False})
            w = SearchResultWidget(cmd["title"], "Quick Navigation Shortcut", cmd["category"], f"System | Navigation | {cmd['category']}")
            item.setSizeHint(w.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_text_changed(self, text: str) -> None:
        if not text.strip():
            self._debounce_timer.stop()
            self._populate_default_commands()
            return
        self._debounce_timer.start()

    def _execute_search(self) -> None:
        query = self.input_field.text().strip()
        if not query:
            self._populate_default_commands()
            return

        if not self.search_service:
            # Filter default commands locally if search service not injected
            filtered = [c for c in self._default_nav_items if query.lower() in c["title"].lower() or query.lower() in c["category"].lower()]
            self.list_widget.clear()
            for cmd in filtered:
                item = QListWidgetItem(self.list_widget)
                item.setData(Qt.ItemDataRole.UserRole, {"route": cmd["route"], "payload": cmd["payload"], "is_header": False})
                w = SearchResultWidget(cmd["title"], "Quick Navigation", cmd["category"], f"System | Navigation | {cmd['category']}")
                item.setSizeHint(w.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, w)
            if self.list_widget.count() > 0:
                self.list_widget.setCurrentRow(0)
            return

        # Execute unified search across all entity categories
        results: list[SearchResultDTO] = self.search_service.search(query, scope=self.search_scope)
        self.list_widget.clear()

        if not results:
            item = QListWidgetItem(self.list_widget)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            w = QLabel(f"No search results found for '{query}'.")
            w.setStyleSheet("color: #64748B; font-size: 12px; padding: 12px; background: transparent;")
            item.setSizeHint(w.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
            return

        # Group search results by result category
        grouped: dict[str, list[SearchResultDTO]] = {}
        for r in results:
            grp_name = r.group.value
            grouped.setdefault(grp_name, []).append(r)

        for grp_name, items_list in grouped.items():
            # Add section header
            h_item = QListWidgetItem(self.list_widget)
            h_item.setFlags(Qt.ItemFlag.NoItemFlags)
            h_widget = GroupHeaderWidget(grp_name)
            h_item.setSizeHint(h_widget.sizeHint())
            self.list_widget.addItem(h_item)
            self.list_widget.setItemWidget(h_item, h_widget)

            # Add result rows
            for res_dto in items_list:
                row_item = QListWidgetItem(self.list_widget)
                row_item.setData(Qt.ItemDataRole.UserRole, {
                    "route": res_dto.route_key,
                    "payload": res_dto.payload,
                    "is_header": False,
                    "dto": res_dto
                })
                row_w = SearchResultWidget(
                    title=res_dto.title,
                    subtitle=res_dto.subtitle,
                    category=res_dto.entity_type,
                    context_text=res_dto.context_text
                )
                row_item.setSizeHint(row_w.sizeHint())
                self.list_widget.addItem(row_item)
                self.list_widget.setItemWidget(row_item, row_w)

        if self.list_widget.count() > 0:
            for idx in range(self.list_widget.count()):
                it = self.list_widget.item(idx)
                d = it.data(Qt.ItemDataRole.UserRole)
                if d and not d.get("is_header"):
                    self.list_widget.setCurrentRow(idx)
                    break

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and not data.get("is_header"):
            route = data.get("route", "dashboard")
            payload = data.get("payload")
            self.action_triggered.emit(route, payload)
            self.accept()
