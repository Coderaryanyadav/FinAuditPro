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
        title = QLabel("Client Document Requests (PBC Tracker)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("Track, follow up, and verify Provided By Client (PBC) statutory evidence and schedules.")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_seed = QPushButton("Auto-Seed Statutory PBC Package")
        self.btn_seed.setStyleSheet("background-color: #f8fafc; color: #0f172a; border: 1px solid #cbd5e1; font-weight: 500; padding: 6px 12px;")
        self.btn_seed.clicked.connect(self._on_seed_pbc)
        header_row.addWidget(self.btn_seed)

        self.btn_new = QPushButton("+ New Request")
        self.btn_new.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_new.clicked.connect(self._on_new_request)
        header_row.addWidget(self.btn_new)
        layout.addLayout(header_row)

        # 2. Metric Cards
        self.metrics_row = QHBoxLayout()
        self.metrics_row.setSpacing(14)
        self.card_total = MetricCard("TOTAL REQUESTED", "0", "Standard audit items", accent_color="#2563eb")
        self.card_pending = MetricCard("PENDING CLIENT", "0", "Awaiting upload", accent_color="#f59e0b")
        self.card_review = MetricCard("UNDER REVIEW", "0", "Received / verifying", accent_color="#8b5cf6")
        self.card_accepted = MetricCard("ACCEPTED", "0", "Evidence verified", accent_color="#10b981")
        for c in [self.card_total, self.card_pending, self.card_review, self.card_accepted]:
            self.metrics_row.addWidget(c)
        layout.addLayout(self.metrics_row)

        # 3. Main Table Card
        table_card = CardWidget()
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(16, 14, 16, 16)
        tc_layout.setSpacing(10)

        tc_header = QLabel("PBC AUDIT REQUEST DIRECTORY")
        tc_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569; letter-spacing: 0.5px;")
        tc_layout.addWidget(tc_header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["DOCUMENT / SCHEDULE", "AUDIT PERIOD", "CONTACT", "DUE DATE", "STATUS", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }")
        tc_layout.addWidget(self.table)
        layout.addWidget(table_card, stretch=1)

    def set_active_engagement(self, engagement_id: str | None) -> None:
        self.active_engagement_id = engagement_id
        self.refresh()

    def refresh(self) -> None:
        if not self.active_engagement_id:
            self.table.setRowCount(0)
            return

        requests = self.pbc_service.list_requests(self.active_engagement_id)
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

            action_widget = self._make_action_widget(req)
            self.table.setCellWidget(row, 5, action_widget)

    def _make_action_widget(self, req: DocumentRequest) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        combo = QComboBox()
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
