"""Initial launch Onboarding Wizard Dialog for setting up Firm and Partner profile."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from finauditpro.application.dtos import CreateFirmDTO
from finauditpro.application.services.firm_service import FirmService


class OnboardingDialog(QDialog):
    """First-run onboarding dialog creating initial Firm and Partner profile."""

    def __init__(self, firm_service: FirmService, parent=None) -> None:
        super().__init__(parent)
        self.firm_service = firm_service

        self.setWindowTitle("Welcome to FinAuditPro — Initial Setup Wizard")
        self.resize(500, 320)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<h3>Welcome to FinAuditPro</h3>")
        layout.addWidget(header)

        notice = QLabel(
            "<b>Offline & Air-Gapped Posture:</b> FinAuditPro runs 100% locally on your machine. "
            "All audit documentation, financial records, and vector search indices remain securely on this device."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            "color: #276749; background-color: #f0fff4; padding: 8px; border-radius: 4px; border: 1px solid #9ae6b4;"
        )
        layout.addWidget(notice)

        form = QFormLayout()

        self.firm_name_input = QLineEdit()
        self.firm_name_input.setPlaceholderText(
            "e.g. M/s Sharma & Associates, Chartered Accountants"
        )
        form.addRow("Audit Firm Name:", self.firm_name_input)

        self.icai_number_input = QLineEdit()
        self.icai_number_input.setPlaceholderText("e.g. 123456N")
        form.addRow("ICAI Firm Reg. No. (FRN):", self.icai_number_input)

        self.partner_name_input = QLineEdit()
        self.partner_name_input.setPlaceholderText("e.g. CA Rajesh Sharma")
        form.addRow("Senior Partner Name:", self.partner_name_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Partner", "Manager", "Senior"])
        form.addRow("Default User Role:", self.role_combo)

        layout.addLayout(form)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Initialize Workspace")
        button_box.accepted.connect(self._on_submit)
        layout.addWidget(button_box)

    def _on_submit(self) -> None:
        firm_name = self.firm_name_input.text().strip()
        partner = self.partner_name_input.text().strip()

        if not firm_name or not partner:
            QMessageBox.warning(
                self, "Validation Error", "Firm Name and Senior Partner Name are required."
            )
            return

        try:
            self.firm_service.create_firm(CreateFirmDTO(name=firm_name))
            QMessageBox.information(
                self,
                "Setup Complete",
                f"Workspace initialized for '{firm_name}'. Welcome, {partner}!",
            )
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Setup Failed", str(ex))
