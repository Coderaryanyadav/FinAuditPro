"""Engagement creation and editing dialog."""

from PySide6.QtCore import Qt
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
        self.setMinimumWidth(620)
        self.resize(640, 500)

        self._init_ui()
        if engagement:
            self._populate_fields(engagement)

    def _init_ui(self) -> None:
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 28)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel(f"New Audit Engagement — {self.client.name}")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        subtitle = QLabel("Configure financial year, statutory audit scope, and assigned team members.")
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

        self.fy_input = QLineEdit()
        self.fy_input.setPlaceholderText("e.g. 2025-26")
        self.fy_input.setText("2025-26")
        self.fy_input.setStyleSheet(field_style)

        self.audit_type_combo = QComboBox()
        for at in AuditTypeEnum:
            self.audit_type_combo.addItem(at.value, at)
        self.audit_type_combo.setStyleSheet(field_style)

        self.status_combo = QComboBox()
        for st in EngagementStatusEnum:
            self.status_combo.addItem(st.value, st)
        self.status_combo.setStyleSheet(field_style)

        self.team_input = QLineEdit()
        self.team_input.setPlaceholderText("e.g. Partner, Manager, Senior (comma separated)")
        self.team_input.setText("Partner, Senior Auditor")
        self.team_input.setStyleSheet(field_style)

        def make_lbl(txt: str) -> QLabel:
            lbl = QLabel(txt)
            lbl.setStyleSheet(lbl_style)
            return lbl

        form_layout.addRow(make_lbl("Financial Year *:"), self.fy_input)
        form_layout.addRow(make_lbl("Audit Type:"), self.audit_type_combo)
        form_layout.addRow(make_lbl("Initial Status:"), self.status_combo)
        form_layout.addRow(make_lbl("Assigned Team:"), self.team_input)

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

        save_btn = QPushButton("Save Engagement")
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
