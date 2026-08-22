"""Multi-Year Engagement Roll-Forward Wizard Dialog."""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.roll_forward_dtos import ExecuteRollForwardDTO
from finauditpro.application.services.roll_forward_service import RollForwardService


class RollForwardWorkerThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, service: RollForwardService, dto: ExecuteRollForwardDTO) -> None:
        super().__init__()
        self.service = service
        self.dto = dto

    def run(self) -> None:
        try:
            new_eng = self.service.roll_forward_engagement(self.dto)
            self.finished_signal.emit(
                True,
                f"Successfully created new engagement for FY {new_eng.financial_year}!\nEngagement ID: {new_eng.id}",
            )
        except Exception as ex:
            self.finished_signal.emit(False, str(ex))


class RollForwardWizardDialog(QDialog):
    """Wizard guiding auditors through multi-year roll-forward options and draft creation."""

    def __init__(
        self,
        roll_forward_service: RollForwardService,
        source_engagement_id: str,
        source_fy: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.roll_forward_service = roll_forward_service
        self.source_engagement_id = source_engagement_id
        self.source_fy = source_fy

        self.setWindowTitle(f"Roll Forward Audit Engagement — FY {source_fy}")
        self.resize(560, 420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel(f"<h3>Roll Forward Engagement from FY {self.source_fy}</h3>")
        layout.addWidget(header)

        notice = QLabel(
            "<i>Notice: Roll-forward creates a new engagement for the next FY for the same client. "
            "Re-usable items are carried as DRAFTS marked for review. Prior conclusions and sign-offs are NEVER carried.</i>"
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            "color: #2b6cb0; background-color: #ebf8ff; padding: 6px; border-radius: 4px;"
        )
        layout.addWidget(notice)

        form = QFormLayout()

        self.fy_input = QLineEdit()
        self.fy_input.setText("2026-27")
        self.fy_input.setPlaceholderText("Target FY (e.g. 2026-27)")
        form.addRow("Target Financial Year:", self.fy_input)

        self.auditor_input = QLineEdit()
        self.auditor_input.setPlaceholderText("e.g. Senior Auditor Name")
        form.addRow("Performed By (Auditor):", self.auditor_input)

        layout.addLayout(form)

        layout.addWidget(QLabel("<b>Select Items to Roll Forward (as Drafts for Review):</b>"))

        self.chk_perm_docs = QCheckBox("Permanent File Documents (M2)")
        self.chk_perm_docs.setChecked(True)
        layout.addWidget(self.chk_perm_docs)

        self.chk_risks = QCheckBox("Risk Register (M4) — ratings reset to unassessed draft")
        self.chk_risks.setChecked(True)
        layout.addWidget(self.chk_risks)

        self.chk_materiality = QCheckBox(
            "Materiality Benchmark Methodology (M4) — method carried, amounts zeroed"
        )
        self.chk_materiality.setChecked(True)
        layout.addWidget(self.chk_materiality)

        self.chk_procedures = QCheckBox("Audit Procedure Templates (M4)")
        self.chk_procedures.setChecked(True)
        layout.addWidget(self.chk_procedures)

        self.chk_findings = QCheckBox(
            "Carried-Forward Findings (M4/M5) — preserving AI badges & citations"
        )
        self.chk_findings.setChecked(True)
        layout.addWidget(self.chk_findings)

        self.chk_opening_balances = QCheckBox(
            "SA 510 Opening Balances — link to prior audited closing balances"
        )
        self.chk_opening_balances.setChecked(True)
        layout.addWidget(self.chk_opening_balances)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Execute Roll-Forward")
        self.button_box.accepted.connect(self._on_execute_clicked)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _on_execute_clicked(self) -> None:
        target_fy = self.fy_input.text().strip()
        auditor = self.auditor_input.text().strip()

        if not target_fy or not auditor:
            QMessageBox.warning(
                self, "Validation Error", "Please provide Target Financial Year and Auditor Name."
            )
            return

        dto = ExecuteRollForwardDTO(
            source_engagement_id=self.source_engagement_id,
            target_financial_year=target_fy,
            performed_by=auditor,
            carry_permanent_documents=self.chk_perm_docs.isChecked(),
            carry_risk_register=self.chk_risks.isChecked(),
            carry_materiality_methodology=self.chk_materiality.isChecked(),
            carry_procedures=self.chk_procedures.isChecked(),
            carry_findings=self.chk_findings.isChecked(),
            link_opening_balances=self.chk_opening_balances.isChecked(),
        )

        self.button_box.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = RollForwardWorkerThread(self.roll_forward_service, dto)
        self.worker.finished_signal.connect(self._on_roll_forward_finished)
        self.worker.start()

    def _on_roll_forward_finished(self, success: bool, message: str) -> None:
        self.progress_bar.setVisible(False)
        self.button_box.setEnabled(True)

        if success:
            QMessageBox.information(self, "Roll-Forward Complete", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Roll-Forward Failed", message)
