"""Engagement Close & Archival Wizard Dialog featuring readiness checklist and off-thread sealing."""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.archival_dtos import FreezeAndSealDTO, ReadinessCheckResultDTO
from finauditpro.application.services.archival_service import ArchivalService


class SealWorkerThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, archival_service: ArchivalService, dto: FreezeAndSealDTO) -> None:
        super().__init__()
        self.archival_service = archival_service
        self.dto = dto

    def run(self) -> None:
        try:
            archive = self.archival_service.freeze_and_seal_engagement(self.dto)
            self.finished_signal.emit(
                True,
                f"Engagement successfully frozen & sealed!\nArchive Path: {archive.archive_path}\nContent Hash: {archive.sealed_content_hash[:16]}...",
            )
        except Exception as ex:
            self.finished_signal.emit(False, str(ex))


class CloseWizardDialog(QDialog):
    """Wizard Dialog guiding auditors through pre-archive readiness checks and engagement sealing."""

    def __init__(
        self, archival_service: ArchivalService, engagement_id: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.archival_service = archival_service
        self.engagement_id = engagement_id
        self.readiness_result: ReadinessCheckResultDTO | None = None

        self.setWindowTitle("Engagement Close & Integrity Seal Wizard — FinAuditPro")
        self.resize(650, 520)
        self._init_ui()
        self._run_readiness_check()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header Notice
        header = QLabel("<h3>Engagement Close & Tamper-Evident Sealing Wizard</h3>")
        layout.addWidget(header)

        notice = QLabel(
            "<i>Notice: Sealing an audit file is an internal records-management control and tamper-evident integrity seal. "
            "It is NOT an IT Act 2000 Class 3 PKI DSC and NOT an ICAI UDIN.</i>"
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #4a5568; font-size: 11px; margin-bottom: 8px;")
        layout.addWidget(notice)

        # Checklist List Widget
        layout.addWidget(QLabel("<b>Pre-Archive Readiness Checklist:</b>"))
        self.checklist_widget = QListWidget()
        layout.addWidget(self.checklist_widget)

        # Form Inputs
        form_layout = QFormLayout()

        self.sealed_by_input = QLineEdit()
        self.sealed_by_input.setPlaceholderText("e.g. Audit Partner Name")
        form_layout.addRow("Sealed By (Auditor):", self.sealed_by_input)

        self.report_date_input = QLineEdit()
        self.report_date_input.setPlaceholderText("YYYY-MM-DD")
        self.report_date_input.setText("2026-03-31")
        form_layout.addRow("Audit Report Date:", self.report_date_input)

        self.passphrase_input = QLineEdit()
        self.passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase_input.setPlaceholderText("Optional archive encryption passphrase")
        form_layout.addRow("Archive Passphrase:", self.passphrase_input)

        self.override_input = QTextEdit()
        self.override_input.setMaximumHeight(60)
        self.override_input.setPlaceholderText(
            "Recorded justification required if soft warnings exist..."
        )
        form_layout.addRow("Override Justification:", self.override_input)

        layout.addLayout(form_layout)

        # Progress Bar & Buttons
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Freeze & Seal Engagement"
        )
        self.button_box.accepted.connect(self._on_seal_clicked)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _run_readiness_check(self) -> None:
        self.checklist_widget.clear()
        self.readiness_result = self.archival_service.run_readiness_check(self.engagement_id)

        for item in self.readiness_result.items:
            status_tag = (
                "[PASS]" if item.is_passed else ("[FAIL]" if item.is_hard_blocker else "[WARN]")
            )
            item_text = f"{status_tag} [{item.category}] {item.item_name}: {item.details}"
            list_item = QListWidgetItem(item_text)
            self.checklist_widget.addItem(list_item)

        if self.readiness_result.has_hard_failures:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            QMessageBox.critical(
                self,
                "Hard Readiness Failure",
                "Hard readiness check failures exist. You must resolve all hard blockers before sealing.",
            )

    def _on_seal_clicked(self) -> None:
        sealed_by = self.sealed_by_input.text().strip()
        if not sealed_by:
            QMessageBox.warning(
                self, "Validation Error", "Please enter auditor name in 'Sealed By'."
            )
            return

        report_date = self.report_date_input.text().strip()
        passphrase = self.passphrase_input.text().strip() or None
        override = self.override_input.toPlainText().strip() or None

        dto = FreezeAndSealDTO(
            engagement_id=self.engagement_id,
            sealed_by=sealed_by,
            report_date=report_date,
            passphrase=passphrase,
            override_justification=override,
        )

        self.button_box.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = SealWorkerThread(self.archival_service, dto)
        self.worker.finished_signal.connect(self._on_seal_finished)
        self.worker.start()

    def _on_seal_finished(self, success: bool, message: str) -> None:
        self.progress_bar.setVisible(False)
        self.button_box.setEnabled(True)

        if success:
            QMessageBox.information(self, "Engagement Sealed", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Sealing Failed", f"Failed to seal engagement:\n{message}")
