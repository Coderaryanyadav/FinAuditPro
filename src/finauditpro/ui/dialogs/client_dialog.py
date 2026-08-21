"""Client creation and editing dialog."""

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
        self.setMinimumWidth(500)

        self._init_ui()
        if client:
            self._populate_fields(client)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"Client Profile ({self.firm.name})")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Reliance Green Tech Pvt Ltd")

        self.entity_type_combo = QComboBox()
        for et in EntityTypeEnum:
            self.entity_type_combo.addItem(et.value, et)

        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AABCR9876E")

        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 27AABCR9876E1Z5")

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Registered Address")

        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g. Information Technology / Manufacturing")

        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("CFO / Finance Head")

        self.contact_email_input = QLineEdit()
        self.contact_email_input.setPlaceholderText("finance@client.com")

        form_layout.addRow("Client Name *:", self.name_input)
        form_layout.addRow("Entity Type:", self.entity_type_combo)
        form_layout.addRow("Client PAN:", self.pan_input)
        form_layout.addRow("Client GSTIN:", self.gstin_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Industry:", self.industry_input)
        form_layout.addRow("Contact Person:", self.contact_person_input)
        form_layout.addRow("Contact Email:", self.contact_email_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Client")
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
