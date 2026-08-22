"""
Engagement Archival & Retention Control Workspace View for FinAuditPro.
Manages 7-year SA 230 audit file retention, cryptographic sealing, and partner authorization for reopening.
"""

from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.archival_dtos import ReopenEngagementDTO
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.ui.dialogs.close_wizard_dialog import CloseWizardDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget


class ReopenDialog(QDialog):
    """Dialog prompting for Partner RBAC verification and justification reason to reopen sealed engagement."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Reopen Sealed Engagement — Partner Auth Required")
        self.resize(480, 260)
        self._init_ui()


    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<b>Reopen Sealed Audit Engagement</b>")
        header.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        layout.addWidget(header)

        notice = QLabel(
            "Notice: Reopening a sealed audit engagement requires Partner role authorization. "
            "The prior sealed archive is preserved intact in the audit trail."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            "color: #B45309; background-color: #FEF3C7; padding: 8px; border-radius: 6px; font-size: 11px;"
        )
        layout.addWidget(notice)

        form = QFormLayout()
        self.partner_name_input = QLineEdit()
        self.partner_name_input.setPlaceholderText("Audit Partner Name")
        form.addRow("Partner Name:", self.partner_name_input)

        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Detailed audit reason for reopening file...")
        form.addRow("Reopen Reason:", self.reason_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        confirm_btn = QPushButton("Authorize & Reopen")
        confirm_btn.setStyleSheet(
            "background-color: #DC2626; color: white; font-weight: 600; padding: 6px 14px; border-radius: 6px;"
        )
        confirm_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)


class ArchivalView(QWidget):
    """Workspace view displaying retention timelines, readiness status, sealed archives, and reopen triggers."""

    def __init__(self, db_manager: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.db_manager = db_manager
        self.archival_service = ArchivalService(db_manager)
        self.current_engagement_id: str | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background: transparent; border: none;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(2)
        title = QLabel("File Archival & Retention")
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; border: none; background: transparent;"
        )
        subtitle = QLabel(
            "Manage 7-year audit file retention (SA 230), sealing, and partner reopening controls."
        )
        subtitle.setStyleSheet(
            "font-size: 12px; color: #64748B; border: none; background: transparent;"
        )
        left_v.addWidget(title)
        left_v.addWidget(subtitle)
        hdr_layout.addLayout(left_v)
        hdr_layout.addStretch()

        self.close_wizard_btn = QPushButton("🔒 Close & Seal Engagement")
        self.close_wizard_btn.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 16px; border: none; } QPushButton:hover { background-color: #1D4ED8; }"
        )
        self.close_wizard_btn.clicked.connect(self._open_close_wizard)
        hdr_layout.addWidget(self.close_wizard_btn)

        self.reopen_btn = QPushButton("🔓 Reopen File (Partner)")
        self.reopen_btn.setStyleSheet(
            "QPushButton { background-color: #B45309; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 16px; border: none; } QPushButton:hover { background-color: #92400E; }"
        )
        self.reopen_btn.clicked.connect(self._open_reopen_dialog)
        hdr_layout.addWidget(self.reopen_btn)
        layout.addWidget(hdr_frame)

        # 2. Status & Retention Banner Card
        banner_card = CardWidget("RETENTION POLICY & FILE STATUS (SA 230)")
        b_layout = QVBoxLayout()
        b_layout.setSpacing(4)
        self.status_banner_label = QLabel("Engagement Status: Active")
        self.status_banner_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #0F172A; border: none; background: transparent;"
        )
        self.timeline_banner_label = QLabel(
            "Retention Policy: Assembly Period: 60 Days | Retention Period: 7 Years (Source: SA 230 Guidance)"
        )
        self.timeline_banner_label.setStyleSheet(
            "font-size: 11px; color: #64748B; border: none; background: transparent;"
        )
        b_layout.addWidget(self.status_banner_label)
        b_layout.addWidget(self.timeline_banner_label)
        banner_card.content_layout.addLayout(b_layout)
        layout.addWidget(banner_card)

        # 3. Sealed Archives Table Card & Empty State
        self.table_card = CardWidget("SEALED AUDIT ARCHIVES & INTEGRITY HASHES")
        self.archives_table = QTableWidget()
        self.archives_table.setColumnCount(6)
        self.archives_table.setHorizontalHeaderLabels(
            [
                "ARCHIVE ID",
                "REPORT DATE",
                "ASSEMBLY DEADLINE",
                "RETAIN UNTIL",
                "ENCRYPTED",
                "SEALED HASH",
            ]
        )
        self.archives_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.archives_table.verticalHeader().setVisible(False)
        self.archives_table.setAlternatingRowColors(True)

        self.empty_state = EmptyStateWidget(
            title="No sealed archives exist for this engagement",
            description="When all audit procedures and review signoffs are finished, use the Close & Seal wizard to generate a tamper-evident archive.",
            action_text="🔒 Close & Seal Engagement",
            action_callback=self._open_close_wizard,
        )

        self.table_card.content_layout.addWidget(self.archives_table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

    def set_active_engagement(self, engagement: Any) -> None:
        if hasattr(engagement, "id"):
            self.load_engagement(engagement.id)
        elif engagement:
            self.load_engagement(str(engagement))
        else:
            self.current_engagement_id = None
            self._refresh_view()

    def load_engagement(self, engagement_id: str) -> None:
        self.current_engagement_id = engagement_id
        self._refresh_view()


    def _refresh_view(self) -> None:
        if not self.current_engagement_id:
            self.archives_table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        ret_cfg = self.archival_service.get_or_create_retention_config()
        self.timeline_banner_label.setText(
            f"Retention Policy: Assembly Period: {ret_cfg.assembly_period_days} Days | "
            f"Retention Period: {ret_cfg.retention_period_years} Years (Source: {ret_cfg.source})"
        )

        status_str = self.archival_service.get_engagement_status(self.current_engagement_id)
        self.status_banner_label.setText(f"Engagement Status: {status_str}")

        if status_str == "Archived":
            self.close_wizard_btn.setEnabled(False)
            self.reopen_btn.setEnabled(True)
        else:
            self.close_wizard_btn.setEnabled(True)
            self.reopen_btn.setEnabled(False)

        archives = self.archival_service.list_archives_for_engagement(self.current_engagement_id)
        if not archives:
            self.archives_table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.archives_table.setVisible(True)
        self.empty_state.setVisible(False)
        self.archives_table.setRowCount(len(archives))

        for row, arch in enumerate(archives):
            self.archives_table.setItem(row, 0, QTableWidgetItem(arch.id[:8]))
            self.archives_table.setItem(row, 1, QTableWidgetItem(arch.report_date))
            self.archives_table.setItem(row, 2, QTableWidgetItem(arch.assembly_deadline))
            self.archives_table.setItem(row, 3, QTableWidgetItem(arch.retain_until))
            self.archives_table.setItem(
                row, 4, QTableWidgetItem("● Yes" if arch.is_encrypted else "No")
            )
            self.archives_table.setItem(
                row, 5, QTableWidgetItem(f"{arch.sealed_content_hash[:16]}...")
            )

        self.archives_table.setFixedHeight(max(1, len(archives)) * 36 + 32)

    def _open_close_wizard(self) -> None:
        if not self.current_engagement_id:
            QMessageBox.warning(self, "No Engagement", "Please select an engagement first.")
            return

        dlg = CloseWizardDialog(self.archival_service, self.current_engagement_id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_view()

    def _open_reopen_dialog(self) -> None:
        if not self.current_engagement_id:
            return

        dlg = ReopenDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            partner_name = dlg.partner_name_input.text().strip()
            reason = dlg.reason_input.toPlainText().strip()
            if not partner_name or not reason:
                QMessageBox.warning(
                    self, "Validation Error", "Partner name and reason are required."
                )
                return

            try:
                self.archival_service.reopen_engagement(
                    ReopenEngagementDTO(
                        engagement_id=self.current_engagement_id,
                        reopened_by=partner_name,
                        user_role="Partner",
                        reason=reason,
                    )
                )
                QMessageBox.information(
                    self, "Engagement Reopened", "Engagement status has been updated to Reopened."
                )
                self._refresh_view()
            except Exception as ex:
                QMessageBox.critical(self, "Reopen Failed", str(ex))
