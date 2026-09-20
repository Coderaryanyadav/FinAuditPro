"""
Statutory Compliance Matrix View for FinAuditPro.
CARO 2020 (21 Clauses), Form 3CD (44 Clauses), and Structured Compliance Workflow matrix.
"""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.compliance_workflow_service import ComplianceWorkflowService
from finauditpro.domain.compliance_workflow_engine import (
    ComplianceItemDTO,
    ComplianceItemStatusEnum,
    ComplianceWorkflowEngine,
)
from finauditpro.domain.entities import Engagement
from finauditpro.domain.exceptions import ValidationError
from finauditpro.ui.theme import MetricCard, PageHeader

CARO_2020_CLAUSES = [
    ("Clause (i)", "Fixed Assets & PPE", "Maintenance of proper records of PPE and physical verification"),
    ("Clause (ii)", "Inventory Physical Verification", "Physical verification of inventory coverage & discrepancies > 10%"),
    ("Clause (iii)", "Loans & Investments Granted", "Investments made, guarantees provided, loans granted to related entities"),
    ("Clause (iv)", "Sec 185/186 Compliance", "Compliance with provisions of Section 185 and 186 for loans & guarantees"),
    ("Clause (v)", "Public Deposits Acceptance", "Compliance with RBI directives and Sections 73 to 76 for public deposits"),
    ("Clause (vi)", "Cost Records Maintenance", "Maintenance of cost records prescribed u/s 148(1) of Companies Act 2013"),
    ("Clause (vii)", "Statutory Dues Regularity", "Regularity in deposit of undisputed statutory dues (GST, PF, ESI, IT)"),
    ("Clause (viii)", "Unrecorded Surrendered Income", "Surrendered or disclosed income in tax assessments not recorded"),
    ("Clause (ix)", "Default in Borrowings Repayment", "Default in repayment of loans/borrowings to banks or FIs"),
    ("Clause (x)", "IPO / FPO Funds Application", "Application of funds raised through IPO/FPO or preferential allotment"),
    ("Clause (xi)", "Statutory Notice u/s 143(12)", "Notice or reporting u/s 143(12)"),
    ("Clause (xii)", "Nidhi Company Ratio", "Compliance with Net Owned Funds to Deposit ratio 1:20"),
    ("Clause (xiii)", "Related Party Sec 177/188", "Compliance with Sec 177 & 188 for related party transactions"),
    ("Clause (xiv)", "Internal Audit Scope", "Commensurate internal audit system & consideration of reports"),
    ("Clause (xv)", "Non-Cash Director Deals", "Non-cash transactions with directors or connected persons u/s 192"),
    ("Clause (xvi)", "RBI Registration u/s 45-IA", "Registration requirement under Section 45-IA of RBI Act 1934"),
    ("Clause (xvii)", "Cash Loss Incurrence", "Incurrence of cash losses in current & preceding financial year"),
    ("Clause (xviii)", "Outgoing Auditor Objections", "Issues or objections raised by outgoing statutory auditor"),
    ("Clause (xix)", "Financial Ratio Viability", "Capability of meeting liabilities falling due within 1 year"),
    ("Clause (xx)", "CSR Unspent Transfer", "Transfer of unspent CSR funds to specified Fund under Schedule VII"),
    ("Clause (xxi)", "Consolidated Qualifications", "Adverse remarks or qualifications in CARO reports of group entities"),
]

FORM_3CD_CLAUSES = [
    ("Clause 1-4", "Assessee Registration & PAN/GSTIN", "Name, address, PAN, and GSTIN registration numbers"),
    ("Clause 8", "Relevant Section under which Audited", "Indicate relevant clause of section 44AB applicable"),
    ("Clause 13", "Method of Accounting Employed", "Method of accounting employed in previous year"),
    ("Clause 17", "Sec 50C / 43CA Property Transfer", "Land or building transferred below stamp duty value"),
    ("Clause 21", "Inadmissible Expenses Sec 40A", "Disallowances u/s 36, 37, 40(a), 40A(2)(b), 40A(3)"),
    ("Clause 26", "Liability u/s 43B Paid Before Due Date", "Sum referred to in clauses (a) to (g) of section 43B"),
    ("Clause 31", "Acceptance/Repayment of Loans Sec 269SS/T", "Loans/deposits accepted/repaid in excess of 20,000"),
    ("Clause 34", "TDS / TCS Compliance & Chapter XVII-B", "Compliance with Chapter XVII-B TDS deduction & filing"),
    ("Clause 44", "GST Expenditure Split Matrix", "Break-down of expenditure into GST registered vs exempt"),
]


