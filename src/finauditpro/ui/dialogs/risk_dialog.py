"""Dialog for creating and editing Audit Risks."""

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

from finauditpro.application.audit_planning_dtos import CreateRiskDTO
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.domain.audit_matrix_entities import AssertionEnum, AuditRisk, RiskSeverityEnum
from finauditpro.domain.entities import Engagement


class RiskDialog(QDialog):
    """Modal dialog for creating an Audit Risk entity."""

    def __init__(
        self,
        planning_service: AuditPlanningService,
        engagement: Engagement,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.planning_service = planning_service
        self.engagement = engagement
        self.result_risk: AuditRisk | None = None

        self.setWindowTitle("New Audit Risk — Risk Register")
        self.resize(600, 520)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel(f"Identify Audit Risk for FY {self.engagement.financial_year}")
        header.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        form = QFormLayout()

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("e.g. RSK-REV-01")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Unrecorded Revenue Outliers")

        self.category_input = QLineEdit()
        self.category_input.setText("Revenue & Statutory Compliance")

        self.inherent_combo = QComboBox()
        for s in RiskSeverityEnum:
            self.inherent_combo.addItem(s.value, s)
        self.inherent_combo.setCurrentText("High")

        self.control_combo = QComboBox()
        for s in RiskSeverityEnum:
            self.control_combo.addItem(s.value, s)
        self.control_combo.setCurrentText("Medium")

        self.sig_check = QCheckBox("Mark as Significant Risk (SA 315)")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Describe risk of material misstatement...")
        self.desc_input.setMaximumHeight(70)

        self.response_input = QTextEdit()
        self.response_input.setPlaceholderText("Detail planned audit procedure response...")
        self.response_input.setMaximumHeight(70)

        form.addRow("Risk Code *:", self.code_input)
        form.addRow("Risk Title *:", self.title_input)
        form.addRow("Risk Category *:", self.category_input)
        form.addRow("Inherent Risk:", self.inherent_combo)
        form.addRow("Control Risk:", self.control_combo)
        form.addRow("Significant Risk:", self.sig_check)
        form.addRow("Description *:", self.desc_input)
        form.addRow("Audit Response:", self.response_input)

        layout.addLayout(form)

        # Assertion Checkboxes
        ass_label = QLabel("Affected Assertions:")
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

        ass_layout2 = QHBoxLayout()
        for a in list(AssertionEnum)[4:]:
            cb = QCheckBox(a.value)
            ass_layout2.addWidget(cb)
            self.assertion_boxes.append((a, cb))
        layout.addLayout(ass_layout2)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Risk")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self) -> None:
        code = self.code_input.text().strip()
        title = self.title_input.text().strip()
        cat = self.category_input.text().strip()
        desc = self.desc_input.toPlainText().strip()

        if not code or not title or not cat or not desc:
            QMessageBox.warning(
                self, "Validation Error", "Please fill in all required fields marked with *."
            )
            return

        selected_assertions = [a for a, cb in self.assertion_boxes if cb.isChecked()]
        if not selected_assertions:
            selected_assertions = [AssertionEnum.COMPLETENESS]

        dto = CreateRiskDTO(
            engagement_id=self.engagement.id,
            risk_code=code,
            title=title,
            category=cat,
            description=desc,
            assertions=selected_assertions,
            inherent_risk=self.inherent_combo.currentData(),
            control_risk=self.control_combo.currentData(),
            is_significant_risk=self.sig_check.isChecked(),
            planned_response=self.response_input.toPlainText().strip(),
        )

        try:
            self.result_risk = self.planning_service.create_risk(dto)
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to save risk: {ex}")
