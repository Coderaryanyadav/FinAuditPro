"""Audit Query Management and Finding Escalation workspace view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
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

from finauditpro.application.services.audit_query_service import AuditQueryService
from finauditpro.domain.audit_matrix_entities import RiskSeverityEnum
from finauditpro.domain.pbc_and_query_entities import AuditQuery, AuditQueryStatusEnum
from finauditpro.ui.theme import CardWidget, MetricCard


class NewAuditQueryDialog(QDialog):
    """Dialog to raise a new audit query."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Raise Audit Query")
        self.resize(500, 360)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.area_input = QLineEdit()
        self.area_input.setPlaceholderText("e.g. Revenue Recognition / Trade Receivables")
        self.query_text_input = QTextEdit()
        self.query_text_input.setPlaceholderText("Detailed query / inquiry regarding ledger entries, missing vouchers, or terms...")
        self.query_text_input.setMaximumHeight(90)
        self.assigned_input = QLineEdit("Senior Auditor")
        self.client_contact_input = QLineEdit()
        self.client_contact_input.setPlaceholderText("Client Contact Person")
        self.evidence_requested_input = QLineEdit()
        self.evidence_requested_input.setPlaceholderText("e.g. Invoices #1021-1035 and Bank Confirmation")
        self.due_date_input = QLineEdit()
        self.due_date_input.setPlaceholderText("YYYY-MM-DD")

        form.addRow("Audit Area *:", self.area_input)
        form.addRow("Query Text *:", self.query_text_input)
        form.addRow("Assigned Auditor:", self.assigned_input)
        form.addRow("Client Contact:", self.client_contact_input)
        form.addRow("Evidence Requested:", self.evidence_requested_input)
        form.addRow("Due Date:", self.due_date_input)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Raise Query")
        btn_save.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _validate_and_accept(self) -> None:
        if not self.area_input.text().strip() or not self.query_text_input.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Please provide Audit Area and Query Text.")
            return
        self.accept()

    def get_data(self) -> dict[str, str | None]:
        return {
            "audit_area": self.area_input.text().strip(),
            "query_text": self.query_text_input.toPlainText().strip(),
            "assigned_to": self.assigned_input.text().strip() or "Associate",
            "client_contact": self.client_contact_input.text().strip() or None,
            "evidence_requested": self.evidence_requested_input.text().strip() or None,
            "due_date": self.due_date_input.text().strip() or None,
        }


