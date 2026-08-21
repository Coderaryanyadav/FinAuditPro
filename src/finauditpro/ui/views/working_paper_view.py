"""
Working Papers Workspace View for FinAuditPro.
Maker-Checker control, review notes, and cryptographic tamper verification.
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.entities import Engagement
from finauditpro.ui.dialogs.review_notes_dialog import ReviewNotesDialog
from finauditpro.ui.dialogs.signoff_dialog import SignOffDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, MetricCard, PageHeader


class WorkingPaperView(QWidget):
    """Primary Working Papers Workspace View."""

    wp_changed = Signal()

    def __init__(
        self,
        engagement_service: EngagementService,
        working_paper_service: WorkingPaperService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        self.wp_service = working_paper_service
        self.current_engagement: Engagement | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header
        self.header = PageHeader(
            title="Working Papers & Controls",
            subtitle="Prepare, review, sign off, and cryptographically seal audit documentation.",
            action_text="+ New Working Paper",
            action_callback=self._on_new_wp_clicked,
        )
        layout.addWidget(self.header)

        # 2. Metric Summary Cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(10)
        self.card_total = MetricCard(
            "TOTAL WORKING PAPERS", "0", "Indexed workpapers", accent_color="#2563EB"
        )
        self.card_open_notes = MetricCard(
            "OPEN REVIEW POINTS", "0", "Awaiting clearance", accent_color="#D97706"
        )
        self.card_signed = MetricCard(
            "SIGNED OFF & LOCKED", "0", "Cryptographically sealed", accent_color="#16A34A"
        )

        summary_layout.addWidget(self.card_total)
        summary_layout.addWidget(self.card_open_notes)
        summary_layout.addWidget(self.card_signed)
        layout.addLayout(summary_layout)

        # 3. Table Card & Empty State
        self.table_card = CardWidget("WORKING PAPERS DIRECTORY")
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "REF CODE",
                "TITLE",
                "AUDIT AREA",
                "STATUS",
                "PREPARER",
                "OPEN POINTS",
                "LOCK / HASH",
                "ACTIONS",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in [0, 2, 3, 4, 5, 6, 7]:
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.empty_state = EmptyStateWidget(
            title="No working papers created yet",
            description="Create a working paper to document audit procedures, link evidence, and complete maker-checker signoff.",
            action_text="+ New Working Paper",
            action_callback=self._on_new_wp_clicked,
        )

        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        layout.addWidget(self.table_card)
        layout.addStretch(1)

        self.refresh()

    def set_engagement(self, engagement: Any) -> None:
        if isinstance(engagement, Engagement):
            self.current_engagement = engagement
            self.header.action_btn.setEnabled(True)
        elif engagement:
            try:
                self.current_engagement = self.engagement_service.get_engagement(str(engagement))
                self.header.action_btn.setEnabled(True)
            except Exception:
                self.current_engagement = None
                self.header.action_btn.setEnabled(False)
        else:
            self.current_engagement = None
            self.header.action_btn.setEnabled(False)
        self.refresh()

    set_active_engagement = set_engagement


    def refresh(self) -> None:
        if not self.current_engagement:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        wps = self.wp_service.list_working_papers(self.current_engagement.id)
        if not wps:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        total_open_notes = 0
        signed_count = 0

        for r, wp in enumerate(wps):
            self.table.insertRow(r)
            op_count = self.wp_service.count_open_review_notes(wp.id)
            total_open_notes += op_count
            if wp.is_locked:
                signed_count += 1

            self.table.setItem(r, 0, QTableWidgetItem(wp.index_reference))
            self.table.setItem(r, 1, QTableWidgetItem(wp.title))
            self.table.setItem(r, 2, QTableWidgetItem(wp.area))
            self.table.setItem(r, 3, QTableWidgetItem(f"● {wp.status.value}"))
            self.table.setItem(r, 4, QTableWidgetItem(wp.preparer_id))
            self.table.setItem(r, 5, QTableWidgetItem(str(op_count)))

            hash_str = (
                f"🔒 LOCKED ({wp.content_hash[:8]}...)"
                if wp.is_locked and wp.content_hash
                else "EDITABLE"
            )
            self.table.setItem(r, 6, QTableWidgetItem(hash_str))

            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_notes = QPushButton("Notes")
            btn_notes.clicked.connect(lambda _, wpid=wp.id: self._open_notes(wpid))

            btn_sign = QPushButton("Sign Off")
            btn_sign.setEnabled(not wp.is_locked)
            btn_sign.clicked.connect(lambda _, wpid=wp.id: self._open_signoff(wpid))

            btn_verify = QPushButton("Verify")
            btn_verify.clicked.connect(lambda _, wpid=wp.id: self._verify_hash(wpid))

            act_layout.addWidget(btn_notes)
            act_layout.addWidget(btn_sign)
            act_layout.addWidget(btn_verify)
            self.table.setCellWidget(r, 7, act_widget)

        self.table.setFixedHeight(max(1, len(wps)) * 36 + 32)
        self.card_total.set_value(str(len(wps)))
        self.card_open_notes.set_value(str(total_open_notes))
        self.card_signed.set_value(str(signed_count))

    def _on_new_wp_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        wp = self.wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=self.current_engagement.id,
                index_reference="WP-REV-001",
                title="Revenue Substantive Testing & Cut-Off",
                area="C. Revenue & Receivables",
                preparer_id="Senior Auditor",
            )
        )
        QMessageBox.information(
            self,
            "Working Paper Created",
            f"Created Working Paper '{wp.index_reference}': {wp.title}",
        )
        self.refresh()
        self.wp_changed.emit()

    def _open_notes(self, wp_id: str) -> None:
        ReviewNotesDialog(wp_id, self.wp_service, parent=self).exec()
        self.refresh()

    def _open_signoff(self, wp_id: str) -> None:
        wp = self.wp_service.get_working_paper(wp_id)
        if SignOffDialog(wp, self.wp_service, parent=self).exec():
            self.refresh()
            self.wp_changed.emit()

    def _verify_hash(self, wp_id: str) -> None:
        is_valid, msg = self.wp_service.verify_integrity(wp_id)
        if is_valid:
            QMessageBox.information(self, "Integrity Verified", msg)
        else:
            QMessageBox.critical(self, "TAMPER DETECTED", msg)
