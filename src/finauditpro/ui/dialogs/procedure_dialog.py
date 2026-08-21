"""Dialog for creating and configuring Audit Procedures."""

from PySide6.QtWidgets import (
    QCheckBox,
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

from finauditpro.application.audit_planning_dtos import CreateProcedureDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.domain.audit_matrix_entities import AssertionEnum, AuditProcedure, AuditRisk
from finauditpro.domain.entities import Engagement


class ProcedureDialog(QDialog):
    """Modal dialog for creating an Audit Procedure."""

    def __init__(
        self,
        planning_service: AuditPlanningService,
        engagement: Engagement,
        risks: list[AuditRisk],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.planning_service = planning_service
        self.engagement = engagement
        self.risks = risks
        self.result_procedure: AuditProcedure | None = None

        self.setWindowTitle("New Audit Procedure — Execution Plan")
        self.resize(600, 500)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel(f"Create Audit Procedure for FY {self.engagement.financial_year}")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        form = QFormLayout()

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("e.g. PROC-REV-01")

        self.type_combo = QComboBox()
        self.type_combo.addItems(
            [
                "Substantive Test of Details",
                "Substantive Analytical Procedure",
                "Test of Controls",
                "Inspection of Documents",
                "Observation",
                "External Confirmation",
                "Recalculation / Re-performance",
            ]
        )

        self.objective_input = QTextEdit()
        self.objective_input.setPlaceholderText("Objective of procedure...")
        self.objective_input.setMaximumHeight(60)

        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText("Step-by-step testing instructions...")
        self.instructions_input.setMaximumHeight(70)

        form.addRow("Procedure Code *:", self.code_input)
        form.addRow("Procedure Type:", self.type_combo)
        form.addRow("Objective *:", self.objective_input)
        form.addRow("Instructions:", self.instructions_input)

        layout.addLayout(form)

        # Linked Risks Checkboxes
        risk_label = QLabel("Linked Audit Risks:")
        risk_label.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        layout.addWidget(risk_label)

        self.risk_boxes: list[tuple[str, QCheckBox]] = []
        risk_layout = QVBoxLayout()
        for r in self.risks[:4]:
            cb = QCheckBox(f"[{r.risk_code}] {r.title}")
            risk_layout.addWidget(cb)
            self.risk_boxes.append((r.id, cb))
        layout.addLayout(risk_layout)

        # Assertion Checkboxes
        ass_label = QLabel("Target Assertions:")
        ass_label.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        layout.addWidget(ass_label)

        ass_layout = QHBoxLayout()
        self.assertion_boxes: list[tuple[AssertionEnum, QCheckBox]] = []
        for a in list(AssertionEnum)[:4]:
            cb = QCheckBox(a.value)
            cb.setChecked(a == AssertionEnum.COMPLETENESS)
            ass_layout.addWidget(cb)
            self.assertion_boxes.append((a, cb))
        layout.addLayout(ass_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Procedure")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self) -> None:
        code = self.code_input.text().strip()
        obj = self.objective_input.toPlainText().strip()

        if not code or not obj:
            QMessageBox.warning(
                self, "Validation Error", "Please fill in Procedure Code and Objective."
            )
            return

        linked_risk_ids = [r_id for r_id, cb in self.risk_boxes if cb.isChecked()]
        selected_assertions = [a for a, cb in self.assertion_boxes if cb.isChecked()]
        if not selected_assertions:
            selected_assertions = [AssertionEnum.COMPLETENESS]

        dto = CreateProcedureDTO(
            engagement_id=self.engagement.id,
            procedure_code=code,
            objective=obj,
            procedure_type=self.type_combo.currentText(),
            instructions=self.instructions_input.toPlainText().strip(),
            linked_risk_ids=linked_risk_ids,
            assertions=selected_assertions,
            preparer="Auditor",
        )

        try:
            self.result_procedure = self.planning_service.create_procedure(dto)
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to save procedure: {ex}")
