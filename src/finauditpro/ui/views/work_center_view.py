"""PySide6 Work Center view unifying Tasks, Compliance, Reconciliations, Requests, Review Notes, and Audit Actions."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos_work import WorkCenterFilterDTO, WorkItemDTO
from finauditpro.application.services.work_center_service import WorkCenterService
from finauditpro.ui.views.dashboard_view import MetricCard


class WorkCenterView(QWidget):
    """Central CA Practice Work Center displaying work items with filters and quick actions."""

    task_selected = Signal(str)
    source_opened = Signal(dict)

    def __init__(
        self,
        work_center_service: WorkCenterService,
        clients: list[dict] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.service = work_center_service
        self.clients = clients or []
        self.current_section = "Tasks"
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header Title & New Task Button
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("PRACTICE WORK CENTER")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        sub_lbl = QLabel("Unified execution hub for Tasks, Compliance, Reconciliations, Requests, and Audit Actions")
        sub_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        btn_new_task = QPushButton("+ Create Task")
        btn_new_task.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn_new_task.clicked.connect(self._on_create_task_dialog)
        header_layout.addWidget(btn_new_task)
        layout.addLayout(header_layout)

        # Metric Summary Bar
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)
        self.card_total = MetricCard("TOTAL TASKS", "0", "Practice wide tasks", accent_color="#2563EB")
        self.card_pending_cli = MetricCard("WAITING CLIENT", "0", "PBC & document requests", accent_color="#D97706")
        self.card_pending_rev = MetricCard("WAITING REVIEW", "0", "Review notes & workpapers", accent_color="#7C3AED")
        self.card_ai_suggestions = MetricCard("AI SUGGESTIONS", "0", "Requires human confirmation", accent_color="#DC2626")

        metrics_layout.addWidget(self.card_total)
        metrics_layout.addWidget(self.card_pending_cli)
        metrics_layout.addWidget(self.card_pending_rev)
        metrics_layout.addWidget(self.card_ai_suggestions)
        layout.addLayout(metrics_layout)

        # Section Tabs Navigation
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(8)
        self.section_buttons: dict[str, QPushButton] = {}
        sections = ["Tasks", "Compliance", "Reconciliations", "Client Requests", "Review Notes", "Audit Actions"]
        for sec in sections:
            btn = QPushButton(sec)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, s=sec: self._select_section(s))
            tabs_layout.addWidget(btn)
            self.section_buttons[sec] = btn
        tabs_layout.addStretch()
        layout.addLayout(tabs_layout)

        # Filters Bar
        filter_box = QFrame()
        filter_box.setStyleSheet("QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px; }")
        filter_layout = QHBoxLayout(filter_box)
        filter_layout.setContentsMargins(10, 6, 10, 6)

        self.cmb_client = QComboBox()
        self.cmb_client.addItem("All Clients", None)
        for c in self.clients:
            self.cmb_client.addItem(c.get("name", "Client"), c.get("id"))
        self.cmb_client.currentIndexChanged.connect(self.refresh_data)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["All States", "TODO", "IN_PROGRESS", "WAITING_CLIENT", "WAITING_REVIEW", "COMPLETED", "CANCELLED"])
        self.cmb_status.currentIndexChanged.connect(self.refresh_data)

        self.cmb_priority = QComboBox()
        self.cmb_priority.addItems(["All Priorities", "URGENT", "HIGH", "MEDIUM", "LOW"])
        self.cmb_priority.currentIndexChanged.connect(self.refresh_data)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search title, assignee, or keyword...")
        self.txt_search.textChanged.connect(self.refresh_data)

        filter_layout.addWidget(QLabel("Client:"))
        filter_layout.addWidget(self.cmb_client)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.cmb_status)
        filter_layout.addWidget(QLabel("Priority:"))
        filter_layout.addWidget(self.cmb_priority)
        filter_layout.addWidget(self.txt_search)
        layout.addWidget(filter_box)

        # Compact Work Items Table
        self.table = QTableWidget()
        headers = ["CONFIRM", "TITLE & DESCRIPTION", "CLIENT & FY", "ASSIGNEE", "STATUS", "PRIORITY", "DUE DATE", "SOURCE", "QUICK ACTIONS"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background: white; gridline-color: #E2E8F0; font-size: 12px; }
            QHeaderView::section { background: #F1F5F9; font-weight: bold; color: #475569; padding: 6px; border: none; }
        """)
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)
        layout.addWidget(self.table)

        self._select_section("Tasks")

    def _select_section(self, section: str) -> None:
        self.current_section = section
        for s, btn in self.section_buttons.items():
            if s == section:
                btn.setChecked(True)
                btn.setStyleSheet("background: #0F172A; color: white; font-weight: bold; border-radius: 6px; padding: 6px 14px;")
            else:
                btn.setChecked(False)
                btn.setStyleSheet("background: #E2E8F0; color: #334155; border-radius: 6px; padding: 6px 14px;")
        self.refresh_data()

    def refresh_data(self) -> None:
        client_id = self.cmb_client.currentData()
        status = self.cmb_status.currentText()
        if status == "All States":
            status = None
        priority = self.cmb_priority.currentText()
        if priority == "All Priorities":
            priority = None
        search = self.txt_search.text().strip() or None

        filters = WorkCenterFilterDTO(
            section=self.current_section,
            client_id=client_id,
            status=status,
            priority=priority,
            search_query=search,
        )

        summary = self.service.get_summary(client_id=client_id)
        self.card_total.set_value(str(summary.total_tasks))
        self.card_pending_cli.set_value(str(summary.waiting_client_count))
        self.card_pending_rev.set_value(str(summary.waiting_review_count))
        self.card_ai_suggestions.set_value(str(summary.ai_suggestions_pending_confirmation))

        items = self.service.get_work_items(filters)
        self._populate_table(items)

    def _populate_table(self, items: list[WorkItemDTO]) -> None:
        self.table.setRowCount(0)
        for i, item in enumerate(items):
            self.table.insertRow(i)

            # Confirm status for AI
            if item.requires_human_confirmation or not item.is_confirmed:
                confirm_item = QTableWidgetItem("⚠️ AI PENDING")
                confirm_item.setForeground(QColor("#DC2626"))
                confirm_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                confirm_item = QTableWidgetItem("✓ CONFIRMED")
                confirm_item.setForeground(QColor("#16A34A"))

            title_item = QTableWidgetItem(f"{item.title}\n{item.description}")
            client_item = QTableWidgetItem(f"{item.client_name}\n{item.financial_year}")
            assignee_item = QTableWidgetItem(item.assignee)

            status_item = QTableWidgetItem(item.status)
            if item.status == "COMPLETED":
                status_item.setForeground(QColor("#16A34A"))
            elif item.status in ("WAITING_CLIENT", "WAITING_REVIEW"):
                status_item.setForeground(QColor("#D97706"))

            priority_item = QTableWidgetItem(item.priority)
            if item.priority in ("URGENT", "HIGH"):
                priority_item.setForeground(QColor("#DC2626"))

            due_item = QTableWidgetItem(item.due_at or "N/A")
            source_item = QTableWidgetItem(item.source)

            self.table.setItem(i, 0, confirm_item)
            self.table.setItem(i, 1, title_item)
            self.table.setItem(i, 2, client_item)
            self.table.setItem(i, 3, assignee_item)
            self.table.setItem(i, 4, status_item)
            self.table.setItem(i, 5, priority_item)
            self.table.setItem(i, 6, due_item)
            self.table.setItem(i, 7, source_item)

            # Quick Action widget
            action_widget = QWidget()
            act_layout = QHBoxLayout(action_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_complete = QPushButton("✓ Complete")
            btn_complete.setStyleSheet("font-size: 10px; padding: 2px 6px; background: #DCFCE7; color: #166534;")
            btn_complete.clicked.connect(lambda _, item_id=item.id: self._on_complete_task(item_id))
            act_layout.addWidget(btn_complete)

            if item.requires_human_confirmation or not item.is_confirmed:
                btn_confirm = QPushButton("👍 Confirm AI")
                btn_confirm.setStyleSheet("font-size: 10px; padding: 2px 6px; background: #FEF08A; color: #854D0E; font-weight: bold;")
                btn_confirm.clicked.connect(lambda _, item_id=item.id: self._on_confirm_ai_task(item_id))
                act_layout.addWidget(btn_confirm)

            btn_source = QPushButton("🔗 Source")
            btn_source.setStyleSheet("font-size: 10px; padding: 2px 6px; background: #E0F2FE; color: #075985;")
            btn_source.clicked.connect(lambda _, item_id=item.id: self._on_open_source(item_id))
            act_layout.addWidget(btn_source)

            self.table.setCellWidget(i, 8, action_widget)
            self.table.setRowHeight(i, 50)

    def _on_create_task_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Work Task")
        dialog.setMinimumWidth(400)
        layout = QFormLayout(dialog)

        txt_title = QLineEdit()
        txt_desc = QTextEdit()
        txt_desc.setMaximumHeight(80)

        cmb_cli = QComboBox()
        cmb_cli.addItem("General Practice", None)
        for c in self.clients:
            cmb_cli.addItem(c.get("name", "Client"), c.get("id"))

        txt_assignee = QLineEdit()
        txt_assignee.setText("Audit Team")

        cmb_pri = QComboBox()
        cmb_pri.addItems(["MEDIUM", "HIGH", "URGENT", "LOW"])

        txt_due = QLineEdit()
        txt_due.setPlaceholderText("YYYY-MM-DD")

        layout.addRow("Title:", txt_title)
        layout.addRow("Description:", txt_desc)
        layout.addRow("Client:", cmb_cli)
        layout.addRow("Assignee:", txt_assignee)
        layout.addRow("Priority:", cmb_pri)
        layout.addRow("Due Date:", txt_due)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = txt_title.text().strip()
            if not title:
                QMessageBox.warning(self, "Validation Error", "Task title is required.")
                return
            self.service.create_task(
                title=title,
                description=txt_desc.toPlainText().strip(),
                client_id=cmb_cli.currentData(),
                assignee=txt_assignee.text().strip() or "Unassigned",
                priority=cmb_pri.currentText(),
                due_at=txt_due.text().strip() or "N/A",
                source="MANUAL",
            )
            self.refresh_data()

    def _on_complete_task(self, item_id: str) -> None:
        self.service.update_task_status(item_id, "COMPLETED")
        self.refresh_data()

    def _on_confirm_ai_task(self, item_id: str) -> None:
        self.service.confirm_ai_suggestion(item_id)
        self.refresh_data()

    def _on_open_source(self, item_id: str) -> None:
        info = self.service.get_open_source_info(item_id)
        self.source_opened.emit(info)
        QMessageBox.information(self, "Open Source Entity", f"Opening Source Item:\nID: {info.get('id')}\nType: {info.get('type')}\nTitle: {info.get('title')}")

    def _on_table_double_clicked(self, row: int, col: int) -> None:
        cell = self.table.item(row, 1)
        if cell:
            self.task_selected.emit(cell.text())
