"""Client Document Request (PBC) Tracker workspace view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
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

from finauditpro.application.services.document_request_service import DocumentRequestService
from finauditpro.domain.pbc_and_query_entities import DocumentRequest, DocumentRequestStatusEnum
from finauditpro.ui.theme import CardWidget, MetricCard
from finauditpro.ui.widgets.custom_combo import CustomComboBox


class NewPBCRequestDialog(QDialog):
    """Dialog to create a new client document request."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Client Document Request (PBC)")
        self.resize(480, 320)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Bank Statements & CC Statements Q4")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Detailed description of required schedules, formats, or certificates...")
        self.desc_input.setMaximumHeight(80)
        self.period_input = QLineEdit("FY 2025-26")
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Client CFO / Accounts Manager Name")
        self.due_date_input = QLineEdit()
        self.due_date_input.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Document Title *:", self.title_input)
        form.addRow("Description *:", self.desc_input)
        form.addRow("Audit Period:", self.period_input)
        form.addRow("Client Contact:", self.contact_input)
        form.addRow("Due Date:", self.due_date_input)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Create Request")
        btn_save.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _validate_and_accept(self) -> None:
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please provide a document title.")
            return
        if not self.desc_input.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Please provide a description.")
            return
        self.accept()

    def get_data(self) -> dict[str, str | None]:
        return {
            "title": self.title_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "period": self.period_input.text().strip() or "FY 2025-26",
            "contact_name": self.contact_input.text().strip() or None,
            "due_date": self.due_date_input.text().strip() or None,
        }


