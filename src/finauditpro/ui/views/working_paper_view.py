"""Primary Working Papers Workspace View for FinAuditPro."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
from finauditpro.domain.working_paper_entities import DEFAULT_WORKING_PAPER_INDEX_GUIDANCE
from finauditpro.ui.dialogs.review_notes_dialog import ReviewNotesDialog
from finauditpro.ui.dialogs.signoff_dialog import SignOffDialog
from finauditpro.ui.theme import CardWidget, MetricCard


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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header Row
        header = QHBoxLayout()
        title = QLabel("Working Papers & Maker–Checker Control Workspace")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")
        header.addWidget(title)
        header.addStretch()

        btn_new_wp = QPushButton("+ New Working Paper")
        btn_new_wp.clicked.connect(self._on_new_wp_clicked)
        header.addWidget(btn_new_wp)
        layout.addLayout(header)

        # 2. Non-Statutory Disclaimer Card
        guidance_card = CardWidget("Configurable Working Paper Index Guidance")
        disc_lbl = QLabel(
            f"<b>Guidance Source:</b> {DEFAULT_WORKING_PAPER_INDEX_GUIDANCE['source']} "
            f"(Verified Statutory: {DEFAULT_WORKING_PAPER_INDEX_GUIDANCE['verified_statutory']})<br>"
            f"<i>{DEFAULT_WORKING_PAPER_INDEX_GUIDANCE['disclaimer']}</i>"
        )
        disc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        guidance_card.content_layout.addWidget(disc_lbl)
        layout.addWidget(guidance_card)

        # 3. Metric Summary Cards
        summary_layout = QHBoxLayout()
        self.card_total = MetricCard("Total Working Papers", "0")
        self.card_open_notes = MetricCard("Open Review Points", "0")
        self.card_signed = MetricCard("Signed Off & Locked", "0")

        summary_layout.addWidget(self.card_total)
        summary_layout.addWidget(self.card_open_notes)
        summary_layout.addWidget(self.card_signed)
        layout.addLayout(summary_layout)

        # 4. Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Ref Code",
                "Title",
                "Audit Area",
                "Status",
                "Preparer",
                "Open Points",
                "Content Hash / Lock",
                "Actions",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def set_engagement(self, engagement_id: str | None) -> None:
        if engagement_id:
            try:
                self.current_engagement = self.engagement_service.get_engagement(engagement_id)
            except Exception:
                self.current_engagement = None
        else:
            self.current_engagement = None
        self.refresh()

    def refresh(self) -> None:
        if not self.current_engagement:
            self.table.setRowCount(0)
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        wps = self.wp_service.list_working_papers(self.current_engagement.id)
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
            self.table.setItem(r, 3, QTableWidgetItem(wp.status.value))
            self.table.setItem(r, 4, QTableWidgetItem(wp.preparer_id))
            self.table.setItem(r, 5, QTableWidgetItem(str(op_count)))

            hash_str = (
                f"LOCKED ({wp.content_hash[:8]}...)"
                if wp.is_locked and wp.content_hash
                else "EDITABLE"
            )
            self.table.setItem(r, 6, QTableWidgetItem(hash_str))

            # Action Buttons Panel
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)

            btn_notes = QPushButton("Review Points")
            btn_notes.clicked.connect(lambda _, wpid=wp.id: self._open_notes(wpid))

            btn_sign = QPushButton("Sign Off")
            btn_sign.setEnabled(not wp.is_locked)
            btn_sign.clicked.connect(lambda _, wpid=wp.id: self._open_signoff(wpid))

            btn_verify = QPushButton("Verify Hash")
            btn_verify.clicked.connect(lambda _, wpid=wp.id: self._verify_hash(wpid))

            act_layout.addWidget(btn_notes)
            act_layout.addWidget(btn_sign)
            act_layout.addWidget(btn_verify)
            self.table.setCellWidget(r, 7, act_widget)

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
        dlg = ReviewNotesDialog(wp_id, self.wp_service, parent=self)
        dlg.exec()
        self.refresh()

    def _open_signoff(self, wp_id: str) -> None:
        wp = self.wp_service.get_working_paper(wp_id)
        dlg = SignOffDialog(wp, self.wp_service, parent=self)
        if dlg.exec():
            self.refresh()
            self.wp_changed.emit()

    def _verify_hash(self, wp_id: str) -> None:
        is_valid, msg = self.wp_service.verify_integrity(wp_id)
        if is_valid:
            QMessageBox.information(self, "Integrity Verified", msg)
        else:
            QMessageBox.critical(self, "TAMPER DETECTED", msg)
