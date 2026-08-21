"""Engagement creation and editing dialog."""

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

from finauditpro.application.dtos import CreateEngagementDTO, UpdateEngagementDTO
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.domain.exceptions import DomainError


class EngagementDialog(QDialog):
    """Dialog for creating or updating audit engagements."""

    def __init__(
        self,
        engagement_service: EngagementService,
        firm: Firm,
        client: Client,
        engagement: Engagement | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        self.firm = firm
        self.client = client
        self.engagement = engagement
        self.result_engagement: Engagement | None = None

        self.setWindowTitle(
            "Edit Audit Engagement" if engagement else "Create New Audit Engagement"
        )
        self.setMinimumWidth(500)

        self._init_ui()
        if engagement:
            self._populate_fields(engagement)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"New Engagement for {self.client.name}")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.fy_input = QLineEdit()
        self.fy_input.setPlaceholderText("e.g. 2025-26")
        self.fy_input.setText("2025-26")

        self.audit_type_combo = QComboBox()
        for at in AuditTypeEnum:
            self.audit_type_combo.addItem(at.value, at)

        self.status_combo = QComboBox()
        for st in EngagementStatusEnum:
            self.status_combo.addItem(st.value, st)

        self.team_input = QLineEdit()
        self.team_input.setPlaceholderText("e.g. Partner, Manager, Senior (comma separated)")
        self.team_input.setText("Partner, Senior Auditor")

        form_layout.addRow("Financial Year *:", self.fy_input)
        form_layout.addRow("Audit Type:", self.audit_type_combo)
        form_layout.addRow("Initial Status:", self.status_combo)
        form_layout.addRow("Assigned Team:", self.team_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Engagement")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_fields(self, engagement: Engagement) -> None:
        self.fy_input.setText(engagement.financial_year)
        idx_at = self.audit_type_combo.findData(engagement.audit_type)
        if idx_at >= 0:
            self.audit_type_combo.setCurrentIndex(idx_at)
        idx_st = self.status_combo.findData(engagement.status)
        if idx_st >= 0:
            self.status_combo.setCurrentIndex(idx_st)
        self.team_input.setText(", ".join(engagement.assigned_team))

    def _save(self) -> None:
        fy = self.fy_input.text().strip()
        if not fy:
            QMessageBox.warning(self, "Validation Error", "Financial Year is required.")
            return

        audit_type = self.audit_type_combo.currentData()
        status = self.status_combo.currentData()
        raw_team = self.team_input.text().strip()
        assigned_team = [t.strip() for t in raw_team.split(",") if t.strip()]

        try:
            if self.engagement:
                update_dto = UpdateEngagementDTO(
                    financial_year=fy,
                    audit_type=audit_type,
                    status=status,
                    assigned_team=assigned_team,
                )
                self.result_engagement = self.engagement_service.update_engagement(
                    self.engagement.id, update_dto
                )
            else:
                create_dto = CreateEngagementDTO(
                    firm_id=self.firm.id,
                    client_id=self.client.id,
                    financial_year=fy,
                    audit_type=audit_type,
                    status=status,
                    assigned_team=assigned_team,
                )
                self.result_engagement = self.engagement_service.create_engagement(create_dto)

            self.accept()
        except DomainError as err:
            QMessageBox.warning(self, "Validation Error", str(err))
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to save engagement: {ex}")
