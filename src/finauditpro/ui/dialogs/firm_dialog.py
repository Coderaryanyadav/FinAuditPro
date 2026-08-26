"""Firm creation and editing dialog."""

from PySide6.QtCore import Qt
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
        self.setMinimumWidth(620)
        self.resize(640, 560)

        self._init_ui()
        if firm:
            self._populate_fields(firm)

    def _init_ui(self) -> None:
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 28)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("Audit Firm Details")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        subtitle = QLabel("Enter ICAI Firm Registration Number (FRN), tax identifiers, and contact coordinates.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(14)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        field_style = """
            QLineEdit {
                border: 1.5px solid #CBD5E1; border-radius: 6px;
                padding: 9px 14px; font-size: 13px; color: #0F172A; background: #FFFFFF;
                min-width: 380px;
            }
            QLineEdit:focus { border-color: #2563EB; background: #FFFFFF; }
            QLineEdit::placeholder { color: #94A3B8; }
        """
        lbl_style = "font-size: 13px; font-weight: 600; color: #334155;"

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Apex Audit & Co.")
        self.name_input.setStyleSheet(field_style)

        self.reg_input = QLineEdit()
        self.reg_input.setPlaceholderText("e.g. 123456N (ICAI Firm Reg. No.)")
        self.reg_input.setStyleSheet(field_style)

        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AAACC1234D")
        self.pan_input.setStyleSheet(field_style)

        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 27AAACC1234D1Z5")
        self.gstin_input.setStyleSheet(field_style)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Registered Office Address")
        self.address_input.setStyleSheet(field_style)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+91 98765 43210")
        self.phone_input.setStyleSheet(field_style)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("contact@apexaudit.in")
        self.email_input.setStyleSheet(field_style)

        def make_lbl(txt: str) -> QLabel:
            lbl = QLabel(txt)
            lbl.setStyleSheet(lbl_style)
            return lbl

        form_layout.addRow(make_lbl("Firm Name *:"), self.name_input)
        form_layout.addRow(make_lbl("FRN / Reg No:"), self.reg_input)
        form_layout.addRow(make_lbl("Firm PAN:"), self.pan_input)
        form_layout.addRow(make_lbl("Firm GSTIN:"), self.gstin_input)
        form_layout.addRow(make_lbl("Address:"), self.address_input)
        form_layout.addRow(make_lbl("Phone:"), self.phone_input)
        form_layout.addRow(make_lbl("Email:"), self.email_input)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F1F5F9; color: #475569; font-size: 13px; font-weight: 600;
                border: 1px solid #CBD5E1; border-radius: 6px; padding: 9px 20px;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Firm")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 600;
                border: 1px solid transparent; border-radius: 6px; padding: 9px 24px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
        """)
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
