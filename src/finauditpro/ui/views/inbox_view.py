"""Practice Inbox View for FinAuditPro Enterprise Shell.

Unified intake view for uploaded documents, client PBC requests, received evidence,
and AI classification approval.
"""


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos_inbox import InboxFilterDTO
from finauditpro.application.services.inbox_service import InboxService
from finauditpro.ui.theme import EmptyStateWidget


class CategoryOverrideDialog(QDialog):
    """Modal dialog allowing human auditors to review and override AI document categories."""

    def __init__(self, current_category: str, confidence_score: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Human Approval — Review & Override Classification")
        self.setFixedSize(420, 240)
        self.selected_category = current_category

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_lbl = QLabel("AI Classification Advisory Review")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title_lbl)

        info_lbl = QLabel(f"Detected Category: {current_category}\nAI Confidence Score: {int(confidence_score * 100)}%")
        info_lbl.setStyleSheet("font-size: 12px; color: #475569; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px;")
        layout.addWidget(info_lbl)

        lbl_select = QLabel("Select Verified Category:")
        lbl_select.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
        layout.addWidget(lbl_select)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems([
            "Bank Statement",
            "General Ledger Extract",
            "Trial Balance",
            "Vendor Invoice",
            "Purchase Order",
            "Tax Return / Form 26AS / GSTR",
            "Board Minutes / Secretarial",
            "Fixed Asset Register",
            "Payroll Summary",
            "Legal & Statutory Document",
            "General Evidence",
        ])
        if current_category in [self.cat_combo.itemText(i) for i in range(self.cat_combo.count())]:
            self.cat_combo.setCurrentText(current_category)

        layout.addWidget(self.cat_combo)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_confirm = QPushButton("Confirm & Accept")
        btn_confirm.setStyleSheet(
            "QPushButton { background: #0284C7; color: #FFFFFF; font-weight: 600; border-radius: 4px; padding: 6px 14px; border: none; }"
            "QPushButton:hover { background: #0369A1; }"
        )
        btn_confirm.clicked.connect(self._on_confirm)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_confirm)
        layout.addLayout(btn_box)

    def _on_confirm(self) -> None:
        self.selected_category = self.cat_combo.currentText()
        self.accept()


