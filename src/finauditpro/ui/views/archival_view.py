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


class ReopenDialog(QDialog):
    """Dialog prompting for Partner RBAC verification and justification reason to reopen sealed engagement."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Reopen Sealed Engagement — Partner Auth Required")
        self.resize(480, 260)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel("<b>Reopen Sealed Audit Engagement</b>")
        layout.addWidget(header)

        notice = QLabel(
            "<i>Notice: Reopening a sealed audit engagement requires Partner role authorization. "
            "The prior sealed archive is preserved intact in the audit trail.</i>"
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            "color: #744210; background-color: #fefcbf; padding: 6px; border-radius: 4px;"
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
        confirm_btn = QPushButton("Authorize & Reopen")
        confirm_btn.setStyleSheet("background-color: #c53030; color: white; font-weight: bold;")
        confirm_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)


class ArchivalView(QWidget):
    """Workspace view displaying retention timelines, readiness status, sealed archives, and reopen triggers."""

    def __init__(self, db_manager: Any, parent=None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.archival_service = ArchivalService(db_manager)
        self.current_engagement_id: str | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Title & Retention Banner
        title_layout = QHBoxLayout()
        self.title_label = QLabel("<h2>Engagement Archival & Retention Control</h2>")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.close_wizard_btn = QPushButton("🔒 Close & Seal Engagement Wizard")
        self.close_wizard_btn.setStyleSheet(
            "background-color: #2b6cb0; color: white; font-weight: bold; padding: 6px 12px;"
        )
        self.close_wizard_btn.clicked.connect(self._open_close_wizard)
        title_layout.addWidget(self.close_wizard_btn)

        self.reopen_btn = QPushButton("🔓 Reopen Engagement (Partner Only)")
        self.reopen_btn.setStyleSheet(
            "background-color: #744210; color: white; font-weight: bold; padding: 6px 12px;"
        )
        self.reopen_btn.clicked.connect(self._open_reopen_dialog)
        title_layout.addWidget(self.reopen_btn)

        layout.addLayout(title_layout)

        # Status & Read-Only Banner
        self.banner_frame = QFrame()
        self.banner_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.banner_frame.setStyleSheet(
            "background-color: #1e293b; border: 1px solid #0284c7; border-radius: 6px; padding: 12px;"
        )
        banner_layout = QVBoxLayout(self.banner_frame)

        self.status_banner_label = QLabel("<b>Engagement Status:</b> Active")
        self.status_banner_label.setStyleSheet("color: #38bdf8; font-size: 13px;")

        self.timeline_banner_label = QLabel(
            "<b>Retention Config:</b> Assembly Period: 60 Days | Retention Period: 7 Years (source: SA 230 Guidance) [verified: false]"
        )
        self.timeline_banner_label.setStyleSheet("color: #f8fafc; font-size: 12px;")

        banner_layout.addWidget(self.status_banner_label)
        banner_layout.addWidget(self.timeline_banner_label)
        layout.addWidget(self.banner_frame)

        # Sealed Archives Table
        layout.addWidget(QLabel("<b>Sealed Audit Archives & Integrity Hashes:</b>"))
        self.archives_table = QTableWidget()
        self.archives_table.setColumnCount(6)
        self.archives_table.setHorizontalHeaderLabels(
            [
                "Archive ID",
                "Report Date",
                "Assembly Deadline",
                "Retain Until",
                "Encrypted",
                "Sealed Content Hash",
            ]
        )
        self.archives_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.archives_table)

    def load_engagement(self, engagement_id: str) -> None:
        self.current_engagement_id = engagement_id
        self._refresh_view()

    def _refresh_view(self) -> None:
        if not self.current_engagement_id:
            return

        ret_cfg = self.archival_service.get_or_create_retention_config()
        self.timeline_banner_label.setText(
            f"<b>Retention Policy:</b> Assembly Period: {ret_cfg.assembly_period_days} Days | "
            f"Retention Period: {ret_cfg.retention_period_years} Years | "
            f"Source: {ret_cfg.source} [verified: false]"
        )

        status_str = self.archival_service.get_engagement_status(self.current_engagement_id)
        self.status_banner_label.setText(f"<b>Engagement Status:</b> {status_str}")

        if status_str == "Archived":
            self.banner_frame.setStyleSheet(
                "background-color: #fff5f5; border: 1px solid #feb2b2; border-radius: 4px; padding: 8px;"
            )
            self.status_banner_label.setText(
                "<b>READ-ONLY ARCHIVED FILE</b> — Engagement is frozen & sealed against modifications."
            )
            self.close_wizard_btn.setEnabled(False)
            self.reopen_btn.setEnabled(True)
        else:
            self.banner_frame.setStyleSheet(
                "background-color: #ebf8ff; border: 1px solid #90cdf4; border-radius: 4px; padding: 8px;"
            )
            self.close_wizard_btn.setEnabled(True)
            self.reopen_btn.setEnabled(False)

        archives = self.archival_service.list_archives_for_engagement(self.current_engagement_id)

        self.archives_table.setRowCount(len(archives))
        for row, arch in enumerate(archives):
            self.archives_table.setItem(row, 0, QTableWidgetItem(arch.id[:8]))
            self.archives_table.setItem(row, 1, QTableWidgetItem(arch.report_date))
            self.archives_table.setItem(row, 2, QTableWidgetItem(arch.assembly_deadline))
            self.archives_table.setItem(row, 3, QTableWidgetItem(arch.retain_until))
            self.archives_table.setItem(
                row, 4, QTableWidgetItem("Yes" if arch.is_encrypted else "No")
            )
            self.archives_table.setItem(
                row, 5, QTableWidgetItem(f"{arch.sealed_content_hash[:16]}...")
            )

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
                    self,
                    "Engagement Reopened",
                    "Engagement status has been updated to Reopened. Prior sealed archive is preserved.",
                )
                self._refresh_view()
            except Exception as ex:
                QMessageBox.critical(self, "Reopen Failed", str(ex))
