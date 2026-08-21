"""Dialog for logging structured Audit Findings."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_planning_dtos import CreateFindingDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    FindingSourceEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import Engagement


class FindingDialog(QDialog):
    """Modal dialog for logging a structured Audit Finding entity."""

    def __init__(
        self,
        planning_service: AuditPlanningService,
        engagement: Engagement,
        procedures: list[AuditProcedure],
        risks: list[AuditRisk],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.planning_service = planning_service
        self.engagement = engagement
        self.procedures = procedures
        self.risks = risks
        self.result_finding: AuditFinding | None = None

        self.setWindowTitle("Log Audit Finding — Exception Vault")
        self.resize(580, 520)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel(f"Log Audit Exception / Finding for FY {self.engagement.financial_year}")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Cut-Off Exception in Sales Invoices")

        self.proc_combo = QComboBox()
        self.proc_combo.addItem("-- Link Audit Procedure (Optional) --", None)
        for p in self.procedures:
            self.proc_combo.addItem(f"[{p.procedure_code}] {p.objective[:35]}...", p.id)

        self.risk_combo = QComboBox()
        self.risk_combo.addItem("-- Link Audit Risk (Optional) --", None)
        for r in self.risks:
            self.risk_combo.addItem(f"[{r.risk_code}] {r.title[:35]}...", r.id)

        self.category_input = QLineEdit()
        self.category_input.setText("Substantive Testing Exception")

        self.severity_combo = QComboBox()
        for s in RiskSeverityEnum:
            self.severity_combo.addItem(s.value, s)
        self.severity_combo.setCurrentText("High")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter monetary impact in INR (e.g. 150000.00)...")

        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("e.g. Sales Revenue / Trade Receivables")

        self.assertion_combo = QComboBox()
        for a in AssertionEnum:
            self.assertion_combo.addItem(a.value, a)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Detailed description of audit exception...")
        self.desc_input.setMaximumHeight(70)

        self.rec_input = QTextEdit()
        self.rec_input.setPlaceholderText("Auditor recommendation / management response...")
        self.rec_input.setMaximumHeight(60)

        form.addRow("Finding Title *:", self.title_input)
        form.addRow("Linked Procedure:", self.proc_combo)
        form.addRow("Linked Risk:", self.risk_combo)
        form.addRow("Severity:", self.severity_combo)
        form.addRow("Monetary Impact (INR):", self.amount_input)
        form.addRow("Affected Account:", self.account_input)
        form.addRow("Assertion:", self.assertion_combo)
        form.addRow("Description *:", self.desc_input)
        form.addRow("Recommendation:", self.rec_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Log Finding")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self) -> None:
        title = self.title_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        amt_str = self.amount_input.text().replace(",", "").strip()

        if not title or not desc:
            QMessageBox.warning(self, "Validation Error", "Please fill in Title and Description.")
            return

        amount_paise = None
        if amt_str:
            try:
                val = float(amt_str)
                amount_paise = int(round(val * 100))
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Invalid monetary impact amount.")
                return

        dto = CreateFindingDTO(
            engagement_id=self.engagement.id,
            procedure_id=self.proc_combo.currentData(),
            risk_id=self.risk_combo.currentData(),
            title=title,
            description=desc,
            category=self.category_input.text().strip(),
            severity=self.severity_combo.currentData(),
            amount_paise=amount_paise,
            affected_account=self.account_input.text().strip() or None,
            assertion=self.assertion_combo.currentData(),
            recommendation=self.rec_input.toPlainText().strip() or None,
            preparer="Auditor",
            source=FindingSourceEnum.MANUAL,
            is_ai_generated=False,
        )

        try:
            self.result_finding = self.planning_service.create_finding(dto)
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to log finding: {ex}")