class InboxView(QWidget):
    """Unified Practice Inbox View."""

    open_document_requested = Signal(str)
    open_pbc_requested = Signal(str)
    navigate_to_route = Signal(str)

    def __init__(self, inbox_service: InboxService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.inbox_service = inbox_service
        self.current_tab = "ALL"
        self.current_client_id: str | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #F8FAFC; border: none;")

        body = QWidget()
        body.setStyleSheet("background-color: #F8FAFC;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 16, 24, 24)
        body_layout.setSpacing(14)

        # Header Title
        hdr_frame = QFrame()
        hdr_l = QHBoxLayout(hdr_frame)
        hdr_l.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(2)
        title_lbl = QLabel("Practice Inbox")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        sub_title = QLabel("Unified intake pipeline for incoming documents, client requests, and AI classifications.")
        sub_title.setStyleSheet("font-size: 12px; color: #64748B;")

        left_v.addWidget(title_lbl)
        left_v.addWidget(sub_title)
        hdr_l.addLayout(left_v)
        hdr_l.addStretch()

        btn_refresh = QPushButton("🔄 Refresh Inbox")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #334155; font-weight: 600; font-size: 12px; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; }"
            "QPushButton:hover { background: #EFF6FF; color: #2563EB; }"
        )
        btn_refresh.clicked.connect(self.refresh)
        hdr_l.addWidget(btn_refresh)

        body_layout.addWidget(hdr_frame)

        # Filter Tabs Row: [All] [Needs Review] [Documents] [Requests] [AI Suggestions]
        tabs_frame = QFrame()
        tabs_l = QHBoxLayout(tabs_frame)
        tabs_l.setContentsMargins(0, 0, 0, 0)
        tabs_l.setSpacing(6)

        self.tab_buttons: dict[str, QPushButton] = {}
        self.tab_group = QButtonGroup(self)

        tab_defs = [
            ("ALL", "All Inbox Items"),
            ("NEEDS_REVIEW", "Needs Review ⚠️"),
            ("DOCUMENTS", "Evidence Documents 📄"),
            ("REQUESTS", "Client PBC Requests 📋"),
            ("AI_SUGGESTIONS", "AI Suggestions ✨"),
        ]

        for idx, (tab_key, label_text) in enumerate(tab_defs):
            btn = QPushButton(label_text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 14px; font-weight: 500; font-size: 12px; }"
                "QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }"
                "QPushButton:checked { background: #0284C7; color: #FFFFFF; border-color: #0284C7; font-weight: 600; }"
            )
            btn.clicked.connect(lambda _, k=tab_key: self._on_tab_changed(k))
            self.tab_buttons[tab_key] = btn
            self.tab_group.addButton(btn, idx)
            tabs_l.addWidget(btn)

        self.tab_buttons["ALL"].setChecked(True)
        tabs_l.addStretch()

        # Quick Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter intake items...")
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(
            "QLineEdit { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px 10px; font-size: 12px; }"
        )
        self.search_input.textChanged.connect(lambda: self.refresh())
        tabs_l.addWidget(self.search_input)

        body_layout.addWidget(tabs_frame)

        # High-Density Inbox Table
        self.table_inbox = QTableWidget()
        self.table_inbox.setColumnCount(6)
        self.table_inbox.setHorizontalHeaderLabels(
            ["CLIENT / ENGAGEMENT", "DOCUMENT / ITEM", "RECEIVED", "DETECTED TYPE & CONFIDENCE", "STATUS", "ACTIONS"]
        )
        self.table_inbox.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_inbox.setColumnWidth(0, 180)
        self.table_inbox.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col_i, col_w in enumerate([140, 220, 110, 160], start=2):
            self.table_inbox.horizontalHeader().setSectionResizeMode(col_i, QHeaderView.ResizeMode.Fixed)
            self.table_inbox.setColumnWidth(col_i, col_w)

        self.table_inbox.verticalHeader().setVisible(False)
        self.table_inbox.setAlternatingRowColors(True)
        self.table_inbox.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_inbox.setStyleSheet(
            "QTableWidget { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; gridline-color: #F1F5F9; font-size: 12px; }"
            "QHeaderView::section { background: #F8FAFC; color: #475569; font-weight: 700; font-size: 11px; border: none; border-bottom: 1px solid #E2E8F0; padding: 6px; }"
        )

        self.empty_widget = EmptyStateWidget(
            title="No Practice Inbox Items Found",
            description="All incoming evidence documents, client requests, and AI classifications are up to date.",
        )

        body_layout.addWidget(self.table_inbox)
        body_layout.addWidget(self.empty_widget)
        body_layout.addStretch(1)

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.refresh()

    def _on_tab_changed(self, tab_key: str) -> None:
        self.current_tab = tab_key
        self.refresh()

    def refresh(self) -> None:
        """Fetches inbox summary payload and updates table rows."""
        filter_dto = InboxFilterDTO(
            tab=self.current_tab,
            client_id=self.current_client_id,
            search_query=self.search_input.text().strip() or None,
        )
        summary = self.inbox_service.get_inbox_items(filter_dto)

        # Update Tab Labels with Counts
        self.tab_buttons["ALL"].setText(f"All ({summary.total_items})")
        self.tab_buttons["NEEDS_REVIEW"].setText(f"Needs Review ({summary.needs_review_count}) ⚠️")
        self.tab_buttons["DOCUMENTS"].setText(f"Documents ({summary.documents_count}) 📄")
        self.tab_buttons["REQUESTS"].setText(f"Requests ({summary.requests_count}) 📋")
        self.tab_buttons["AI_SUGGESTIONS"].setText(f"AI Suggestions ({summary.ai_suggestions_count}) ✨")

        items = summary.items
        has_items = len(items) > 0
        self.table_inbox.setVisible(has_items)
        self.empty_widget.setVisible(not has_items)

        if not has_items:
            return

        self.table_inbox.setRowCount(0)
        for idx, item in enumerate(items):
            self.table_inbox.insertRow(idx)

            # 0. Client & FY
            c_text = f"{item.client_name}\nFY {item.financial_year}"
            c_item = QTableWidgetItem(c_text)
            c_item.setData(Qt.ItemDataRole.UserRole, item.id)

            # 1. Title
            title_item = QTableWidgetItem(item.title)

            # 2. Received Time
            ts_str = item.received_time.strftime("%d %b %Y, %H:%M")
            time_item = QTableWidgetItem(ts_str)

            # 3. Detected Type & Confidence Badge
            pct = item.confidence_percentage
            det_text = f"{item.detected_category} ({pct}%)"
            det_item = QTableWidgetItem(det_text)

            # 4. Status Badge
            status_item = QTableWidgetItem(f"● {item.status}")

            # 5. Interactive Actions Widget
            actions_widget = QWidget()
            act_layout = QHBoxLayout(actions_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(4)

            btn_accept = QPushButton("Accept")
            btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_accept.setStyleSheet(
                "QPushButton { background: #0284C7; color: #FFFFFF; font-size: 11px; font-weight: 600; border-radius: 4px; padding: 3px 8px; border: none; }"
                "QPushButton:hover { background: #0369A1; }"
            )
            btn_accept.clicked.connect(lambda _, doc_id=item.id: self._on_accept_clicked(doc_id))

            btn_edit = QPushButton("Edit")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(
                "QPushButton { background: #F8FAFC; color: #334155; font-size: 11px; font-weight: 500; border-radius: 4px; padding: 3px 8px; border: 1px solid #CBD5E1; }"
                "QPushButton:hover { background: #EFF6FF; color: #2563EB; }"
            )
            btn_edit.clicked.connect(
                lambda _, doc_id=item.id, cat=item.detected_category, score=item.confidence_score: self._on_edit_clicked(doc_id, cat, score)
            )

            btn_open = QPushButton("Open →")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet(
                "QPushButton { background: transparent; color: #2563EB; font-size: 11px; font-weight: 600; border: none; padding: 3px 6px; }"
                "QPushButton:hover { text-decoration: underline; }"
            )
            btn_open.clicked.connect(lambda _, route=item.target_route: self.navigate_to_route.emit(route))

            act_layout.addWidget(btn_accept)
            act_layout.addWidget(btn_edit)
            act_layout.addWidget(btn_open)

            table_items = [c_item, title_item, time_item, det_item, status_item]
            for col, t_item in enumerate(table_items):
                t_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table_inbox.setItem(idx, col, t_item)

            self.table_inbox.setCellWidget(idx, 5, actions_widget)

        self.table_inbox.setFixedHeight(len(items) * 42 + 34)

    def _on_accept_clicked(self, doc_id: str) -> None:
        if self.inbox_service.accept_classification(doc_id):
            QMessageBox.information(self, "Classification Accepted", "Document classification accepted successfully.")
            self.refresh()

    def _on_edit_clicked(self, doc_id: str, current_cat: str, confidence_score: float) -> None:
        dlg = CategoryOverrideDialog(current_category=current_cat, confidence_score=confidence_score, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.inbox_service.accept_classification(doc_id, human_category=dlg.selected_category):
                QMessageBox.information(
                    self,
                    "Classification Updated",
                    f"Category overridden to '{dlg.selected_category}' and approved.",
                )
                self.refresh()