class AuditQueryView(QWidget):
    """Interactive workspace for Audit Query lifecycle and Finding escalation."""

    def __init__(self, query_service: AuditQueryService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.query_service = query_service
        self.active_engagement_id: str | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 1. Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Audit Query & Follow-Up Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("Log audit inquiries, track client responses, resolve points, or escalate to formal audit findings.")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.btn_new = QPushButton("+ Raise Query")
        self.btn_new.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_new.clicked.connect(self._on_new_query)
        header_row.addWidget(self.btn_new)
        layout.addLayout(header_row)

        # 2. Metric Cards
        self.metrics_row = QHBoxLayout()
        self.metrics_row.setSpacing(14)
        self.card_total = MetricCard("TOTAL QUERIES", "0", "Raised on engagement", accent_color="#2563eb")
        self.card_sent = MetricCard("PENDING CLIENT", "0", "Awaiting response", accent_color="#f59e0b")
        self.card_resolved = MetricCard("RESOLVED", "0", "Satisfactorily closed", accent_color="#10b981")
        self.card_escalated = MetricCard("ESCALATED FINDINGS", "0", "Converted to findings", accent_color="#ef4444")
        for c in [self.card_total, self.card_sent, self.card_resolved, self.card_escalated]:
            self.metrics_row.addWidget(c)
        layout.addLayout(self.metrics_row)

        # 3. Main Table Card
        table_card = CardWidget("ENGAGEMENT AUDIT QUERIES")

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["AREA & QUERY", "ASSIGNED TO", "CLIENT CONTACT", "STATUS", "RESPONSE / RESOLUTION", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 6px; }")
        table_card.content_layout.addWidget(self.table)
        layout.addWidget(table_card, stretch=1)

    def set_active_engagement(self, engagement_id: str | None) -> None:
        self.active_engagement_id = engagement_id
        self.refresh()

    def refresh(self) -> None:
        if not self.active_engagement_id:
            self.table.setRowCount(0)
            return

        queries = self.query_service.list_queries(self.active_engagement_id)
        self.table.setRowCount(len(queries))

        total_cnt = len(queries)
        sent_cnt = sum(1 for q in queries if q.status == AuditQueryStatusEnum.SENT_TO_CLIENT)
        resolved_cnt = sum(1 for q in queries if q.status == AuditQueryStatusEnum.RESOLVED)
        escalated_cnt = sum(1 for q in queries if q.status == AuditQueryStatusEnum.ESCALATED_TO_FINDING)

        self.card_total.value_lbl.setText(str(total_cnt))
        self.card_sent.value_lbl.setText(str(sent_cnt))
        self.card_resolved.value_lbl.setText(str(resolved_cnt))
        self.card_escalated.value_lbl.setText(str(escalated_cnt))

        for row, q in enumerate(queries):
            query_item = QTableWidgetItem(f"[{q.audit_area}]\n{q.query_text}")
            assigned_item = QTableWidgetItem(q.assigned_to)
            contact_item = QTableWidgetItem(q.client_contact or "—")

            status_item = QTableWidgetItem(f"• {q.status.value}")
            if q.status == AuditQueryStatusEnum.RESOLVED:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif q.status == AuditQueryStatusEnum.ESCALATED_TO_FINDING:
                status_item.setForeground(Qt.GlobalColor.red)
            elif q.status == AuditQueryStatusEnum.CLIENT_RESPONDED:
                status_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                status_item.setForeground(Qt.GlobalColor.darkYellow)

            resp_text = q.response_text or q.resolution_notes or "Awaiting response..."
            resp_item = QTableWidgetItem(resp_text)

            self.table.setItem(row, 0, query_item)
            self.table.setItem(row, 1, assigned_item)
            self.table.setItem(row, 2, contact_item)
            self.table.setItem(row, 3, status_item)
            self.table.setItem(row, 4, resp_item)

            action_widget = self._make_action_widget(q)
            self.table.setCellWidget(row, 5, action_widget)

    def _make_action_widget(self, q: AuditQuery) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        if q.status not in (AuditQueryStatusEnum.RESOLVED, AuditQueryStatusEnum.ESCALATED_TO_FINDING):
            btn_resp = QPushButton("Log Reply")
            btn_resp.setStyleSheet("font-size: 11px; padding: 3px 8px;")
            btn_resp.clicked.connect(lambda _, q_id=q.id: self._on_log_reply(q_id))
            lay.addWidget(btn_resp)

            btn_res = QPushButton("Resolve")
            btn_res.setStyleSheet("background-color: #10b981; color: white; font-size: 11px; font-weight: bold; padding: 3px 8px;")
            btn_res.clicked.connect(lambda _, q_id=q.id: self._on_resolve(q_id))
            lay.addWidget(btn_res)

            btn_esc = QPushButton("Escalate")
            btn_esc.setStyleSheet("background-color: #ef4444; color: white; font-size: 11px; font-weight: bold; padding: 3px 8px;")
            btn_esc.clicked.connect(lambda _, query=q: self._on_escalate(query))
            lay.addWidget(btn_esc)
        else:
            lbl_done = QLabel("Closed" if q.status == AuditQueryStatusEnum.RESOLVED else "Escalated")
            lbl_done.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 500;")
            lay.addWidget(lbl_done)

        return w

    def _on_log_reply(self, query_id: str) -> None:
        text, ok = QInputDialog.getMultiLineText(self, "Log Client Response", "Enter explanation or documents provided by client:")
        if ok and text.strip():
            self.query_service.record_client_response(query_id, text.strip())
            self.refresh()

    def _on_resolve(self, query_id: str) -> None:
        notes, ok = QInputDialog.getText(self, "Resolve Audit Query", "Enter resolution notes / audit verification conclusion:")
        if ok and notes.strip():
            self.query_service.resolve_query(query_id, notes.strip())
            self.refresh()

    def _on_escalate(self, q: AuditQuery) -> None:
        title, ok1 = QInputDialog.getText(self, "Escalate to Finding", "Audit Finding Title:", text=f"Unresolved Query: {q.audit_area}")
        if not ok1 or not title.strip():
            return
        desc, ok2 = QInputDialog.getMultiLineText(self, "Escalate to Finding", "Finding Description / Impact:", text=f"Client explanation was inadequate or missing for query:\n{q.query_text}")
        if not ok2 or not desc.strip():
            return

        self.query_service.escalate_to_finding(
            query_id=q.id,
            finding_title=title.strip(),
            finding_description=desc.strip(),
            severity=RiskSeverityEnum.HIGH,
        )
        QMessageBox.information(self, "Escalated", f"Query escalated to formal Audit Finding '{title.strip()}'.")
        self.refresh()

    def _on_new_query(self) -> None:
        if not self.active_engagement_id:
            QMessageBox.warning(self, "No Active Audit", "Please select an active engagement first.")
            return
        dlg = NewAuditQueryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self.query_service.raise_query(
                engagement_id=self.active_engagement_id,
                audit_area=str(data["audit_area"]),
                query_text=str(data["query_text"]),
                assigned_to=str(data["assigned_to"]),
                client_contact=data["client_contact"],
                evidence_requested=data["evidence_requested"],
                due_date=data["due_date"],
            )
            self.refresh()
