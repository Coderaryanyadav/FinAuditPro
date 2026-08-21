"""Firm creation and editing dialog."""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos import CreateFirmDTO, UpdateFirmDTO
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.entities import Firm
from finauditpro.domain.exceptions import DomainError


class FirmDialog(QDialog):
    """Dialog for creating or updating audit firm details."""

    def __init__(
        self, firm_service: FirmService, firm: Firm | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.firm_service = firm_service
        self.firm = firm
        self.result_firm: Firm | None = None

        self.setWindowTitle("Edit Audit Firm" if firm else "Create New Audit Firm")
        self.setMinimumWidth(480)

        self._init_ui()
        if firm:
            self._populate_fields(firm)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Audit Firm Details")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Apex Audit & Co.")

        self.reg_input = QLineEdit()
        self.reg_input.setPlaceholderText("e.g. 123456N (ICAI Firm Reg. No.)")

        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AAACC1234D")

        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 27AAACC1234D1Z5")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Registered Office Address")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+91 98765 43210")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("contact@apexaudit.in")

        form_layout.addRow("Firm Name *:", self.name_input)
        form_layout.addRow("FRN / Reg No:", self.reg_input)
        form_layout.addRow("Firm PAN:", self.pan_input)
        form_layout.addRow("Firm GSTIN:", self.gstin_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Firm")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_fields(self, firm: Firm) -> None:
        self.name_input.setText(firm.name)
        self.reg_input.setText(firm.registration_number or "")
        self.pan_input.setText(firm.pan or "")
        self.gstin_input.setText(firm.gstin or "")
        self.address_input.setText(firm.address or "")
        self.phone_input.setText(firm.phone or "")
        self.email_input.setText(firm.email or "")

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Firm Name is required.")
            return

        reg = self.reg_input.text().strip() or None
        pan = self.pan_input.text().strip() or None
        gstin = self.gstin_input.text().strip() or None
        address = self.address_input.text().strip() or None
        phone = self.phone_input.text().strip() or None
        email = self.email_input.text().strip() or None

        try:
            if self.firm:
                update_dto = UpdateFirmDTO(
                    name=name,
                    registration_number=reg,
                    pan=pan,
                    gstin=gstin,
                    address=address,
                    phone=phone,
                    email=email,
                )
                self.result_firm = self.firm_service.update_firm(self.firm.id, update_dto)
            else:
                create_dto = CreateFirmDTO(
                    name=name,
                    registration_number=reg,
                    pan=pan,
                    gstin=gstin,
                    address=address,
                    phone=phone,
                    email=email,
                )
                self.result_firm = self.firm_service.create_firm(create_dto)

            self.accept()
        except DomainError as err:
            QMessageBox.warning(self, "Validation Error", str(err))
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to save firm: {ex}")
