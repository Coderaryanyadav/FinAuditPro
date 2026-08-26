"""Client creation and editing dialog."""

from PySide6.QtCore import Qt
from finauditpro.ui.widgets.custom_combo import CustomComboBox
from finauditpro.ui.widgets.custom_combo import CustomComboBox
from PySide6.QtWidgets import (
    QComboBox,
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

from finauditpro.application.dtos import CreateClientDTO, UpdateClientDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.domain.entities import Client, EntityTypeEnum, Firm
from finauditpro.domain.exceptions import DomainError


class ClientDialog(QDialog):
    """Dialog for creating or updating client entity details."""

    def __init__(
        self,
        client_service: ClientService,
        firm: Firm,
        client: Client | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.firm = firm
        self.client = client
        self.result_client: Client | None = None

        self.setWindowTitle("Edit Client" if client else "Create New Client")
        self.setMinimumWidth(620)
        self.resize(640, 580)

        self._init_ui()
        if client:
            self._populate_fields(client)

    def _init_ui(self) -> None:
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 28)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel(f"Client Profile — {self.firm.name}")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        subtitle = QLabel("Enter audited entity legal details, corporate identification, and finance contacts.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B;")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(14)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        field_style = """
            QLineEdit, QComboBox {
                border: 1.5px solid #CBD5E1; border-radius: 6px;
                padding: 9px 14px; font-size: 13px; color: #0F172A; background: #FFFFFF;
                min-width: 380px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #2563EB; background: #FFFFFF; }
            QLineEdit::placeholder { color: #94A3B8; }
        """
        lbl_style = "font-size: 13px; font-weight: 600; color: #334155;"

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Reliance Green Tech Pvt Ltd")
        self.name_input.setStyleSheet(field_style)

        self.entity_type_combo = CustomComboBox()
        for et in EntityTypeEnum:
            self.entity_type_combo.addItem(et.value, et)
        self.entity_type_combo.setStyleSheet(field_style)

        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AABCR9876E")
        self.pan_input.setStyleSheet(field_style)

        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 27AABCR9876E1Z5")
        self.gstin_input.setStyleSheet(field_style)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Registered Address")
        self.address_input.setStyleSheet(field_style)

        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g. Information Technology / Manufacturing")
        self.industry_input.setStyleSheet(field_style)

        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("CFO / Finance Head")
        self.contact_person_input.setStyleSheet(field_style)

        self.contact_email_input = QLineEdit()
        self.contact_email_input.setPlaceholderText("finance@client.com")
        self.contact_email_input.setStyleSheet(field_style)

        def make_lbl(txt: str) -> QLabel:
            lbl = QLabel(txt)
            lbl.setStyleSheet(lbl_style)
            return lbl

        form_layout.addRow(make_lbl("Client Name *:"), self.name_input)
        form_layout.addRow(make_lbl("Entity Type:"), self.entity_type_combo)
        form_layout.addRow(make_lbl("Client PAN:"), self.pan_input)
        form_layout.addRow(make_lbl("Client GSTIN:"), self.gstin_input)
        form_layout.addRow(make_lbl("Address:"), self.address_input)
        form_layout.addRow(make_lbl("Industry:"), self.industry_input)
        form_layout.addRow(make_lbl("Contact Person:"), self.contact_person_input)
        form_layout.addRow(make_lbl("Contact Email:"), self.contact_email_input)

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

        save_btn = QPushButton("Save Client")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 600;
                border: none; border-radius: 6px; padding: 9px 24px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:pressed { background: #1E40AF; }
        """)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_fields(self, client: Client) -> None:
        self.name_input.setText(client.name)
        idx = self.entity_type_combo.findData(client.entity_type)
        if idx >= 0:
            self.entity_type_combo.setCurrentIndex(idx)
        self.pan_input.setText(client.pan or "")
        self.gstin_input.setText(client.gstin or "")
        self.address_input.setText(client.registered_address or "")
        self.industry_input.setText(client.industry or "")
        self.contact_person_input.setText(client.contact_person or "")
        self.contact_email_input.setText(client.contact_email or "")

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Client Name is required.")
            return

        entity_type = self.entity_type_combo.currentData()
        pan = self.pan_input.text().strip() or None
        gstin = self.gstin_input.text().strip() or None
        address = self.address_input.text().strip() or None
        industry = self.industry_input.text().strip() or None
        cperson = self.contact_person_input.text().strip() or None
        cemail = self.contact_email_input.text().strip() or None

        try:
            if self.client:
                update_dto = UpdateClientDTO(
                    name=name,
                    entity_type=entity_type,
                    pan=pan,
                    gstin=gstin,
                    registered_address=address,
                    industry=industry,
                    contact_person=cperson,
                    contact_email=cemail,
                )
                self.result_client = self.client_service.update_client(self.client.id, update_dto)
            else:
                create_dto = CreateClientDTO(
                    firm_id=self.firm.id,
                    name=name,
                    entity_type=entity_type,
                    pan=pan,
                    gstin=gstin,
                    registered_address=address,
                    industry=industry,
                    contact_person=cperson,
                    contact_email=cemail,
                )
                self.result_client = self.client_service.create_client(create_dto)

            self.accept()
        except DomainError as err:
            QMessageBox.warning(self, "Validation Error", str(err))
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to save client: {ex}")