class PBCTrackerView(QWidget):
    """Interactive workspace for Provided By Client (PBC) document request tracking."""

    def __init__(self, pbc_service: DocumentRequestService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pbc_service = pbc_service
        self.active_engagement_id: str | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 1. Header & Actions
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Client Document Requests (PBC) & SA 505 Confirmations")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("Track, follow up, and verify Provided By Client (PBC) statutory evidence and SA 505 Third-Party External Confirmations.")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_seed_conf = QPushButton("+ Seed SA 505 Letters")
        self.btn_seed_conf.setStyleSheet("background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; font-weight: 600; padding: 6px 12px; border-radius: 6px;")
        self.btn_seed_conf.clicked.connect(self._on_seed_confirmations)
        header_row.addWidget(self.btn_seed_conf)

        self.btn_seed = QPushButton("Auto-Seed Statutory PBC")
        self.btn_seed.setStyleSheet("background-color: #f8fafc; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 500; padding: 6px 12px; border-radius: 6px;")
        self.btn_seed.clicked.connect(self._on_seed_pbc)
        header_row.addWidget(self.btn_seed)

        self.btn_new = QPushButton("+ New Request")
        self.btn_new.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        self.btn_new.clicked.connect(self._on_new_request)
        header_row.addWidget(self.btn_new)
        layout.addLayout(header_row)

        # 2. Metric Cards
        self.metrics_row = QHBoxLayout()
        self.metrics_row.setSpacing(14)
        self.card_total = MetricCard("TOTAL REQUESTED", "0", "Standard audit items", accent_color="#2563eb")
        self.card_pending = MetricCard("PENDING CLIENT", "0", "Awaiting upload", accent_color="#f59e0b")
        self.card_review = MetricCard("UNDER REVIEW", "0", "Received / verifying", accent_color="#8b5cf6")
        self.card_accepted = MetricCard("ACCEPTED / CONFIRMED", "0", "Evidence verified", accent_color="#10b981")
        for c in [self.card_total, self.card_pending, self.card_review, self.card_accepted]:
            self.metrics_row.addWidget(c)
        layout.addLayout(self.metrics_row)

        # 3. Segmented Tab Selection
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideNone)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)
        self.tabs.tabBar().setExpanding(False)

        # Tab 1: PBC Document Directory
        table_card = CardWidget("PBC AUDIT REQUEST DIRECTORY")
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["DOCUMENT / SCHEDULE", "AUDIT PERIOD", "CONTACT", "DUE DATE", "STATUS", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }")
        self.table.setVisible(False)

        from finauditpro.ui.theme import EmptyStateWidget
        self.empty_state = EmptyStateWidget(
            title="No PBC document requests active",
            description="Generate standard statutory document requests (TB, bank reconciliations, GST returns) or add custom PBC schedules.",
            action_text="Auto-Seed Statutory PBC Package",
            action_callback=self._on_seed_pbc,
        )
        table_card.content_layout.addWidget(self.table)
        table_card.content_layout.addWidget(self.empty_state)
        self.tabs.addTab(table_card, "Client Document Requests (PBC)")

        # Tab 2: SA 505 External Confirmations
        conf_card = CardWidget("SA 505 THIRD-PARTY BALANCE CONFIRMATIONS")
        self.conf_table = QTableWidget()
        self.conf_table.setColumnCount(6)
        self.conf_table.setHorizontalHeaderLabels(["TYPE / PARTY", "REF / MANDATE", "BOOK BAL (₹)", "CONFIRMED BAL (₹)", "STATUS", "ACTIONS"])
        self.conf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 6):
            self.conf_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.conf_table.verticalHeader().setVisible(False)
        self.conf_table.setAlternatingRowColors(True)
        self.conf_table.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }")

        self.conf_empty = EmptyStateWidget(
            title="No external confirmations logged",
            description="Generate standard SA 505 bank and debtor balance confirmation requests.",
            action_text="+ Seed SA 505 Letters",
            action_callback=self._on_seed_confirmations,
        )
        conf_card.content_layout.addWidget(self.conf_table)
        conf_card.content_layout.addWidget(self.conf_empty)
        self.tabs.addTab(conf_card, "SA 505 External Confirmations")

        layout.addWidget(self.tabs, stretch=1)

    def set_active_engagement(self, engagement_id: str | None) -> None:
        self.active_engagement_id = engagement_id
        self.refresh()

    def refresh(self) -> None:
        if not self.active_engagement_id:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            self.table.setRowCount(0)
            self.conf_table.setVisible(False)
            self.conf_empty.setVisible(True)
            self.conf_table.setRowCount(0)
            return

        # 1. Refresh PBC Requests Table
        requests = self.pbc_service.list_requests(self.active_engagement_id)
        has_reqs = len(requests) > 0
        self.table.setVisible(has_reqs)
        self.empty_state.setVisible(not has_reqs)
        self.table.setRowCount(len(requests))

        total_cnt = len(requests)
        pending_cnt = sum(1 for r in requests if r.status in (DocumentRequestStatusEnum.REQUESTED, DocumentRequestStatusEnum.PARTIALLY_RECEIVED))
        review_cnt = sum(1 for r in requests if r.status in (DocumentRequestStatusEnum.RECEIVED, DocumentRequestStatusEnum.UNDER_REVIEW))
        accepted_cnt = sum(1 for r in requests if r.status == DocumentRequestStatusEnum.ACCEPTED)

        self.card_total.value_lbl.setText(str(total_cnt))
        self.card_pending.value_lbl.setText(str(pending_cnt))
        self.card_review.value_lbl.setText(str(review_cnt))
        self.card_accepted.value_lbl.setText(str(accepted_cnt))

        for row, req in enumerate(requests):
            title_item = QTableWidgetItem(f"{req.title}\n{req.description[:70]}...")
            title_item.setToolTip(req.description)
            period_item = QTableWidgetItem(req.period)
            contact_item = QTableWidgetItem(req.contact_name or "Finance Team")
            due_item = QTableWidgetItem(req.due_date or "—")

            status_item = QTableWidgetItem(f"• {req.status.value}")
            if req.status == DocumentRequestStatusEnum.ACCEPTED:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif req.status in (DocumentRequestStatusEnum.RECEIVED, DocumentRequestStatusEnum.UNDER_REVIEW):
                status_item.setForeground(Qt.GlobalColor.darkMagenta)
            elif req.status == DocumentRequestStatusEnum.REJECTED:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)

            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, period_item)
            self.table.setItem(row, 2, contact_item)
            self.table.setItem(row, 3, due_item)
            self.table.setItem(row, 4, status_item)
            self.table.setCellWidget(row, 5, self._make_action_widget(req))

        # 2. Refresh SA 505 Confirmations Table
        confs = self.pbc_service.list_confirmations_for_engagement(self.active_engagement_id)
        has_confs = len(confs) > 0
        self.conf_table.setVisible(has_confs)
        self.conf_empty.setVisible(not has_confs)
        self.conf_table.setRowCount(len(confs))

        for row, conf in enumerate(confs):
            c_type_str = conf.confirmation_type.value if hasattr(conf.confirmation_type, "value") else str(conf.confirmation_type)
            p_name = conf.third_party_name
            self.conf_table.setItem(row, 0, QTableWidgetItem(f"{p_name}\n({c_type_str[:30]}...)"))
            self.conf_table.setItem(row, 1, QTableWidgetItem(conf.account_reference or "Ref / Mandate"))
            self.conf_table.setItem(row, 2, QTableWidgetItem(f"₹{conf.book_balance_paise / 100:,.2f}"))
            conf_amt_str = f"₹{conf.confirmed_balance_paise / 100:,.2f}" if conf.confirmed_balance_paise is not None else "—"
            self.conf_table.setItem(row, 3, QTableWidgetItem(conf_amt_str))

            c_status_str = conf.status.value if hasattr(conf.status, "value") else str(conf.status)
            s_item = QTableWidgetItem(f"• {c_status_str}")
            if "Agreed" in c_status_str or "Cleared" in c_status_str:
                s_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "Dispute" in c_status_str:
                s_item.setForeground(Qt.GlobalColor.red)
            else:
                s_item.setForeground(Qt.GlobalColor.darkBlue)
            self.conf_table.setItem(row, 4, s_item)

            btn_log = QPushButton("Log Reply")
            btn_log.setStyleSheet("font-size: 11px; padding: 3px 8px;")
            btn_log.clicked.connect(lambda _, cid=conf.id: self._on_log_conf_reply(cid))
            self.conf_table.setCellWidget(row, 5, btn_log)

    def _on_log_conf_reply(self, conf_id: str) -> None:
        from PySide6.QtWidgets import QInputDialog
        amt_str, ok1 = QInputDialog.getText(self, "Record Third-Party Confirmation", "Enter confirmed balance amount in ₹ (e.g. 500000.00):")
        if not ok1 or not amt_str.strip():
            return
        try:
            amt_float = float(amt_str.replace(",", "").strip())
            amt_paise = int(round(amt_float * 100))
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric rupee amount.")
            return

        notes, _ = QInputDialog.getText(self, "Record Confirmation Notes", "Enter discrepancy explanation or verification notes (optional):")
        self.pbc_service.record_confirmation_response(
            confirmation_id=conf_id,
            confirmed_balance_paise=amt_paise,
            response_date="2026-03-31",
            explanation=notes.strip() if notes else None,
        )
        QMessageBox.information(self, "Response Recorded", "Third-party balance confirmation response successfully logged per SA 505.")
        self.refresh()

    def _make_action_widget(self, req: DocumentRequest) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)
        combo = CustomComboBox()
        for s in DocumentRequestStatusEnum:
            combo.addItem(s.value, s)
        idx = combo.findData(req.status)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda _, r_id=req.id, cb=combo: self._on_status_changed(r_id, cb))
        lay.addWidget(combo)
        return w

    def _on_status_changed(self, request_id: str, combo: QComboBox) -> None:
        target_status = combo.currentData()
        try:
            self.pbc_service.update_status(request_id, target_status)
            self.refresh()
        except Exception as ex:
            QMessageBox.critical(self, "Status Update Error", str(ex))

    def _on_seed_pbc(self) -> None:
        if not self.active_engagement_id:
            QMessageBox.warning(self, "No Active Audit", "Please select an active engagement first.")
            return
        self.pbc_service.seed_default_pbc_package(self.active_engagement_id)
        QMessageBox.information(self, "PBC Package Seeded", "Standard ICAI statutory PBC document requests initialized.")
        self.refresh()

    def _on_seed_confirmations(self) -> None:
        if not self.active_engagement_id:
            QMessageBox.warning(self, "No Active Audit", "Please select an active engagement first.")
            return
        created = self.pbc_service.seed_default_confirmations(self.active_engagement_id)
        QMessageBox.information(self, "SA 505 Letters Seeded", f"Successfully generated {len(created)} standard third-party external balance confirmation requests.")
        self.refresh()

    def _on_new_request(self) -> None:
        if not self.active_engagement_id:
            QMessageBox.warning(self, "No Active Audit", "Please select an active engagement first.")
            return
        dlg = NewPBCRequestDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self.pbc_service.create_request(
                engagement_id=self.active_engagement_id,
                title=str(data["title"]),
                description=str(data["description"]),
                period=str(data["period"]),
                contact_name=data["contact_name"],
                due_date=data["due_date"],
            )
            self.refresh()

