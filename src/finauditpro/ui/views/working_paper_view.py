"""
Working Papers Workspace View for FinAuditPro.
Maker-Checker control, review notes, and cryptographic tamper verification.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
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

from finauditpro.application.security.rbac import UserSession
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
        user_session: UserSession | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        self.wp_service = working_paper_service
        self.user_session = user_session
        self.current_engagement: Engagement | None = None

        self._init_ui()

    def set_user_session(self, session: UserSession | None) -> None:
        self.user_session = session

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Page Header with Auto-Scaffolding
        self.header = PageHeader(
            title="Working Papers & Controls",
            subtitle="Prepare, review, sign off, and cryptographically seal statutory audit documentation (SA 230).",
            action_text="+ New Working Paper",
            action_callback=self._on_new_wp_clicked,
        )
        self.btn_scaffold_paf = QPushButton("+ Seed PAF")
        self.btn_scaffold_paf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scaffold_paf.setStyleSheet("QPushButton { background: #FFFFFF; color: #0F766E; border: 1px solid #99F6E4; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }")
        self.btn_scaffold_paf.clicked.connect(self._on_scaffold_paf_clicked)
        self.header.action_layout.addWidget(self.btn_scaffold_paf)

        self.btn_scaffold = QPushButton("Auto-Generate Schedule III")
        self.btn_scaffold.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scaffold.setStyleSheet("QPushButton { background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }")
        self.btn_scaffold.clicked.connect(self._on_scaffold_clicked)
        self.header.action_layout.addWidget(self.btn_scaffold)
        layout.addWidget(self.header)

        # 2. Metric Summary Cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(10)
        self.card_total = MetricCard("TOTAL WORKING PAPERS", "0", "Indexed workpapers", accent_color="#2563EB")
        self.card_open_notes = MetricCard("OPEN REVIEW POINTS", "0", "Awaiting clearance", accent_color="#D97706")
        self.card_signed = MetricCard("SIGNED OFF & LOCKED", "0", "Cryptographically sealed", accent_color="#16A34A")
        summary_layout.addWidget(self.card_total)
        summary_layout.addWidget(self.card_open_notes)
        summary_layout.addWidget(self.card_signed)
        layout.addLayout(summary_layout)

        # 2b. PAF / CAF Segmented Filter Bar
        from PySide6.QtWidgets import QButtonGroup, QRadioButton
        filter_box = QHBoxLayout()
        filter_box.setSpacing(8)
        self.btn_group_filter = QButtonGroup(self)
        self.radio_all = QRadioButton("All Working Papers")
        self.radio_paf = QRadioButton("Permanent File (PAF)")
        self.radio_caf = QRadioButton("Current File (CAF)")
        self.radio_all.setChecked(True)

        for idx, rb in enumerate([self.radio_all, self.radio_paf, self.radio_caf]):
            self.btn_group_filter.addButton(rb, idx)
            filter_box.addWidget(rb)
            rb.toggled.connect(self.refresh)
        filter_box.addStretch()
        layout.addLayout(filter_box)

        # 3. Splitter Workspace (Left: Table, Right: Details / Evidence Preview)
        from PySide6.QtWidgets import QSplitter, QTextEdit

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_card = CardWidget("WORKING PAPERS DIRECTORY")
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["REF CODE", "FILE TYPE", "TITLE", "AUDIT AREA", "STATUS", "PREPARER", "OPEN POINTS", "LOCK / HASH", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 3, 4, 5, 6, 7, 8]:
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_wp_selected)

        self.empty_state = EmptyStateWidget(
            title="No working papers created yet",
            description="Generate standard Schedule III audit folders or create a custom working paper.",
            action_text="+ Auto-Generate Folders",
            action_callback=self._on_scaffold_clicked,
        )

        self.table.setVisible(False)
        self.table_card.content_layout.addWidget(self.table)
        self.table_card.content_layout.addWidget(self.empty_state)
        self.splitter.addWidget(self.table_card)

        # Right Pane: Evidence & Details
        self.preview_card = CardWidget("DOCUMENT EVIDENCE & TESTING PREVIEW")
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("QTextEdit { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; color: #334155; font-family: monospace; font-size: 12px; padding: 12px; }")
        from PySide6.QtGui import QColor, QPalette
        pal = self.preview_text.palette()
        pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#94A3B8"))
        self.preview_text.setPalette(pal)
        self.preview_text.setPlaceholderText("Select a working paper to inspect testing procedures, audit conclusions, and linked evidence.")
        self.preview_card.content_layout.addWidget(self.preview_text)
        self.splitter.addWidget(self.preview_card)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)
        layout.addWidget(self.splitter, 1)
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

    set_active_engagement = set_engagement

    def refresh(self) -> None:
        if not self.current_engagement:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        all_wps = self.wp_service.list_working_papers(self.current_engagement.id)
        if not all_wps:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        # Apply PAF / CAF Radio Filter
        from finauditpro.domain.working_paper_entities import FileCategoryEnum
        if self.radio_paf.isChecked():
            wps = [w for w in all_wps if getattr(w, "file_category", FileCategoryEnum.CURRENT_FILE) == FileCategoryEnum.PERMANENT_FILE]
        elif self.radio_caf.isChecked():
            wps = [w for w in all_wps if getattr(w, "file_category", FileCategoryEnum.CURRENT_FILE) == FileCategoryEnum.CURRENT_FILE]
        else:
            wps = all_wps

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

            cat_str = wp.file_category.value if hasattr(wp.file_category, "value") else str(getattr(wp, "file_category", "Current File"))
            is_paf = "Permanent" in cat_str

            self.table.setItem(r, 0, QTableWidgetItem(wp.index_reference))
            cat_item = QTableWidgetItem("PAF" if is_paf else "CAF")
            cat_item.setForeground(Qt.GlobalColor.darkCyan if is_paf else Qt.GlobalColor.darkBlue)
            self.table.setItem(r, 1, cat_item)
            self.table.setItem(r, 2, QTableWidgetItem(wp.title))
            self.table.setItem(r, 3, QTableWidgetItem(wp.area))
            self.table.setItem(r, 4, QTableWidgetItem(f"● {wp.status.value}"))
            self.table.setItem(r, 5, QTableWidgetItem(wp.preparer_id))
            self.table.setItem(r, 6, QTableWidgetItem(str(op_count)))

            hash_str = (
                f"LOCKED ({wp.content_hash[:8]}...)"
                if wp.is_locked and wp.content_hash
                else "EDITABLE"
            )
            self.table.setItem(r, 7, QTableWidgetItem(hash_str))

            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_notes = QPushButton("Notes")
            btn_notes.clicked.connect(lambda _, wpid=wp.id: self._open_notes(wpid))
            act_layout.addWidget(btn_notes)

            from finauditpro.domain.working_paper_entities import WorkingPaperStatusEnum
            if wp.status in (WorkingPaperStatusEnum.DRAFT, WorkingPaperStatusEnum.RETURNED):
                btn_submit = QPushButton("Submit")
                btn_submit.clicked.connect(lambda _, wpid=wp.id: self._submit_wp(wpid))
                act_layout.addWidget(btn_submit)
            elif wp.status in (WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW, WorkingPaperStatusEnum.RESUBMITTED):
                btn_review = QPushButton("Review")
                btn_review.clicked.connect(lambda _, wpid=wp.id: self._start_review(wpid))
                act_layout.addWidget(btn_review)
            elif wp.status == WorkingPaperStatusEnum.UNDER_REVIEW:
                btn_return = QPushButton("Return")
                btn_return.clicked.connect(lambda _, wpid=wp.id: self._return_wp(wpid))
                act_layout.addWidget(btn_return)

                btn_sign = QPushButton("Sign Off")
                btn_sign.clicked.connect(lambda _, wpid=wp.id: self._open_signoff(wpid))
                act_layout.addWidget(btn_sign)
            elif wp.status in (WorkingPaperStatusEnum.APPROVED, WorkingPaperStatusEnum.LOCKED):
                btn_reopen = QPushButton("Reopen")
                btn_reopen.clicked.connect(lambda _, wpid=wp.id: self._reopen_wp(wpid))
                act_layout.addWidget(btn_reopen)

            btn_verify = QPushButton("Verify")
            btn_verify.clicked.connect(lambda _, wpid=wp.id: self._verify_hash(wpid))
            act_layout.addWidget(btn_verify)

            self.table.setCellWidget(r, 8, act_widget)

        self.table.setFixedHeight(max(1, len(wps)) * 36 + 32)
        self.card_total.set_value(str(len(all_wps)))
        self.card_open_notes.set_value(str(total_open_notes))
        self.card_signed.set_value(str(signed_count))

    def _on_scaffold_paf_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        created = self.wp_service.scaffold_permanent_audit_file(self.current_engagement.id)
        if created:
            QMessageBox.information(
                self,
                "Permanent Audit File (PAF) Seeded",
                f"Successfully initialized {len(created)} permanent statutory records (MOA/AOA, Tax Registrations, KMP, Bank mandates).",
            )
        else:
            QMessageBox.information(
                self,
                "Permanent Audit File",
                "All standard Permanent Audit File (PAF) records already exist for this engagement.",
            )
        self.refresh()
        self.wp_changed.emit()

    def _on_new_wp_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        preparer = self.user_session.username if self.user_session else "Lead Auditor"
        wp = self.wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=self.current_engagement.id,
                index_reference="WP-REV-001",
                title="Revenue Substantive Testing & Cut-Off",
                area="C. Revenue & Receivables",
                preparer_id=preparer,
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
        if SignOffDialog(wp, self.wp_service, user_session=self.user_session, parent=self).exec():
            self.refresh()
            self.wp_changed.emit()

    def _on_scaffold_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return
        created = self.wp_service.scaffold_schedule_iii_working_papers(self.current_engagement.id)
        if created:
            QMessageBox.information(
                self,
                "Schedule III Folders Scaffolded",
                f"Successfully generated {len(created)} standard ICAI Schedule III statutory working papers.",
            )
        else:
            QMessageBox.information(
                self,
                "Schedule III Folders",
                "All standard Schedule III statutory audit working papers already exist for this engagement.",
            )
        self.refresh()
        self.wp_changed.emit()

    def _on_wp_selected(self) -> None:
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        ref_item = self.table.item(row, 0)
        if not ref_item or not self.current_engagement:
            return

        wps = self.wp_service.list_working_papers(self.current_engagement.id)
        if row < len(wps):
            wp = wps[row]
            sections = self.wp_service.get_sections(wp.id)
            links = self.wp_service.list_links(wp.id)

            lines = [
                "===========================================================",
                f" WORKING PAPER: [{wp.index_reference}] {wp.title}",
                f" Area: {wp.area} | Status: {wp.status.value}",
                f" Preparer: {wp.preparer_id} | Version: {wp.version}",
                f" Locked: {'YES (Tamper-Sealed)' if wp.is_locked else 'NO (Draft / Editable)'}",
                f" Content Hash: {wp.content_hash or 'Not sealed yet'}",
                "===========================================================\n",
                "--- SECTIONS & PROCEDURAL TESTING ---",
            ]

            for s in sections:
                lines.append(f"\n▶ {s.title}")
                lines.append(f"  {s.content_markdown}")

            lines.append("\n--- LINKED AUDIT EVIDENCE & PROCEDURES ---")
            if links:
                for l in links:
                    lines.append(
                        f"• [{l.get('link_type', 'evidence').upper()}] ID: {l.get('target_id')}"
                    )
            else:
                lines.append(
                    "• No external PDF / document evidence linked yet. Link evidence via Document Intelligence."
                )

            self.preview_text.setText("\n".join(lines))

    def _verify_hash(self, wp_id: str) -> None:
        is_valid, msg = self.wp_service.verify_integrity(wp_id)
        if is_valid:
            QMessageBox.information(self, "Integrity Verified", msg)
        else:
            QMessageBox.critical(self, "TAMPER DETECTED", msg)

    def _submit_wp(self, wp_id: str) -> None:
        user_name = self.user_session.username if self.user_session else "Auditor"
        try:
            self.wp_service.submit_for_review(wp_id, user_name)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def _start_review(self, wp_id: str) -> None:
        user_name = self.user_session.username if self.user_session else "Auditor"
        try:
            self.wp_service.start_review(wp_id, user_name)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def _return_wp(self, wp_id: str) -> None:
        user_name = self.user_session.username if self.user_session else "Auditor"
        try:
            self.wp_service.return_working_paper(wp_id, user_name)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def _reopen_wp(self, wp_id: str) -> None:
        from PySide6.QtWidgets import QInputDialog
        user_name = self.user_session.username if self.user_session else "Auditor"
        reason, ok = QInputDialog.getText(self, "Reopen Working Paper", "Enter reason for reopening:")
        if ok and reason.strip():
            from finauditpro.application.working_paper_dtos import ReopenWorkingPaperDTO
            try:
                self.wp_service.reopen_working_paper(ReopenWorkingPaperDTO(
                    working_paper_id=wp_id,
                    reopened_by=user_name,
                    reason=reason.strip()
                ))
                self.refresh()
                self.wp_changed.emit()
            except Exception as ex:
                QMessageBox.critical(self, "Error", str(ex))