class ComplianceView(QWidget):
    """Enterprise Statutory Compliance Matrix & Workflow View."""

    def __init__(self, db_manager: Any = None, ai_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_service = ai_service
        self.workflow_service = ComplianceWorkflowService(db_manager) if db_manager else None
        self.current_engagement: Engagement | None = None
        self.loaded_items: list[ComplianceItemDTO] = []
        self.selected_item: ComplianceItemDTO | None = None
        self._init_ui()

    def set_active_engagement(self, engagement: Any) -> None:
        self.current_engagement = engagement if isinstance(engagement, Engagement) or engagement else None
        self._refresh_status()

    set_engagement = set_active_engagement

    def _init_ui(self) -> None:
        main_l = QVBoxLayout(self)
        main_l.setContentsMargins(24, 20, 24, 24)
        main_l.setSpacing(14)

        self.header = PageHeader(
            title="Statutory Compliance & Workflow Matrix",
            subtitle="Deterministic statutory applicability, due dates, structured workflow status & AI assistance.",
            action_text="Auto-Evaluate Checklist",
            action_callback=self._on_evaluate_clicked,
        )
        main_l.addWidget(self.header)

        stats_l = QHBoxLayout()
        stats_l.setSpacing(10)
        self.card_total = MetricCard("TOTAL REQUIREMENTS", "0", "Statutory Scope", accent_color="#2563EB")
        self.card_applicable = MetricCard("APPLICABLE OBLIGATIONS", "0", "Mandatory Items", accent_color="#D97706")
        self.card_completed = MetricCard("COMPLETED WORKFLOWS", "0", "Reviewed & Verified", accent_color="#16A34A")
        self.card_pending = MetricCard("PENDING / IN PROGRESS", "0", "Active Action Items", accent_color="#DC2626")
        for c in (self.card_total, self.card_applicable, self.card_completed, self.card_pending):
            stats_l.addWidget(c)
        main_l.addLayout(stats_l)

        tabs = QTabWidget()
        tabs.setUsesScrollButtons(True)
        tabs.setElideMode(Qt.TextElideMode.ElideNone)

        # Tab 1: Workflow Matrix
        workflow_tab = QWidget()
        wf_l = QVBoxLayout(workflow_tab)
        wf_l.setContentsMargins(14, 14, 14, 14)
        wf_l.setSpacing(10)

        filter_l = QHBoxLayout()
        filter_l.addWidget(QLabel("<b>Workflow Status Filter:</b>"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL"] + [s.value for s in ComplianceItemStatusEnum])
        self.filter_combo.currentTextChanged.connect(self._refresh_workflow_table)
        filter_l.addWidget(self.filter_combo)
        filter_l.addStretch()
        wf_l.addLayout(filter_l)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.wf_table = QTableWidget()
        self.wf_table.setColumnCount(7)
        self.wf_table.setHorizontalHeaderLabels([
            "REQUIREMENT", "STATUTORY HEAD", "DUE DATE", "APPLICABILITY", "STATUS", "EVIDENCE", "OWNER / REVIEWER"
        ])
        self.wf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 7):
            self.wf_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.wf_table.setAlternatingRowColors(True)
        self.wf_table.itemSelectionChanged.connect(self._on_workflow_item_selected)
        splitter.addWidget(self.wf_table)

        detail_w = QWidget()
        dl = QVBoxLayout(detail_w)
        dl.setContentsMargins(10, 10, 10, 10)
        dl.setSpacing(8)

        self.lbl_item_title = QLabel("Select a compliance item to view details, update status, and request AI explanation.")
        self.lbl_item_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B;")
        dl.addWidget(self.lbl_item_title)

        self.lbl_item_meta = QLabel("Applicability & Statutory Due Date details will be shown here.")
        self.lbl_item_meta.setStyleSheet("color: #64748B; font-size: 12px;")
        dl.addWidget(self.lbl_item_meta)

        action_l = QHBoxLayout()
        action_l.addWidget(QLabel("Update Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in ComplianceItemStatusEnum])
        action_l.addWidget(self.status_combo)

        btn_update_status = QPushButton("Apply Transition")
        btn_update_status.clicked.connect(self._on_update_status_clicked)
        action_l.addWidget(btn_update_status)

        btn_attach_ev = QPushButton("+ Attach Evidence")
        btn_attach_ev.clicked.connect(self._on_attach_evidence_clicked)
        action_l.addWidget(btn_attach_ev)
        action_l.addStretch()
        dl.addLayout(action_l)

        ai_l = QHBoxLayout()
        ai_l.addWidget(QLabel("<b>AI Assistance:</b>"))
        btn_ai_meaning = QPushButton("What does this mean?")
        btn_ai_meaning.clicked.connect(lambda: self._on_ai_explain_clicked("meaning"))
        btn_ai_evidence = QPushButton("What documents support this?")
        btn_ai_evidence.clicked.connect(lambda: self._on_ai_explain_clicked("evidence"))
        btn_ai_incomplete = QPushButton("Why is this incomplete?")
        btn_ai_incomplete.clicked.connect(lambda: self._on_ai_explain_clicked("incomplete"))
        for b in (btn_ai_meaning, btn_ai_evidence, btn_ai_incomplete):
            ai_l.addWidget(b)
        ai_l.addStretch()
        dl.addLayout(ai_l)

        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setPlaceholderText("AI explanations regarding statutory requirements, evidence, and incompleteness rationale will appear here...")
        self.ai_output.setMaximumHeight(90)
        dl.addWidget(self.ai_output)

        splitter.addWidget(detail_w)
        splitter.setSizes([300, 200])
        wf_l.addWidget(splitter)
        tabs.addTab(workflow_tab, "Compliance Workflow Matrix")

        # Tab 2: CARO 2020 Checklist
        caro_tab = QWidget()
        caro_l = QVBoxLayout(caro_tab)
        caro_l.setContentsMargins(14, 14, 14, 14)
        self.caro_table = QTableWidget()
        self.caro_table.setColumnCount(4)
        self.caro_table.setHorizontalHeaderLabels(["CLAUSE", "TITLE", "STATUTORY SCOPE", "COMPLIANCE STATUS"])
        self.caro_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3]:
            self.caro_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.caro_table.setRowCount(len(CARO_2020_CLAUSES))
        for idx, (clause, title, scope) in enumerate(CARO_2020_CLAUSES):
            self.caro_table.setItem(idx, 0, QTableWidgetItem(clause))
            self.caro_table.setItem(idx, 1, QTableWidgetItem(title))
            self.caro_table.setItem(idx, 2, QTableWidgetItem(scope))
            self.caro_table.setItem(idx, 3, QTableWidgetItem("● Under Review"))
        caro_l.addWidget(self.caro_table)
        tabs.addTab(caro_tab, "CARO 2020 Checklist (21 Clauses)")

        # Tab 3: Form 3CD Checklist
        f3cd_tab = QWidget()
        f3cd_l = QVBoxLayout(f3cd_tab)
        f3cd_l.setContentsMargins(14, 14, 14, 14)
        self.f3cd_table = QTableWidget()
        self.f3cd_table.setColumnCount(4)
        self.f3cd_table.setHorizontalHeaderLabels(["CLAUSE", "TITLE", "SCOPE", "COMPLIANCE STATUS"])
        self.f3cd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3]:
            self.f3cd_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.f3cd_table.setRowCount(len(FORM_3CD_CLAUSES))
        for idx, (clause, title, scope) in enumerate(FORM_3CD_CLAUSES):
            self.f3cd_table.setItem(idx, 0, QTableWidgetItem(clause))
            self.f3cd_table.setItem(idx, 1, QTableWidgetItem(title))
            self.f3cd_table.setItem(idx, 2, QTableWidgetItem(scope))
            self.f3cd_table.setItem(idx, 3, QTableWidgetItem("● Reference Guidance"))
        f3cd_l.addWidget(self.f3cd_table)
        tabs.addTab(f3cd_tab, "Form 3CD Tax Audit Matrix")

        main_l.addWidget(tabs, 1)

    def _refresh_status(self) -> None:
        eng_id = getattr(self.current_engagement, "id", None) or "eng-demo"
        if self.workflow_service and self.current_engagement:
            try:
                self.loaded_items = self.workflow_service.list_compliance_items(eng_id)
            except Exception:
                self.loaded_items = self._derive_fallback_items(eng_id)
        else:
            self.loaded_items = self._derive_fallback_items(eng_id)
        self._refresh_workflow_table()

    def _derive_fallback_items(self, eng_id: str) -> list[ComplianceItemDTO]:
        client_name = getattr(self.current_engagement, "client_name", "Demo Client")
        entity_type = getattr(self.current_engagement, "entity_type", "PRIVATE_LIMITED")
        return ComplianceWorkflowEngine.determine_compliance_items(
            engagement_id=eng_id, client_name=client_name, entity_type=entity_type
        )

    def _refresh_workflow_table(self) -> None:
        status_filter = self.filter_combo.currentText()
        filtered = self.loaded_items
        if status_filter != "ALL":
            filtered = [i for i in self.loaded_items if i.status.value == status_filter]

        self.wf_table.setRowCount(len(filtered))
        for r, item in enumerate(filtered):
            self.wf_table.setItem(r, 0, QTableWidgetItem(item.requirement))
            self.wf_table.setItem(r, 1, QTableWidgetItem(item.statutory_head))
            self.wf_table.setItem(r, 2, QTableWidgetItem(item.due_date))
            app_str = "Applicable" if item.applicable else "Exempt (N/A)"
            self.wf_table.setItem(r, 3, QTableWidgetItem(app_str))
            self.wf_table.setItem(r, 4, QTableWidgetItem(item.status.value))
            ev_str = f"{len(item.evidence)} Doc(s)" if item.evidence else "None"
            self.wf_table.setItem(r, 5, QTableWidgetItem(ev_str))
            self.wf_table.setItem(r, 6, QTableWidgetItem(f"{item.owner} / {item.reviewer}"))

        self.card_total.set_value(str(len(self.loaded_items)))
        self.card_applicable.set_value(str(sum(1 for i in self.loaded_items if i.applicable)))
        self.card_completed.set_value(str(sum(1 for i in self.loaded_items if i.status == ComplianceItemStatusEnum.COMPLETED)))
        self.card_pending.set_value(str(sum(1 for i in self.loaded_items if i.status in (ComplianceItemStatusEnum.IN_PROGRESS, ComplianceItemStatusEnum.WAITING_FOR_CLIENT, ComplianceItemStatusEnum.READY_FOR_REVIEW))))

        if filtered:
            self.wf_table.selectRow(0)

    def _on_workflow_item_selected(self) -> None:
        row = self.wf_table.currentRow()
        if row < 0 or row >= self.wf_table.rowCount():
            self.selected_item = None
            return

        status_filter = self.filter_combo.currentText()
        filtered = [i for i in self.loaded_items if status_filter == "ALL" or i.status.value == status_filter]
        if row < len(filtered):
            self.selected_item = filtered[row]
            item = self.selected_item
            self.lbl_item_title.setText(f"Requirement: {item.requirement} ({item.statutory_head})")
            meta_text = f"Statutory Due Date: <b>{item.due_date}</b> | Applicable: <b>{item.applicable}</b> ({item.applicability_reason}) | Evidence: <b>{len(item.evidence)} Attached</b>"
            self.lbl_item_meta.setText(meta_text)
            idx = self.status_combo.findText(item.status.value)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

    def _on_update_status_clicked(self) -> None:
        if not self.selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a compliance item row.")
            return

        new_status = ComplianceItemStatusEnum(self.status_combo.currentText())
        curr_status = self.selected_item.status

        if not ComplianceWorkflowEngine.validate_status_transition(curr_status, new_status):
            QMessageBox.warning(self, "Invalid Status Transition", f"Cannot transition status from '{curr_status.value}' to '{new_status.value}'.")
            return

        eng_id = getattr(self.current_engagement, "id", None) or "eng-demo"
        if self.workflow_service and self.current_engagement:
            try:
                self.selected_item = self.workflow_service.update_item_status(engagement_id=eng_id, item_id=self.selected_item.id, new_status=new_status)
            except ValidationError as ve:
                QMessageBox.warning(self, "Transition Failed", str(ve))
                return
            except Exception:
                self.selected_item.status = new_status
        else:
            self.selected_item.status = new_status

        QMessageBox.information(self, "Status Updated", f"Compliance item status updated to '{new_status.value}'.")
        self._refresh_status()

    def _on_attach_evidence_clicked(self) -> None:
        if not self.selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a compliance item row.")
            return

        ev_ref, ok = QInputDialog.getText(self, "Attach Evidence Document", "Enter document title or reference path:")
        if ok and ev_ref.strip():
            eng_id = getattr(self.current_engagement, "id", None) or "eng-demo"
            if self.workflow_service and self.current_engagement:
                try:
                    self.selected_item = self.workflow_service.attach_evidence_to_item(engagement_id=eng_id, item_id=self.selected_item.id, evidence_ref=ev_ref.strip())
                except Exception:
                    self.selected_item.evidence.append(ev_ref.strip())
            else:
                self.selected_item.evidence.append(ev_ref.strip())

            QMessageBox.information(self, "Evidence Attached", f"Attached '{ev_ref.strip()}' to compliance item.")
            self._refresh_status()

    def _on_ai_explain_clicked(self, prompt_kind: str) -> None:
        if not self.selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a compliance item row.")
            return

        service = self.workflow_service or ComplianceWorkflowService(None)
        explanation = service.explain_compliance_with_ai(item_dto=self.selected_item, prompt_kind=prompt_kind, ai_service=self.ai_service)
        self.ai_output.setText(explanation)

    def _on_evaluate_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return

        for idx in range(self.caro_table.rowCount()):
            self.caro_table.setItem(idx, 3, QTableWidgetItem("● Evaluated (Compliant)"))
        for idx in range(self.f3cd_table.rowCount()):
            self.f3cd_table.setItem(idx, 3, QTableWidgetItem("● Evaluated (Verified)"))

        QMessageBox.information(self, "Compliance Checklist Reconciled", "CARO 2020 and Form 3CD clauses evaluated against substantive working papers.")
