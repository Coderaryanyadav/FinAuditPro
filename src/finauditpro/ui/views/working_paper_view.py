"""Audit Workbench & Working Papers Workspace View for FinAuditPro.

3-Pane Audit Workbench:
- LEFT: Working Paper tree (PAF, CAF, Audit Areas)
- CENTER: Active Working Paper workspace (Objective, Risks, Assertions, Procedures, Testing, Sections, Conclusion, Versions)
- RIGHT: Linked Evidence & Document Verification + Review Notes & Sign-offs
"""

import json
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    WorkingPaperWorkbenchDTO,
)
from finauditpro.domain.entities import Engagement
from finauditpro.domain.working_paper_entities import (
    FileCategoryEnum,
    ReviewNoteStatusEnum,
    WorkingPaper,
    WorkingPaperStatusEnum,
)
from finauditpro.ui.dialogs.review_notes_dialog import ReviewNotesDialog
from finauditpro.ui.dialogs.sampling_dialog import SamplingCalculatorDialog
from finauditpro.ui.dialogs.signoff_dialog import SignOffDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, MetricCard, PageHeader, format_inr


class WorkingPaperView(QWidget):
    """Integrated 3-Pane Audit Workbench View."""

    wp_changed = Signal()

    def __init__(
        self,
        engagement_service: EngagementService,
        working_paper_service: WorkingPaperService,
        user_session: UserSession | None = None,
        audit_matrix_service: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        self.wp_service = working_paper_service
        self.user_session = user_session
        self.audit_matrix_service = audit_matrix_service
        self.current_engagement: Engagement | None = None
        self.active_wp_id: str | None = None
        self.current_workbench_data: WorkingPaperWorkbenchDTO | None = None

        self._init_ui()

    def set_user_session(self, session: UserSession | None) -> None:
        self.user_session = session

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(10)

        # Header
        self.header = PageHeader(
            title="Audit Workbench & Working Papers",
            subtitle="Prepare, review, execute procedures, verify evidence, and cryptographically seal statutory audit documentation (SA 230).",
            action_text="+ New Working Paper",
            action_callback=self._on_new_wp_clicked,
        )
        self.btn_scaffold_paf = QPushButton("+ Seed PAF")
        self.btn_scaffold_paf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scaffold_paf.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #0F766E; border: 1px solid #99F6E4; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }"
        )
        self.btn_scaffold_paf.clicked.connect(self._on_scaffold_paf_clicked)
        self.header.action_layout.addWidget(self.btn_scaffold_paf)

        self.btn_scaffold = QPushButton("Auto-Generate Schedule III")
        self.btn_scaffold.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scaffold.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: 600; font-size: 12px; }"
        )
        self.btn_scaffold.clicked.connect(self._on_scaffold_clicked)
        self.header.action_layout.addWidget(self.btn_scaffold)
        layout.addWidget(self.header)

        # Top Metric Cards
        metric_layout = QHBoxLayout()
        metric_layout.setSpacing(10)
        self.card_total = MetricCard("TOTAL WORKING PAPERS", "0", "Indexed workpapers", accent_color="#2563EB")
        self.card_open_notes = MetricCard("OPEN REVIEW POINTS", "0", "Awaiting clearance", accent_color="#D97706")
        self.card_signed = MetricCard("SIGNED OFF & LOCKED", "0", "Cryptographically sealed", accent_color="#16A34A")
        metric_layout.addWidget(self.card_total)
        metric_layout.addWidget(self.card_open_notes)
        metric_layout.addWidget(self.card_signed)
        layout.addLayout(metric_layout)

        # Main 3-Pane Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ====================================================================
        # LEFT PANE: Working Paper Tree
        # ====================================================================
        self.left_card = CardWidget("WORKING PAPERS TREE")
        left_layout = self.left_card.content_layout

        # Filter bar
        filter_box = QHBoxLayout()
        filter_box.setSpacing(6)
        self.btn_group_filter = QButtonGroup(self)
        self.radio_all = QRadioButton("All")
        self.radio_paf = QRadioButton("PAF")
        self.radio_caf = QRadioButton("CAF")
        self.radio_all.setChecked(True)
        for idx, rb in enumerate([self.radio_all, self.radio_paf, self.radio_caf]):
            self.btn_group_filter.addButton(rb, idx)
            filter_box.addWidget(rb)
            rb.toggled.connect(self.refresh)
        filter_box.addStretch()
        left_layout.addLayout(filter_box)

        # Search Bar
        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("Filter working papers...")
        self.tree_search.textChanged.connect(self._filter_tree)
        left_layout.addWidget(self.tree_search)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        left_layout.addWidget(self.tree, 1)

        self.main_splitter.addWidget(self.left_card)

        # ====================================================================
        # CENTER PANE: Active Working Paper Workspace
        # ====================================================================
        self.center_card = CardWidget("WORKING PAPER WORKSPACE")
        center_layout = self.center_card.content_layout

        # Header Banner for active WP
        self.wp_header_widget = QWidget()
        self.wp_header_layout = QVBoxLayout(self.wp_header_widget)
        self.wp_header_layout.setContentsMargins(0, 0, 0, 6)
        self.wp_header_layout.setSpacing(4)

        self.lbl_wp_title = QLabel("Select a working paper from the tree on the left.")
        self.lbl_wp_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        self.lbl_wp_meta = QLabel("")
        self.lbl_wp_meta.setStyleSheet("font-size: 12px; color: #64748B;")
        self.lbl_wp_meta.setWordWrap(True)

        self.wp_header_layout.addWidget(self.lbl_wp_title)
        self.wp_header_layout.addWidget(self.lbl_wp_meta)
        center_layout.addWidget(self.wp_header_widget)

        # Tab Widget for Center Pane
        self.center_tabs = QTabWidget()

        # Tab 1: Objectives & Canonical Audit Graph
        self.tab_graph = QWidget()
        tab_graph_layout = QVBoxLayout(self.tab_graph)
        tab_graph_layout.setContentsMargins(6, 6, 6, 6)
        tab_graph_layout.setSpacing(8)

        self.lbl_objective = QLabel("Audit Objective: None")
        self.lbl_objective.setStyleSheet("background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 8px; color: #1E40AF; font-size: 12px; font-weight: 500;")
        self.lbl_objective.setWordWrap(True)
        tab_graph_layout.addWidget(self.lbl_objective)

        # Risks & Assertions Table
        tab_graph_layout.addWidget(QLabel("<b>Linked Risks & Assertions:</b>"))
        self.tbl_risks = QTableWidget()
        self.tbl_risks.setColumnCount(5)
        self.tbl_risks.setHorizontalHeaderLabels(["Risk Code", "Title", "Inherent", "Control", "Derived RoMM"])
        self.tbl_risks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_risks.verticalHeader().setVisible(False)
        self.tbl_risks.setFixedHeight(110)
        tab_graph_layout.addWidget(self.tbl_risks)

        # Procedures & Testing Table
        tab_graph_layout.addWidget(QLabel("<b>Procedures, Population & Testing Executions:</b>"))
        self.tbl_procs = QTableWidget()
        self.tbl_procs.setColumnCount(5)
        self.tbl_procs.setHorizontalHeaderLabels(["Code", "Objective", "Population", "Samples", "Outcome"])
        self.tbl_procs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_procs.verticalHeader().setVisible(False)
        self.tbl_procs.setFixedHeight(120)
        tab_graph_layout.addWidget(self.tbl_procs)

        # Findings & Exceptions
        tab_graph_layout.addWidget(QLabel("<b>Audit Exceptions & Findings:</b>"))
        self.tbl_findings = QTableWidget()
        self.tbl_findings.setColumnCount(4)
        self.tbl_findings.setHorizontalHeaderLabels(["Title / Code", "Severity", "Monetary Amount", "Status"])
        self.tbl_findings.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_findings.verticalHeader().setVisible(False)
        self.tbl_findings.setFixedHeight(100)
        tab_graph_layout.addWidget(self.tbl_findings)

        self.center_tabs.addTab(self.tab_graph, "Canonical Graph")

        # Tab 2: Substantive Testing Grid & Tick Marks
        self._init_testing_tab()
        self.center_tabs.addTab(self.tab_testing, "Testing Grid & Tick Marks")

        # Tab 3: Working Paper Content & Sections Editor
        self.tab_content = QWidget()
        tab_content_layout = QVBoxLayout(self.tab_content)
        tab_content_layout.setContentsMargins(6, 6, 6, 6)
        tab_content_layout.setSpacing(6)

        self.txt_sections_editor = QTextEdit()
        self.txt_sections_editor.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-family: monospace; font-size: 12px; padding: 10px; color: #1E293B; }"
        )
        tab_content_layout.addWidget(self.txt_sections_editor, 1)

        btn_save_row = QHBoxLayout()
        self.btn_save_content = QPushButton("Save Content Changes")
        self.btn_save_content.setStyleSheet("background: #0284C7; color: white; font-weight: 600; padding: 6px 14px; border-radius: 6px;")
        self.btn_save_content.clicked.connect(self._on_save_content_clicked)
        btn_save_row.addWidget(self.btn_save_content)
        btn_save_row.addStretch()
        tab_content_layout.addLayout(btn_save_row)

        self.center_tabs.addTab(self.tab_content, "Documentation & Sections")

        # Tab 3: Auditor Conclusion
        self.tab_conclusion = QWidget()
        tab_conc_layout = QVBoxLayout(self.tab_conclusion)
        tab_conc_layout.setContentsMargins(6, 6, 6, 6)
        tab_conc_layout.setSpacing(6)

        tab_conc_layout.addWidget(QLabel("<b>Auditor Conclusion & SA 700 Impact:</b>"))
        self.txt_conclusion_editor = QTextEdit()
        self.txt_conclusion_editor.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; padding: 10px; color: #1E293B; }"
        )
        tab_conc_layout.addWidget(self.txt_conclusion_editor, 1)

        btn_save_conc_row = QHBoxLayout()
        self.btn_save_conclusion = QPushButton("Save Conclusion")
        self.btn_save_conclusion.setStyleSheet("background: #0D9488; color: white; font-weight: 600; padding: 6px 14px; border-radius: 6px;")
        self.btn_save_conclusion.clicked.connect(self._on_save_conclusion_clicked)
        btn_save_conc_row.addWidget(self.btn_save_conclusion)
        btn_save_conc_row.addStretch()
        tab_conc_layout.addLayout(btn_save_conc_row)

        self.center_tabs.addTab(self.tab_conclusion, "Conclusion")

        # Tab 4: Version History & Historical Snapshots
        self.tab_versions = QWidget()
        tab_ver_layout = QVBoxLayout(self.tab_versions)
        tab_ver_layout.setContentsMargins(6, 6, 6, 6)
        tab_ver_layout.setSpacing(6)

        self.tbl_versions = QTableWidget()
        self.tbl_versions.setColumnCount(5)
        self.tbl_versions.setHorizontalHeaderLabels(["Version", "Status", "Preparer", "Content Hash", "Archived At"])
        self.tbl_versions.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_versions.verticalHeader().setVisible(False)
        self.tbl_versions.itemSelectionChanged.connect(self._on_version_selected)
        tab_ver_layout.addWidget(self.tbl_versions, 1)

        tab_ver_layout.addWidget(QLabel("<b>Historical Version Snapshot (Read-Only):</b>"))
        self.txt_snapshot_view = QTextEdit()
        self.txt_snapshot_view.setReadOnly(True)
        self.txt_snapshot_view.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-family: monospace; font-size: 12px; padding: 8px;")
        tab_ver_layout.addWidget(self.txt_snapshot_view, 1)

        self.center_tabs.addTab(self.tab_versions, "Version History")

        center_layout.addWidget(self.center_tabs, 1)

        # Center Bottom Action Bar
        self.action_bar = QHBoxLayout()
        self.action_bar.setSpacing(6)

        self.btn_submit = QPushButton("Submit for Review")
        self.btn_submit.clicked.connect(self._on_submit_clicked)
        self.action_bar.addWidget(self.btn_submit)

        self.btn_review = QPushButton("Start Review")
        self.btn_review.clicked.connect(self._on_start_review_clicked)
        self.action_bar.addWidget(self.btn_review)

        self.btn_return = QPushButton("Return")
        self.btn_return.clicked.connect(self._on_return_clicked)
        self.action_bar.addWidget(self.btn_return)

        self.btn_approve = QPushButton("Approve")
        self.btn_approve.setStyleSheet("background: #10B981; color: white; font-weight: 600;")
        self.btn_approve.clicked.connect(self._on_approve_clicked)
        self.action_bar.addWidget(self.btn_approve)

        self.btn_signoff = QPushButton("Sign Off & Seal")
        self.btn_signoff.setStyleSheet("background: #059669; color: white; font-weight: 600;")
        self.btn_signoff.clicked.connect(self._on_signoff_clicked)
        self.action_bar.addWidget(self.btn_signoff)

        self.btn_reopen = QPushButton("Reopen (Partner)")
        self.btn_reopen.setStyleSheet("background: #E11D48; color: white; font-weight: 600;")
        self.btn_reopen.clicked.connect(self._on_reopen_clicked)
        self.action_bar.addWidget(self.btn_reopen)

        self.action_bar.addStretch()
        center_layout.addLayout(self.action_bar)

        self.main_splitter.addWidget(self.center_card)

        # ====================================================================
        # RIGHT PANE: Evidence + Review Notes
        # ====================================================================
        self.right_card = CardWidget("EVIDENCE & REVIEW")
        right_layout = self.right_card.content_layout

        # Section 1: Linked Evidence
        right_layout.addWidget(QLabel("<b>Linked Evidence & Hash Verification:</b>"))
        self.evidence_list = QListWidget()
        right_layout.addWidget(self.evidence_list, 1)

        ev_btn_row = QHBoxLayout()
        self.btn_verify_hash = QPushButton("Verify Hash Integrity")
        self.btn_verify_hash.clicked.connect(self._on_verify_hash_clicked)
        ev_btn_row.addWidget(self.btn_verify_hash)
        right_layout.addLayout(ev_btn_row)

        # Section 2: Review Notes & Preconditions
        self.lbl_review_alert = QLabel("")
        self.lbl_review_alert.setStyleSheet("background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; font-size: 12px; font-weight: 600; padding: 6px; border-radius: 6px;")
        self.lbl_review_alert.setVisible(False)
        self.lbl_review_alert.setWordWrap(True)
        right_layout.addWidget(self.lbl_review_alert)

        right_layout.addWidget(QLabel("<b>Review Notes & Clearance:</b>"))
        self.notes_list = QListWidget()
        right_layout.addWidget(self.notes_list, 1)

        notes_btn_row = QHBoxLayout()
        self.btn_raise_note = QPushButton("+ Raise Note")
        self.btn_raise_note.setStyleSheet("background: #2563EB; color: white; font-weight: 600;")
        self.btn_raise_note.clicked.connect(self._on_raise_note_clicked)
        self.btn_respond_note = QPushButton("Respond")
        self.btn_respond_note.clicked.connect(self._on_respond_note_clicked)
        self.btn_clear_note = QPushButton("Clear Note")
        self.btn_clear_note.clicked.connect(self._on_clear_note_clicked)
        self.btn_thread_notes = QPushButton("Threaded View")
        self.btn_thread_notes.setToolTip("Open full threaded conversation workspace for review notes")
        self.btn_thread_notes.clicked.connect(self._on_open_threaded_notes_clicked)

        notes_btn_row.addWidget(self.btn_raise_note)
        notes_btn_row.addWidget(self.btn_respond_note)
        notes_btn_row.addWidget(self.btn_clear_note)
        notes_btn_row.addWidget(self.btn_thread_notes)
        right_layout.addLayout(notes_btn_row)

        # Section 3: Sign-Off Records
        right_layout.addWidget(QLabel("<b>Electronic Sign-Offs & UDIN Attestations:</b>"))
        self.signoffs_list = QListWidget()
        self.signoffs_list.setFixedHeight(90)
        right_layout.addWidget(self.signoffs_list)

        self.main_splitter.addWidget(self.right_card)

        # Set Splitter Proportions: Left 25%, Center 45%, Right 30%
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setStretchFactor(2, 4)

        layout.addWidget(self.main_splitter, 1)

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
        self.active_wp_id = None
        self.refresh()

    set_active_engagement = set_engagement

    def refresh(self) -> None:
        if not self.current_engagement:
            self.tree.clear()
            self._clear_active_wp()
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        all_wps = self.wp_service.list_working_papers(self.current_engagement.id)
        if not all_wps:
            self.tree.clear()
            self._clear_active_wp()
            self.card_total.set_value("0")
            self.card_open_notes.set_value("0")
            self.card_signed.set_value("0")
            return

        # Metrics
        total_open_notes = sum(self.wp_service.count_open_review_notes(w.id) for w in all_wps)
        signed_count = sum(1 for w in all_wps if w.is_locked)
        self.card_total.set_value(str(len(all_wps)))
        self.card_open_notes.set_value(str(total_open_notes))
        self.card_signed.set_value(str(signed_count))

        # Filter
        if self.radio_paf.isChecked():
            wps = [w for w in all_wps if getattr(w, "file_category", FileCategoryEnum.CURRENT_FILE) == FileCategoryEnum.PERMANENT_FILE]
        elif self.radio_caf.isChecked():
            wps = [w for w in all_wps if getattr(w, "file_category", FileCategoryEnum.CURRENT_FILE) == FileCategoryEnum.CURRENT_FILE]
        else:
            wps = all_wps

        # Populate Tree
        self.tree.clear()
        paf_root = QTreeWidgetItem(self.tree, ["Permanent Audit File (PAF)"])
        caf_root = QTreeWidgetItem(self.tree, ["Current Audit File (CAF)"])

        bold_font = QFont()
        bold_font.setBold(True)
        paf_root.setFont(0, bold_font)
        caf_root.setFont(0, bold_font)

        # Group CAF by area
        area_nodes: dict[str, QTreeWidgetItem] = {}

        for wp in wps:
            is_paf = wp.file_category == FileCategoryEnum.PERMANENT_FILE or "Permanent" in str(wp.file_category)
            status_text = f"[{wp.status.value}]"
            if wp.is_locked:
                status_text = f"🔒 [Locked v{wp.version}]"
            elif wp.version > 1:
                status_text = f"[{wp.status.value} v{wp.version}]"

            label = f"{wp.index_reference} - {wp.title}  {status_text}"
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, wp.id)

            if is_paf:
                paf_root.addChild(item)
            else:
                area_name = wp.area or "General & Administration"
                if area_name not in area_nodes:
                    area_node = QTreeWidgetItem(caf_root, [area_name])
                    area_node.setFont(0, bold_font)
                    area_nodes[area_name] = area_node
                area_nodes[area_name].addChild(item)

        self.tree.expandAll()

        # Re-select active wp or select first
        if self.active_wp_id:
            self._select_tree_wp(self.active_wp_id)
        elif wps:
            self._load_working_paper(wps[0].id)

    def _filter_tree(self, query: str) -> None:
        q = query.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            self._filter_tree_item(root, q)

    def _filter_tree_item(self, item: QTreeWidgetItem, query: str) -> bool:
        if not query:
            item.setHidden(False)
            for i in range(item.childCount()):
                self._filter_tree_item(item.child(i), query)
            return True

        has_matching_child = False
        for i in range(item.childCount()):
            child_matched = self._filter_tree_item(item.child(i), query)
            if child_matched:
                has_matching_child = True

        matches = query in item.text(0).lower() or has_matching_child
        item.setHidden(not matches)
        if matches:
            item.setExpanded(True)
        return matches

    def _select_tree_wp(self, wp_id: str) -> None:
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            found = self._find_and_select_in_item(root, wp_id)
            if found:
                break

    def _find_and_select_in_item(self, item: QTreeWidgetItem, wp_id: str) -> bool:
        if item.data(0, Qt.ItemDataRole.UserRole) == wp_id:
            self.tree.setCurrentItem(item)
            return True
        for i in range(item.childCount()):
            if self._find_and_select_in_item(item.child(i), wp_id):
                return True
        return False

    def _on_tree_selection_changed(self) -> None:
        curr = self.tree.currentItem()
        if not curr:
            return
        wp_id = curr.data(0, Qt.ItemDataRole.UserRole)
        if wp_id:
            self._load_working_paper(wp_id)

    def _clear_active_wp(self) -> None:
        self.active_wp_id = None
        self.current_workbench_data = None
        self.lbl_wp_title.setText("Select a working paper from the tree on the left.")
        self.lbl_wp_meta.setText("")
        self.lbl_objective.setText("Audit Objective: None")
        self.tbl_risks.setRowCount(0)
        self.tbl_procs.setRowCount(0)
        self.tbl_findings.setRowCount(0)
        if hasattr(self, "tbl_testing"):
            self.tbl_testing.blockSignals(True)
            self.tbl_testing.setRowCount(0)
            self.tbl_testing.blockSignals(False)
            self._recalculate_testing_totals()
        self.txt_sections_editor.clear()
        self.txt_conclusion_editor.clear()
        self.tbl_versions.setRowCount(0)
        self.txt_snapshot_view.clear()
        self.evidence_list.clear()
        self.notes_list.clear()
        self.signoffs_list.clear()
        self.lbl_review_alert.setVisible(False)

    def _load_working_paper(self, wp_id: str) -> None:
        try:
            wb = self.wp_service.get_workbench_data(wp_id)
        except Exception as ex:
            QMessageBox.critical(self, "Error Loading Working Paper", str(ex))
            return

        self.active_wp_id = wp_id
        self.current_workbench_data = wb
        wp = wb.working_paper

        # Header
        lock_badge = f"🔒 LOCKED (SHA-256: {wb.content_hash[:12]}...)" if wb.is_locked and wb.content_hash else "EDITABLE / DRAFT"
        self.lbl_wp_title.setText(f"[{wp.index_reference}] {wp.title}")

        # Check materiality context if available
        mat_info = ""
        if self.current_engagement and hasattr(self, "audit_matrix_service") and self.audit_matrix_service:
            try:
                if hasattr(self.audit_matrix_service, "get_latest_materiality"):
                    m_eval = self.audit_matrix_service.get_latest_materiality(self.current_engagement.id)
                    if m_eval and m_eval.performance_materiality:
                        mat_info = f" | <b>PM (SA 320):</b> {m_eval.performance_materiality.formatted}"
            except Exception:
                pass

        self.lbl_wp_meta.setText(
            f"<b>Area:</b> {wp.area} | <b>Category:</b> {wp.file_category.value} | <b>Status:</b> {wp.status.value} | "
            f"<b>Version:</b> v{wb.version} | <b>Preparer:</b> {wp.preparer_id} | <b>Reviewer:</b> {wp.reviewer_id or 'Unassigned'}"
            f"{mat_info} | <b>Integrity:</b> <span style='color: {'#16A34A' if wb.is_locked else '#2563EB'};'>{lock_badge}</span>"
        )

        # Tab 1: Objectives & Canonical Graph
        self.lbl_objective.setText(f"<b>Audit Objective:</b> {wb.objective}")

        # Risks Table
        self.tbl_risks.setRowCount(0)
        for r_idx, risk in enumerate(wb.risks):
            self.tbl_risks.insertRow(r_idx)
            self.tbl_risks.setItem(r_idx, 0, QTableWidgetItem(risk.risk_code))
            self.tbl_risks.setItem(r_idx, 1, QTableWidgetItem(risk.title))
            self.tbl_risks.setItem(r_idx, 2, QTableWidgetItem(str(risk.inherent_risk.value if hasattr(risk.inherent_risk, 'value') else risk.inherent_risk)))
            self.tbl_risks.setItem(r_idx, 3, QTableWidgetItem(str(risk.control_risk.value if hasattr(risk.control_risk, 'value') else risk.control_risk)))
            self.tbl_risks.setItem(r_idx, 4, QTableWidgetItem(str(risk.derived_romm.value if hasattr(risk.derived_romm, 'value') else risk.derived_romm)))

        # Procedures Table
        self.tbl_procs.setRowCount(0)
        for p_idx, proc in enumerate(wb.procedures):
            self.tbl_procs.insertRow(p_idx)
            self.tbl_procs.setItem(p_idx, 0, QTableWidgetItem(proc.procedure_code))
            self.tbl_procs.setItem(p_idx, 1, QTableWidgetItem(proc.objective))
            self.tbl_procs.setItem(p_idx, 2, QTableWidgetItem(proc.population_definition or wb.population))
            samples_count = sum(1 for s in wb.samples if s["procedure_id"] == proc.id)
            self.tbl_procs.setItem(p_idx, 3, QTableWidgetItem(f"{samples_count} sampled"))
            self.tbl_procs.setItem(p_idx, 4, QTableWidgetItem(proc.status.value))

        # Findings Table
        self.tbl_findings.setRowCount(0)
        for f_idx, finding in enumerate(wb.findings):
            self.tbl_findings.insertRow(f_idx)
            self.tbl_findings.setItem(f_idx, 0, QTableWidgetItem(finding.title))
            self.tbl_findings.setItem(f_idx, 1, QTableWidgetItem(str(finding.severity.value if hasattr(finding.severity, 'value') else finding.severity)))
            amt_str = f"₹{finding.amount_paise / 100:,.2f}" if finding.amount_paise else "N/A"
            self.tbl_findings.setItem(f_idx, 2, QTableWidgetItem(amt_str))
            self.tbl_findings.setItem(f_idx, 3, QTableWidgetItem(finding.status.value))

        # Tab 2: Load Testing Grid from sections
        self._load_testing_grid_from_sections(wb.sections)
        self.tbl_testing.setEnabled(not wb.is_locked)
        self.btn_add_test_row.setEnabled(not wb.is_locked)
        self.btn_del_test_row.setEnabled(not wb.is_locked)
        self.btn_sampling_tool.setEnabled(not wb.is_locked)
        self.btn_save_grid.setEnabled(not wb.is_locked)

        # Tab 3: Sections Content Editor
        sections_text = []
        for s in wb.sections:
            if s.title.strip() not in ("Substantive Testing Grid", "Testing Grid"):
                sections_text.append(f"## {s.title}\n{s.content_markdown}\n")
        self.txt_sections_editor.setText("\n".join(sections_text))
        self.txt_sections_editor.setReadOnly(wb.is_locked)
        self.btn_save_content.setEnabled(not wb.is_locked)

        # Tab 4: Conclusion Editor
        self.txt_conclusion_editor.setText(wb.conclusion)
        self.txt_conclusion_editor.setReadOnly(wb.is_locked)
        self.btn_save_conclusion.setEnabled(not wb.is_locked)

        # Tab 5: Version History Table
        self.tbl_versions.setRowCount(0)
        for v_idx, snap in enumerate(wb.historical_versions):
            self.tbl_versions.insertRow(v_idx)
            self.tbl_versions.setItem(v_idx, 0, QTableWidgetItem(f"v{snap.version}"))
            self.tbl_versions.setItem(v_idx, 1, QTableWidgetItem(snap.status))
            self.tbl_versions.setItem(v_idx, 2, QTableWidgetItem(snap.preparer_id))
            hash_abbr = f"{snap.content_hash[:12]}..." if snap.content_hash else "Unsealed"
            self.tbl_versions.setItem(v_idx, 3, QTableWidgetItem(hash_abbr))
            self.tbl_versions.setItem(v_idx, 4, QTableWidgetItem(snap.created_at_iso[:19]))
        self.txt_snapshot_view.clear()

        # Action Buttons State based on lifecycle
        is_locked = wb.is_locked
        status = wp.status
        self.btn_submit.setEnabled(not is_locked and status in (WorkingPaperStatusEnum.DRAFT, WorkingPaperStatusEnum.RETURNED))
        self.btn_review.setEnabled(not is_locked and status in (WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW, WorkingPaperStatusEnum.RESUBMITTED))
        self.btn_return.setEnabled(not is_locked and status == WorkingPaperStatusEnum.UNDER_REVIEW)
        self.btn_approve.setEnabled(not is_locked and status == WorkingPaperStatusEnum.UNDER_REVIEW)
        self.btn_signoff.setEnabled(not is_locked and status in (WorkingPaperStatusEnum.UNDER_REVIEW, WorkingPaperStatusEnum.APPROVED))
        self.btn_reopen.setEnabled(is_locked)

        # RIGHT PANE: Evidence List
        self.evidence_list.clear()
        if wb.evidence_items:
            for ev in wb.evidence_items:
                hash_text = f"SHA-256: {ev.content_hash[:8]}..." if ev.content_hash else "No Hash"
                item_text = f"📄 {ev.title} [{ev.status.value}]\n   Source: {ev.source} | Ref: {ev.excerpt_or_reference[:40]} | {hash_text}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, ev.id)
                self.evidence_list.addItem(list_item)
        else:
            self.evidence_list.addItem("No external evidence documents linked yet.")

        # Review Notes List & Alert
        self.notes_list.clear()
        if wb.open_review_notes_count > 0:
            self.lbl_review_alert.setText(f"⚠️ <b>Approval Precondition Blocked:</b> {wb.open_review_notes_count} open review point(s) must be cleared before approval/sign-off.")
            self.lbl_review_alert.setVisible(True)
        else:
            self.lbl_review_alert.setVisible(False)

        if wb.review_notes:
            for n in wb.review_notes:
                status_tag = n.status.value.upper()
                note_display = n.note_text
                pin_prefix = ""
                if note_display.startswith("[PIN:"):
                    pin_part, _, rem = note_display.partition("]")
                    pin_prefix = f"📌 {pin_part.replace('[PIN:', '').strip()} | "
                    note_display = rem.strip()
                txt = f"[{status_tag}] {pin_prefix}Raised by {n.raised_by}: {note_display}"
                if n.response_text:
                    txt += f"\n   ➜ Responded ({n.responded_by}): {n.response_text}"
                if n.cleared_by:
                    txt += f"\n   ✓ Cleared by: {n.cleared_by}"
                n_item = QListWidgetItem(txt)
                n_item.setData(Qt.ItemDataRole.UserRole, n.id)
                if n.status == ReviewNoteStatusEnum.OPEN:
                    n_item.setForeground(QColor("#D97706"))
                elif n.status == ReviewNoteStatusEnum.CLEARED:
                    n_item.setForeground(QColor("#16A34A"))
                self.notes_list.addItem(n_item)
        else:
            self.notes_list.addItem("No review notes raised on this working paper.")

        # Sign-Offs List
        self.signoffs_list.clear()
        if wb.sign_offs:
            for s in wb.sign_offs:
                udin_str = ""
                if s.note and "[UDIN:" in s.note:
                    u_part = s.note.split("[UDIN:")[1].split("]")[0].strip()
                    udin_str = f" | UDIN: {u_part}"
                self.signoffs_list.addItem(
                    f"✓ {s.level.value} by {s.user_role} {s.user_id}{udin_str}\n  Hash: {s.content_hash[:16]}... | {s.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
        else:
            self.signoffs_list.addItem("No electronic sign-offs recorded yet.")

    def _on_version_selected(self) -> None:
        selected = self.tbl_versions.selectedItems()
        if not selected or not self.current_workbench_data:
            return
        row = selected[0].row()
        if row < len(self.current_workbench_data.historical_versions):
            snap = self.current_workbench_data.historical_versions[row]
            lines = [
                f"=== HISTORICAL VERSION SNAPSHOT: v{snap.version} ===",
                f"Title: {snap.title}",
                f"Area: {snap.area} | Status: {snap.status}",
                f"Preparer: {snap.preparer_id} | Reviewer: {snap.reviewer_id or 'None'}",
                f"Content Hash: {snap.content_hash or 'None'}",
                f"Archived At: {snap.created_at_iso}",
                f"Conclusion: {snap.conclusion}\n",
                "--- SECTIONS CONTENT ---",
            ]
            for s in snap.sections:
                lines.append(f"\n▶ {s.get('title', 'Section')}\n{s.get('content_markdown', '')}")
            self.txt_snapshot_view.setText("\n".join(lines))

    def _on_save_content_clicked(self) -> None:
        if not self.active_wp_id:
            return
        raw_text = self.txt_sections_editor.toPlainText()
        # Parse into sections based on ## headers or default single section
        sections_list = []
        raw_blocks = raw_text.split("## ")
        for block in raw_blocks:
            if not block.strip():
                continue
            lines = block.splitlines()
            title = lines[0].strip() if lines else "Section"
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
            sections_list.append({"title": title, "content_markdown": body})

        if not sections_list:
            sections_list = [{"title": "Work Done & Testing", "content_markdown": raw_text}]

        editor = self.user_session.username if self.user_session else "Auditor"
        try:
            wb = self.current_workbench_data
            self.wp_service.update_working_paper_content(
                wp_id=self.active_wp_id,
                title=wb.working_paper.title if wb else "Working Paper",
                area=wb.working_paper.area if wb else "General",
                conclusion=self.txt_conclusion_editor.toPlainText().strip(),
                sections_list=sections_list,
                editor_id=editor,
            )
            QMessageBox.information(self, "Saved", "Working paper documentation saved successfully.")
            self._load_working_paper(self.active_wp_id)
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Save Error", str(ex))

    def _on_save_conclusion_clicked(self) -> None:
        if not self.active_wp_id or not self.current_workbench_data:
            return
        conc_text = self.txt_conclusion_editor.toPlainText().strip()
        editor = self.user_session.username if self.user_session else "Auditor"
        wb = self.current_workbench_data
        sections_data = [{"title": s.title, "content_markdown": s.content_markdown} for s in wb.sections]
        try:
            self.wp_service.update_working_paper_content(
                wp_id=self.active_wp_id,
                title=wb.working_paper.title,
                area=wb.working_paper.area,
                conclusion=conc_text,
                sections_list=sections_data,
                editor_id=editor,
            )
            QMessageBox.information(self, "Saved", "Auditor conclusion saved successfully.")
            self._load_working_paper(self.active_wp_id)
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Save Error", str(ex))

    def _on_submit_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_id = self.user_session.username if self.user_session else "Lead Auditor"
        try:
            self.wp_service.submit_for_review(self.active_wp_id, user_id)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Submit Error", str(ex))

    def _on_start_review_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_id = self.user_session.username if self.user_session else "Reviewer"
        try:
            self.wp_service.start_review(self.active_wp_id, user_id)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Review Error", str(ex))

    def _on_return_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_id = self.user_session.username if self.user_session else "Reviewer"
        try:
            self.wp_service.return_working_paper(self.active_wp_id, user_id)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Return Error", str(ex))

    def _on_approve_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_id = self.user_session.username if self.user_session else "Reviewer"
        try:
            self.wp_service.approve_working_paper(self.active_wp_id, user_id)
            QMessageBox.information(self, "Approved", "Working paper approved successfully.")
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Approval Blocked", str(ex))

    def _on_signoff_clicked(self) -> None:
        if not self.active_wp_id:
            return
        wp = self.wp_service.get_working_paper(self.active_wp_id)
        if SignOffDialog(wp, self.wp_service, user_session=self.user_session, parent=self).exec():
            self.refresh()
            self.wp_changed.emit()

    def _on_reopen_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_name = self.user_session.username if self.user_session else "Partner"
        reason, ok = QInputDialog.getText(self, "Reopen Working Paper (Partner)", "Enter reason for reopening paper to create new version:")
        if ok and reason.strip():
            try:
                self.wp_service.reopen_working_paper(
                    ReopenWorkingPaperDTO(
                        working_paper_id=self.active_wp_id,
                        reopened_by=user_name,
                        reason=reason.strip(),
                    )
                )
                QMessageBox.information(self, "Reopened", "Working paper reopened. A new version draft has been created and historical version sealed.")
                self.refresh()
                self.wp_changed.emit()
            except Exception as ex:
                QMessageBox.critical(self, "Reopen Error", str(ex))

    def _on_verify_hash_clicked(self) -> None:
        if not self.active_wp_id:
            return
        is_valid, msg = self.wp_service.verify_integrity(self.active_wp_id)
        if is_valid:
            QMessageBox.information(self, "Integrity Verified", msg)
        else:
            QMessageBox.critical(self, "TAMPER DETECTED", msg)

    def _on_raise_note_clicked(self) -> None:
        if not self.active_wp_id:
            return
        author = self.user_session.username if self.user_session else "Reviewer"

        # Check if there is an active selection in the testing grid
        default_ref = ""
        if hasattr(self, "tbl_testing") and self.tbl_testing.currentRow() >= 0:
            row_num = self.tbl_testing.currentRow() + 1
            v_ref = self.tbl_testing.item(self.tbl_testing.currentRow(), 1)
            v_str = f" ({v_ref.text()})" if v_ref and v_ref.text() else ""
            default_ref = f"Testing Grid Row #{row_num}{v_str}"

        dlg = QDialog(self)
        dlg.setWindowTitle("Raise Line-Pinned Review Note")
        dlg.resize(480, 220)
        d_layout = QVBoxLayout(dlg)

        form = QFormLayout()
        ref_input = QLineEdit(default_ref)
        ref_input.setPlaceholderText("e.g. 'Testing Grid Row #3', 'Procedure PROC-01', 'Section 1'...")
        note_input = QTextEdit()
        note_input.setPlaceholderText("Enter specific review query or deficiency for preparer...")
        note_input.setMaximumHeight(80)

        form.addRow("Line / Section Pin:", ref_input)
        form.addRow("Review Point:", note_input)
        d_layout.addLayout(form)

        b_box = QHBoxLayout()
        b_box.addStretch()
        b_ok = QPushButton("Raise Note")
        b_ok.setStyleSheet("background: #2563EB; color: white; font-weight: 600; padding: 6px 14px; border-radius: 4px;")
        b_cancel = QPushButton("Cancel")
        b_ok.clicked.connect(dlg.accept)
        b_cancel.clicked.connect(dlg.reject)
        b_box.addWidget(b_cancel)
        b_box.addWidget(b_ok)
        d_layout.addLayout(b_box)

        if dlg.exec() and note_input.toPlainText().strip():
            ref = ref_input.text().strip()
            txt = note_input.toPlainText().strip()
            final_note = f"[PIN: {ref}] {txt}" if ref else txt
            self.wp_service.raise_review_note(
                CreateReviewNoteDTO(
                    working_paper_id=self.active_wp_id,
                    raised_by=author,
                    note_text=final_note,
                    section_id=ref[:36] if ref else None,
                )
            )
            self._load_working_paper(self.active_wp_id)
            self.refresh()
            self.wp_changed.emit()

    def _on_open_threaded_notes_clicked(self) -> None:
        if not self.active_wp_id:
            return
        user_name = self.user_session.username if self.user_session else "Auditor"
        role = (
            self.user_session.role.value
            if self.user_session and hasattr(self.user_session.role, "value")
            else "Manager"
        )
        dlg = ReviewNotesDialog(
            working_paper_id=self.active_wp_id,
            working_paper_service=self.wp_service,
            current_user=user_name,
            user_role=role,
            parent=self,
        )
        dlg.exec()
        self._load_working_paper(self.active_wp_id)
        self.refresh()
        self.wp_changed.emit()

    def _on_respond_note_clicked(self) -> None:
        curr = self.notes_list.currentItem()
        if not curr:
            QMessageBox.warning(self, "Select Note", "Please select a review note to respond to.")
            return
        note_id = curr.data(Qt.ItemDataRole.UserRole)
        if not note_id:
            return
        responder = self.user_session.username if self.user_session else "Preparer"
        resp, ok = QInputDialog.getText(self, "Respond to Review Note", "Enter response:")
        if ok and resp.strip():
            self.wp_service.respond_review_note(
                RespondReviewNoteDTO(
                    review_note_id=note_id,
                    response_text=resp.strip(),
                    responder=responder,
                )
            )
            self._load_working_paper(self.active_wp_id)
            self.refresh()
            self.wp_changed.emit()

    def _on_clear_note_clicked(self) -> None:
        curr = self.notes_list.currentItem()
        if not curr:
            QMessageBox.warning(self, "Select Note", "Please select a review note to clear.")
            return
        note_id = curr.data(Qt.ItemDataRole.UserRole)
        if not note_id:
            return
        reviewer = self.user_session.username if self.user_session else "Reviewer"
        try:
            self.wp_service.clear_review_note(
                ClearReviewNoteDTO(
                    review_note_id=note_id,
                    reviewer=reviewer,
                )
            )
            self._load_working_paper(self.active_wp_id)
            self.refresh()
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Clear Note Error", str(ex))

    def _on_new_wp_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        ref, ok1 = QInputDialog.getText(self, "New Working Paper", "Enter Reference Code (e.g. WP-REV-001):")
        if not ok1 or not ref.strip():
            return
        title, ok2 = QInputDialog.getText(self, "New Working Paper", "Enter Title:")
        if not ok2 or not title.strip():
            return
        area, ok3 = QInputDialog.getText(self, "New Working Paper", "Enter Audit Area (e.g. C. Revenue & Receivables):")
        if not ok3 or not area.strip():
            area = "General"

        preparer = self.user_session.username if self.user_session else "Lead Auditor"
        wp = self.wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=self.current_engagement.id,
                index_reference=ref.strip(),
                title=title.strip(),
                area=area.strip(),
                preparer_id=preparer,
            )
        )
        self.refresh()
        self._load_working_paper(wp.id)
        self.wp_changed.emit()

    def _on_scaffold_paf_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        created = self.wp_service.scaffold_permanent_audit_file(self.current_engagement.id)
        msg = f"Successfully initialized {len(created)} permanent statutory records." if created else "All standard PAF records already exist."
        QMessageBox.information(self, "Permanent Audit File", msg)
        self.refresh()
        self.wp_changed.emit()

    def _on_scaffold_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        created = self.wp_service.scaffold_schedule_iii_working_papers(self.current_engagement.id)
        msg = f"Successfully generated {len(created)} standard Schedule III working papers." if created else "All standard Schedule III working papers already exist."
        QMessageBox.information(self, "Schedule III Folders", msg)
        self.refresh()
        self.wp_changed.emit()

    # =========================================================================
    # Substantive Testing Grid & Audit Tick-Marks Implementation
    # =========================================================================

    def _init_testing_tab(self) -> None:
        self.tab_testing = QWidget()
        layout = QVBoxLayout(self.tab_testing)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Audit Tick Marks Quick-Insert Toolbar
        tick_frame = QFrame()
        tick_frame.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 4px;")
        tick_layout = QHBoxLayout(tick_frame)
        tick_layout.setContentsMargins(4, 2, 4, 2)
        tick_layout.setSpacing(4)

        lbl_ticks = QLabel("<b>Audit Ticks:</b>")
        lbl_ticks.setStyleSheet("font-size: 11px; color: #475569;")
        tick_layout.addWidget(lbl_ticks)

        self.tick_buttons = [
            ("^ Footed", "^", "Footed / Casted (Arithmetic Sum Verified)"),
            ("§ Agreed to GL", "§", "Agreed to General Ledger / Trial Balance"),
            ("© Confirmed", "©", "External Direct Confirmation Received (SA 505)"),
            ("T Tax Verified", "T", "Agreed to GST Portal / Tax Invoice / E-Way Bill"),
            ("V Physical", "V", "Physical Verification Inspected (SA 501)"),
            ("R Recalculated", "R", "Arithmetic / Depreciation Recalculated (SA 520)"),
            ("— Clear", "", "Clear Tick Mark"),
        ]
        for btn_label, symbol, tooltip in self.tick_buttons:
            btn = QPushButton(btn_label)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; "
                "border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 500; } "
                "QPushButton:hover { background: #EFF6FF; color: #2563EB; border-color: #93C5FD; }"
            )
            btn.clicked.connect(lambda _, s=symbol: self._apply_tick_mark(s))
            tick_layout.addWidget(btn)

        tick_layout.addStretch()
        layout.addWidget(tick_frame)

        # 2. Grid Management Action Row
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self.btn_add_test_row = QPushButton("+ Add Test Row")
        self.btn_add_test_row.setStyleSheet("background: #2563EB; color: white; font-weight: 600; padding: 5px 12px; border-radius: 4px; font-size: 12px;")
        self.btn_add_test_row.clicked.connect(self._on_add_test_row_clicked)

        self.btn_del_test_row = QPushButton("- Remove Row")
        self.btn_del_test_row.setStyleSheet("background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; font-weight: 500; padding: 5px 12px; border-radius: 4px; font-size: 12px;")
        self.btn_del_test_row.clicked.connect(self._on_del_test_row_clicked)

        self.btn_sampling_tool = QPushButton("SA 530 Sampling Calculator")
        self.btn_sampling_tool.setStyleSheet("background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; font-weight: 600; padding: 5px 12px; border-radius: 4px; font-size: 12px;")
        self.btn_sampling_tool.clicked.connect(self._on_open_sampling_calculator)

        self.btn_save_grid = QPushButton("Save Grid to WP")
        self.btn_save_grid.setStyleSheet("background: #0284C7; color: white; font-weight: 600; padding: 5px 14px; border-radius: 4px; font-size: 12px;")
        self.btn_save_grid.clicked.connect(self._on_save_grid_clicked)

        action_row.addWidget(self.btn_add_test_row)
        action_row.addWidget(self.btn_del_test_row)
        action_row.addWidget(self.btn_sampling_tool)
        action_row.addStretch()
        action_row.addWidget(self.btn_save_grid)
        layout.addLayout(action_row)

        # 3. Interactive Table Widget
        self.tbl_testing = QTableWidget()
        self.tbl_testing.setColumnCount(10)
        self.tbl_testing.setHorizontalHeaderLabels([
            "#", "VOUCHER / REF", "DATE", "ACCOUNT / PARTICULARS", "BOOK AMT (₹)",
            "AUDITED AMT (₹)", "VARIANCE (₹)", "TICK", "REMARKS", "STATUS"
        ])
        self.tbl_testing.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_testing.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        for c in [0, 1, 2, 4, 5, 6, 7, 9]:
            self.tbl_testing.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_testing.verticalHeader().setVisible(False)
        self.tbl_testing.setAlternatingRowColors(True)
        self.tbl_testing.itemChanged.connect(self._on_testing_grid_cell_changed)
        layout.addWidget(self.tbl_testing, 1)

        # 4. Summary Strip
        self.testing_summary_strip = QFrame()
        self.testing_summary_strip.setStyleSheet(
            "background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 12px;"
        )
        sum_layout = QHBoxLayout(self.testing_summary_strip)
        sum_layout.setContentsMargins(8, 4, 8, 4)

        self.lbl_sum_count = QLabel("Tested: 0 items")
        self.lbl_sum_count.setStyleSheet("font-size: 12px; font-weight: 600; color: #334155;")
        self.lbl_sum_book = QLabel("Book Total: ₹0.00")
        self.lbl_sum_book.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B;")
        self.lbl_sum_audited = QLabel("Audited Total: ₹0.00")
        self.lbl_sum_audited.setStyleSheet("font-size: 12px; font-weight: 600; color: #1E293B;")
        self.lbl_sum_diff = QLabel("Net Variance: ₹0.00")
        self.lbl_sum_diff.setStyleSheet("font-size: 12px; font-weight: 700; color: #16A34A;")

        sum_layout.addWidget(self.lbl_sum_count)
        sum_layout.addSpacing(16)
        sum_layout.addWidget(self.lbl_sum_book)
        sum_layout.addSpacing(16)
        sum_layout.addWidget(self.lbl_sum_audited)
        sum_layout.addSpacing(16)
        sum_layout.addWidget(self.lbl_sum_diff)
        sum_layout.addStretch()
        layout.addWidget(self.testing_summary_strip)

    def _apply_tick_mark(self, symbol: str) -> None:
        selected_rows = set(item.row() for item in self.tbl_testing.selectedItems())
        if not selected_rows and self.tbl_testing.currentRow() >= 0:
            selected_rows = {self.tbl_testing.currentRow()}
        if not selected_rows:
            QMessageBox.information(
                self, "Select Row",
                "Please select one or more rows in the testing grid to apply the tick mark."
            )
            return

        self.tbl_testing.blockSignals(True)
        for r in selected_rows:
            item = self.tbl_testing.item(r, 7)
            if not item:
                item = QTableWidgetItem(symbol)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_testing.setItem(r, 7, item)
            else:
                item.setText(symbol)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tbl_testing.blockSignals(False)

    def _on_add_test_row_clicked(self) -> None:
        self.tbl_testing.blockSignals(True)
        r_idx = self.tbl_testing.rowCount()
        self.tbl_testing.insertRow(r_idx)
        self.tbl_testing.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
        self.tbl_testing.setItem(r_idx, 1, QTableWidgetItem(f"VR-{r_idx+1:03d}"))
        self.tbl_testing.setItem(r_idx, 2, QTableWidgetItem(""))
        self.tbl_testing.setItem(r_idx, 3, QTableWidgetItem(""))
        self.tbl_testing.setItem(r_idx, 4, QTableWidgetItem("0.00"))
        self.tbl_testing.setItem(r_idx, 5, QTableWidgetItem("0.00"))
        self.tbl_testing.setItem(r_idx, 6, QTableWidgetItem("0.00"))
        self.tbl_testing.setItem(r_idx, 7, QTableWidgetItem(""))
        self.tbl_testing.setItem(r_idx, 8, QTableWidgetItem(""))
        self.tbl_testing.setItem(r_idx, 9, QTableWidgetItem("Reconciled"))
        self.tbl_testing.blockSignals(False)
        self._recalculate_testing_totals()

    def _on_del_test_row_clicked(self) -> None:
        selected_rows = sorted(set(item.row() for item in self.tbl_testing.selectedItems()), reverse=True)
        if not selected_rows and self.tbl_testing.currentRow() >= 0:
            selected_rows = [self.tbl_testing.currentRow()]
        if not selected_rows:
            return

        self.tbl_testing.blockSignals(True)
        for r in selected_rows:
            self.tbl_testing.removeRow(r)
        # Re-number rows
        for r in range(self.tbl_testing.rowCount()):
            num_item = self.tbl_testing.item(r, 0)
            if num_item:
                num_item.setText(str(r + 1))
        self.tbl_testing.blockSignals(False)
        self._recalculate_testing_totals()

    def _on_open_sampling_calculator(self) -> None:
        tm_paise = None
        if self.current_engagement and hasattr(self, "audit_matrix_service") and self.audit_matrix_service:
            try:
                if hasattr(self.audit_matrix_service, "get_latest_materiality"):
                    mat = self.audit_matrix_service.get_latest_materiality(self.current_engagement.id)
                    if mat and mat.performance_materiality:
                        tm_paise = mat.performance_materiality.amount_paise
            except Exception:
                pass

        dlg = SamplingCalculatorDialog(tolerable_misstatement_paise=tm_paise, parent=self)
        if dlg.exec():
            n = dlg.calculated_sample_size
            if n > 0:
                self.tbl_testing.blockSignals(True)
                cur_rows = self.tbl_testing.rowCount()
                for i in range(n):
                    r_idx = cur_rows + i
                    self.tbl_testing.insertRow(r_idx)
                    self.tbl_testing.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
                    self.tbl_testing.setItem(r_idx, 1, QTableWidgetItem(f"SMP-{r_idx+1:03d}"))
                    self.tbl_testing.setItem(r_idx, 2, QTableWidgetItem(""))
                    self.tbl_testing.setItem(r_idx, 3, QTableWidgetItem("Sample Item Tested"))
                    self.tbl_testing.setItem(r_idx, 4, QTableWidgetItem("0.00"))
                    self.tbl_testing.setItem(r_idx, 5, QTableWidgetItem("0.00"))
                    self.tbl_testing.setItem(r_idx, 6, QTableWidgetItem("0.00"))
                    self.tbl_testing.setItem(r_idx, 7, QTableWidgetItem(""))
                    self.tbl_testing.setItem(r_idx, 8, QTableWidgetItem(""))
                    self.tbl_testing.setItem(r_idx, 9, QTableWidgetItem("Pending Testing"))
                self.tbl_testing.blockSignals(False)
                self._recalculate_testing_totals()
                QMessageBox.information(
                    self, "Samples Seeded",
                    f"Successfully generated {n} sample execution rows in the testing grid per SA 530."
                )

    def _on_testing_grid_cell_changed(self, item: QTableWidgetItem) -> None:
        col = item.column()
        row = item.row()
        if col in (4, 5):  # Book or Audited Amount changed
            try:
                b_text = self.tbl_testing.item(row, 4).text().replace(",", "").strip() if self.tbl_testing.item(row, 4) else "0"
                a_text = self.tbl_testing.item(row, 5).text().replace(",", "").strip() if self.tbl_testing.item(row, 5) else "0"
                b_val = float(b_text) if b_text else 0.0
                a_val = float(a_text) if a_text else 0.0
                diff = b_val - a_val

                self.tbl_testing.blockSignals(True)
                diff_item = self.tbl_testing.item(row, 6)
                diff_str = f"{diff:,.2f}"
                if not diff_item:
                    diff_item = QTableWidgetItem(diff_str)
                    self.tbl_testing.setItem(row, 6, diff_item)
                else:
                    diff_item.setText(diff_str)

                # Set color
                if abs(diff) > 0.001:
                    diff_item.setForeground(QColor("#DC2626"))
                    st_item = self.tbl_testing.item(row, 9)
                    if st_item and st_item.text() in ("Reconciled", "Pending Testing"):
                        st_item.setText("Variance Flagged")
                else:
                    diff_item.setForeground(QColor("#16A34A"))
                self.tbl_testing.blockSignals(False)

            except Exception:
                pass
            self._recalculate_testing_totals()

    def _recalculate_testing_totals(self) -> None:
        count = self.tbl_testing.rowCount()
        total_book = 0.0
        total_aud = 0.0
        total_diff = 0.0

        for r in range(count):
            try:
                b_t = self.tbl_testing.item(r, 4).text().replace(",", "").strip() if self.tbl_testing.item(r, 4) else "0"
                a_t = self.tbl_testing.item(r, 5).text().replace(",", "").strip() if self.tbl_testing.item(r, 5) else "0"
                d_t = self.tbl_testing.item(r, 6).text().replace(",", "").strip() if self.tbl_testing.item(r, 6) else "0"
                total_book += float(b_t) if b_t else 0.0
                total_aud += float(a_t) if a_t else 0.0
                total_diff += float(d_t) if d_t else 0.0
            except Exception:
                pass

        self.lbl_sum_count.setText(f"Tested: {count} items")
        self.lbl_sum_book.setText(f"Book Total: ₹{total_book:,.2f}")
        self.lbl_sum_audited.setText(f"Audited Total: ₹{total_aud:,.2f}")

        if abs(total_diff) > 0.001:
            self.lbl_sum_diff.setText(f"⚠️ Net Variance: ₹{total_diff:,.2f}")
            self.lbl_sum_diff.setStyleSheet("font-size: 12px; font-weight: 700; color: #DC2626;")
        else:
            self.lbl_sum_diff.setText("✓ Net Variance: ₹0.00")
            self.lbl_sum_diff.setStyleSheet("font-size: 12px; font-weight: 700; color: #16A34A;")

    def _load_testing_grid_from_sections(self, sections: list[Any]) -> None:
        self.tbl_testing.blockSignals(True)
        self.tbl_testing.setRowCount(0)
        grid_section = None
        for s in sections:
            if s.title.strip() in ("Substantive Testing Grid", "Testing Grid"):
                grid_section = s
                break

        if grid_section and grid_section.content_markdown:
            content = grid_section.content_markdown
            rows = []
            if "<!-- GRID_JSON:" in content:
                try:
                    raw_json = content.split("<!-- GRID_JSON:")[1].split("-->")[0].strip()
                    rows = json.loads(raw_json)
                except Exception:
                    rows = []
            if not rows:
                for line in content.splitlines():
                    if line.startswith("|") and not line.startswith("|---") and not line.startswith("| #") and not line.startswith("| ROW"):
                        parts = [p.strip() for p in line.strip("|").split("|")]
                        if len(parts) >= 8:
                            rows.append({
                                "ref": parts[1] if len(parts) > 1 else "",
                                "date": parts[2] if len(parts) > 2 else "",
                                "particulars": parts[3] if len(parts) > 3 else "",
                                "book_amt": parts[4] if len(parts) > 4 else "0.00",
                                "audited_amt": parts[5] if len(parts) > 5 else "0.00",
                                "variance": parts[6] if len(parts) > 6 else "0.00",
                                "tick": parts[7] if len(parts) > 7 else "",
                                "remarks": parts[8] if len(parts) > 8 else "",
                                "status": parts[9] if len(parts) > 9 else "Reconciled",
                            })

            for r_idx, r in enumerate(rows):
                self.tbl_testing.insertRow(r_idx)
                self.tbl_testing.setItem(r_idx, 0, QTableWidgetItem(str(r_idx + 1)))
                self.tbl_testing.setItem(r_idx, 1, QTableWidgetItem(r.get("ref", "")))
                self.tbl_testing.setItem(r_idx, 2, QTableWidgetItem(r.get("date", "")))
                self.tbl_testing.setItem(r_idx, 3, QTableWidgetItem(r.get("particulars", "")))
                self.tbl_testing.setItem(r_idx, 4, QTableWidgetItem(str(r.get("book_amt", "0.00"))))
                self.tbl_testing.setItem(r_idx, 5, QTableWidgetItem(str(r.get("audited_amt", "0.00"))))
                self.tbl_testing.setItem(r_idx, 6, QTableWidgetItem(str(r.get("variance", "0.00"))))
                self.tbl_testing.setItem(r_idx, 7, QTableWidgetItem(r.get("tick", "")))
                self.tbl_testing.setItem(r_idx, 8, QTableWidgetItem(r.get("remarks", "")))
                self.tbl_testing.setItem(r_idx, 9, QTableWidgetItem(r.get("status", "Reconciled")))
        self.tbl_testing.blockSignals(False)
        self._recalculate_testing_totals()

    def _serialize_testing_grid(self) -> str:
        rows = []
        md_lines = [
            "### Substantive Testing & Tick-Marks",
            "| # | Voucher Ref | Date | Particulars | Book Amt (₹) | Audited Amt (₹) | Variance (₹) | Tick | Remarks | Status |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in range(self.tbl_testing.rowCount()):
            ref = self.tbl_testing.item(r, 1).text() if self.tbl_testing.item(r, 1) else ""
            dt = self.tbl_testing.item(r, 2).text() if self.tbl_testing.item(r, 2) else ""
            part = self.tbl_testing.item(r, 3).text() if self.tbl_testing.item(r, 3) else ""
            book = self.tbl_testing.item(r, 4).text() if self.tbl_testing.item(r, 4) else "0.00"
            aud = self.tbl_testing.item(r, 5).text() if self.tbl_testing.item(r, 5) else "0.00"
            diff = self.tbl_testing.item(r, 6).text() if self.tbl_testing.item(r, 6) else "0.00"
            tick = self.tbl_testing.item(r, 7).text() if self.tbl_testing.item(r, 7) else ""
            rem = self.tbl_testing.item(r, 8).text() if self.tbl_testing.item(r, 8) else ""
            st = self.tbl_testing.item(r, 9).text() if self.tbl_testing.item(r, 9) else "Reconciled"
            rows.append({
                "ref": ref, "date": dt, "particulars": part, "book_amt": book,
                "audited_amt": aud, "variance": diff, "tick": tick, "remarks": rem, "status": st,
            })
            md_lines.append(f"| {r+1} | {ref} | {dt} | {part} | {book} | {aud} | {diff} | {tick} | {rem} | {st} |")

        json_comment = f"\n\n<!-- GRID_JSON: {json.dumps(rows)} -->"
        return "\n".join(md_lines) + json_comment

    def _on_save_grid_clicked(self) -> None:
        if not self.active_wp_id or not self.current_workbench_data:
            return

        grid_content = self._serialize_testing_grid()
        wb = self.current_workbench_data

        # Keep existing non-grid sections and update or append the grid section
        existing_sections = []
        found_grid = False
        for s in wb.sections:
            if s.title.strip() in ("Substantive Testing Grid", "Testing Grid"):
                existing_sections.append({"title": "Substantive Testing Grid", "content_markdown": grid_content})
                found_grid = True
            else:
                existing_sections.append({"title": s.title, "content_markdown": s.content_markdown})

        if not found_grid:
            existing_sections.insert(0, {"title": "Substantive Testing Grid", "content_markdown": grid_content})

        editor = self.user_session.username if self.user_session else "Auditor"
        try:
            self.wp_service.update_working_paper_content(
                wp_id=self.active_wp_id,
                title=wb.working_paper.title,
                area=wb.working_paper.area,
                conclusion=self.txt_conclusion_editor.toPlainText().strip(),
                sections_list=existing_sections,
                editor_id=editor,
            )
            QMessageBox.information(
                self, "Testing Grid Saved",
                "Substantive testing grid successfully saved and bound to working paper documentation."
            )
            self._load_working_paper(self.active_wp_id)
            self.wp_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Save Error", str(ex))
