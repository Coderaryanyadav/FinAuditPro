"""
SA 230 Compliant Audit Working Paper Workspace for FinAuditPro.
Provides a 3-Zone Professional Audit File Management Vault (Audit File Navigator,
Working Paper Content Editor, Evidence & Reviewer Inspector) with 3-Tier Sign-Off Workflow.
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, 
                               QTextEdit, QComboBox, QTreeWidget, QTreeWidgetItem,
                               QSplitter, QHeaderView, QTabWidget, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Client, AuditProject, WorkingPaper, WorkingPaperIndex, Document, Finding
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.working_paper_service import WorkingPaperService
from security.security_manager import SecurityManager
from security.rbac import Permission
from ai.workers import OllamaWorker
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget

logger = logging.getLogger(__name__)

class InAppNotificationDialog(QDialog):
    """Custom in-app notification modal."""
    def __init__(self, title: str, message: str, is_warning: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel(title)
        fg_color = "#DC2626" if is_warning else "#2563EB"
        header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {fg_color}; border: none;")
        layout.addWidget(header)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 12px; color: #374151; line-height: 1.5; border: none;")
        layout.addWidget(msg)

        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setObjectName("primaryBtn")
        btn_ok.clicked.connect(self.accept)

        btn_r = QHBoxLayout()
        btn_r.addStretch()
        btn_r.addWidget(btn_ok)
        layout.addLayout(btn_r)

class WorkingPaperWidget(QWidget):
    """SA 230 Professional Electronic Audit Working Paper Workspace Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #F7F8FA;")
        self._active_engagement_id = None
        self._active_project_id = None
        self.active_wp_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(52)
        header.setObjectName("wpHeader")
        header.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("SA 230 Electronic Audit Working Papers")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827; letter-spacing: -0.2px; border: none;")
        subtitle = QLabel("ICAI SA 230 Electronic File Index, Substantive Evidence & Sign-Off Vault.")
        subtitle.setStyleSheet("font-size: 11px; color: #6B7280; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        self.ai_btn = QPushButton("⚡ Draft Observation")
        self.ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_btn.setObjectName("secondaryBtn")
        self.ai_btn.clicked.connect(self.generate_ai_draft)

        self.save_btn = QPushButton("Save Working Paper")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self.save_working_paper)

        h_layout.addWidget(self.ai_btn)
        h_layout.addSpacing(8)
        h_layout.addWidget(self.save_btn)
        main_layout.addWidget(header)

        # 2. Main 3-Zone Splitter Layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E5E7EB; width: 1px; }")

        # Zone 1: Audit File Index (Left 25%)
        z1_container = QFrame()
        z1_container.setStyleSheet("background-color: #FFFFFF; border-right: 1px solid #E5E7EB;")
        z1_layout = QVBoxLayout(z1_container)
        z1_layout.setContentsMargins(14, 14, 14, 14)
        z1_layout.setSpacing(8)

        z1_title = QLabel("AUDIT FILE INDEX")
        z1_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #6B7280; letter-spacing: 0.5px; border: none;")
        z1_layout.addWidget(z1_title)

        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("Filter SA 230 index...")
        self.tree_search.setObjectName("searchField")
        self.tree_search.textChanged.connect(self._filter_tree)
        z1_layout.addWidget(self.tree_search)

        self.wp_tree = QTreeWidget()
        self.wp_tree.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.wp_tree.setHeaderHidden(True)
        self.wp_tree.setStyleSheet("""
            QTreeWidget { border: 1px solid #E5E7EB; border-radius: 6px; background: #FFFFFF; outline: none; }
            QTreeWidget::item { padding: 7px 6px; color: #374151; font-size: 12px; font-weight: 500; }
            QTreeWidget::item:selected { background: #EFF6FF; color: #2563EB; font-weight: 600; border-radius: 4px; }
        """)
        self.wp_tree.itemClicked.connect(self.on_tree_item_selected)
        z1_layout.addWidget(self.wp_tree)

        splitter.addWidget(z1_container)

        # Zone 2: Working Paper Content Editor (Center 45%)
        z2_container = QFrame()
        z2_container.setStyleSheet("background-color: #FFFFFF;")
        z2_layout = QVBoxLayout(z2_container)
        z2_layout.setContentsMargins(18, 16, 18, 16)
        z2_layout.setSpacing(10)

        self.index_lbl = QLabel("Index Code: PAF-01 | MOA & Statutory Registration")
        self.index_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #111827; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; border: none;")
        z2_layout.addWidget(self.index_lbl)

        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setFrameShape(QFrame.Shape.NoFrame)
        scroll2_content = QWidget()
        s2_layout = QVBoxLayout(scroll2_content)
        s2_layout.setContentsMargins(0, 0, 0, 0)
        s2_layout.setSpacing(10)

        def add_editor_field(label_text, placeholder, is_textarea=False):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: 600; color: #6B7280; font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px; border: none;")
            s2_layout.addWidget(lbl)

            if is_textarea:
                field = QTextEdit()
                field.setFixedHeight(75)
            else:
                field = QLineEdit()
                field.setFixedHeight(34)

            field.setPlaceholderText(placeholder)
            s2_layout.addWidget(field)
            return field

        self.objective_field = add_editor_field("Audit Objective (SA 230)", "e.g. To verify legal capacity and statutory registration objects under Companies Act 2013")
        self.procedure_field = add_editor_field("Audit Procedure & Sampling Methodology (SA 330)", "e.g. Inspected certified true copy of MOA/AOA and cross-verified with MCA portal", True)
        self.evidence_field = add_editor_field("Substantive Evidence / Document Reference", "e.g. MOA_Certified_2024.pdf (SHA-256: 8f3a1...)")
        self.observation_field = add_editor_field("Audit Findings & Observations", "e.g. Main objects clause matches registered operations. Authorized capital is ₹1.5 Cr.", True)
        self.conclusion_field = add_editor_field("Auditor Conclusion & Sign-Off", "e.g. Verified and found compliant with statutory requirements.")

        scroll2.setWidget(scroll2_content)
        z2_layout.addWidget(scroll2)

        splitter.addWidget(z2_container)

        # Zone 3: Context, Evidence & Reviewer Inspector (Right 30%)
        z3_container = QFrame()
        z3_container.setStyleSheet("background-color: #F7F8FA; border-left: 1px solid #E5E7EB;")
        z3_layout = QVBoxLayout(z3_container)
        z3_layout.setContentsMargins(14, 14, 14, 14)
        z3_layout.setSpacing(10)

        # 3-Tier Sign-off Status Bar
        signoff_frame = QFrame()
        signoff_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;")
        so_layout = QVBoxLayout(signoff_frame)
        so_layout.setContentsMargins(12, 10, 12, 10)
        so_layout.setSpacing(6)

        so_title = QLabel("SIGN-OFF & REVIEW WORKFLOW")
        so_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px; border: none;")
        so_layout.addWidget(so_title)

        self.lbl_prepared = QLabel("Status: Draft Prepared")
        self.lbl_prepared.setObjectName("statusBadgeGreen")

        btn_r = QHBoxLayout()
        self.btn_review = QPushButton("Mark Reviewed")
        self.btn_review.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_review.setObjectName("secondaryBtn")
        self.btn_review.clicked.connect(self.review_working_paper)

        self.btn_approve = QPushButton("Partner Sign-Off")
        self.btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_approve.setObjectName("saveBtn")
        self.btn_approve.clicked.connect(self.approve_working_paper)

        btn_r.addWidget(self.btn_review)
        btn_r.addWidget(self.btn_approve)

        so_layout.addWidget(self.lbl_prepared)
        so_layout.addLayout(btn_r)
        z3_layout.addWidget(signoff_frame)

        # Inspector 4 Tabs
        self.inspector_tabs = QTabWidget()
        self.inspector_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e8f4; background: #ffffff; border-radius: 6px; }
            QTabBar::tab { background: #f8fafc; color: #64748b; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid #e1e8f4; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #0284c7; color: #ffffff; border-color: #0284c7; }
        """)

        # Tab 1: Evidence & Documents
        ev_w = QWidget()
        ev_l = QVBoxLayout(ev_w)
        ev_l.setContentsMargins(10, 10, 10, 10)
        self.ev_list_lbl = QLabel("Linked Evidence Files:\n• MOA_Certified_2024.pdf (Page 14)\n• MCA_Registration_Cert.pdf")
        self.ev_list_lbl.setWordWrap(True)
        self.ev_list_lbl.setStyleSheet("font-size: 11px; color: #334155; line-height: 1.4;")
        ev_l.addWidget(self.ev_list_lbl)
        ev_l.addStretch()
        self.inspector_tabs.addTab(ev_w, "Evidence (2)")

        # Tab 2: Findings
        f_w = QWidget()
        f_l = QVBoxLayout(f_w)
        f_l.setContentsMargins(10, 10, 10, 10)
        self.f_list_lbl = QLabel("Linked Audit Findings:\n• [FIND-001] Statutory DIN compliance verified.\n• [TAX-001] Missing Vendor PAN.")
        self.f_list_lbl.setWordWrap(True)
        self.f_list_lbl.setStyleSheet("font-size: 11px; color: #334155; line-height: 1.4;")
        f_l.addWidget(self.f_list_lbl)
        f_l.addStretch()
        self.inspector_tabs.addTab(f_w, "Findings (2)")

        # Tab 3: Review Notes
        rn_w = QWidget()
        rn_l = QVBoxLayout(rn_w)
        rn_l.setContentsMargins(10, 10, 10, 10)
        self.rn_list_lbl = QLabel("Review Notes Thread:\n• Senior Note #1: Verify authorized share capital against Form SH-7.\n• Status: Open")
        self.rn_list_lbl.setWordWrap(True)
        self.rn_list_lbl.setStyleSheet("font-size: 11px; color: #334155; line-height: 1.4;")
        rn_l.addWidget(self.rn_list_lbl)
        rn_l.addStretch()
        self.inspector_tabs.addTab(rn_w, "Review Notes (1)")

        z3_layout.addWidget(self.inspector_tabs, 1)

        splitter.addWidget(z3_container)
        splitter.setSizes([260, 480, 320])

        main_layout.addWidget(splitter)

        self.worker = None
        self.build_sa230_tree()
        self.load_working_paper()

    @property
    def active_engagement_id(self):
        return self._active_engagement_id

    @active_engagement_id.setter
    def active_engagement_id(self, val):
        self._active_engagement_id = val

    @property
    def active_project_id(self):
        return self._active_project_id

    @active_project_id.setter
    def active_project_id(self, val):
        self._active_project_id = val

    def load_audit_projects(self):
        """Compatibility alias for loading audit projects."""
        pass

    def refresh_data(self):
        self.load_working_paper()

    def _show_app_notification(self, title: str, message: str, is_warning: bool = False):
        dlg = InAppNotificationDialog(title, message, is_warning, self)
        dlg.exec()

    def build_sa230_tree(self):
        self.wp_tree.clear()

        # Permanent Audit File (PAF)
        paf_root = QTreeWidgetItem([" Permanent Audit File (PAF)"])
        paf_root.setFont(0, QFont("Inter", 10, QFont.Weight.Bold))
        
        paf_1 = QTreeWidgetItem([" MOA & AOA Memorandum (PAF-01)"])
        paf_2 = QTreeWidgetItem([" Statutory Licenses & CIN (PAF-02)"])
        paf_3 = QTreeWidgetItem([" Long-Term Leases & Contracts (PAF-03)"])
        
        paf_root.addChild(paf_1)
        paf_root.addChild(paf_2)
        paf_root.addChild(paf_3)
        self.wp_tree.addTopLevelItem(paf_root)

        # Current Audit File (CAF)
        caf_root = QTreeWidgetItem([" Current Audit File (CAF)"])
        caf_root.setFont(0, QFont("Inter", 10, QFont.Weight.Bold))

        sec_a = QTreeWidgetItem([" Section A: Planning & Materiality"])
        sec_a.addChild(QTreeWidgetItem([" Engagement Letter & Scope (CAF-A1)"]))
        sec_a.addChild(QTreeWidgetItem([" Materiality Calculation SA 320 (CAF-A2)"]))
        sec_a.addChild(QTreeWidgetItem([" Audit Risk Assessment (CAF-A3)"]))

        sec_b = QTreeWidgetItem([" Section B: Financial Statements"])
        sec_b.addChild(QTreeWidgetItem([" Schedule III Trial Balance Mapping (CAF-B1)"]))
        sec_b.addChild(QTreeWidgetItem([" Bank Reconciliation Summary (CAF-B2)"]))

        sec_c = QTreeWidgetItem([" Section C: Asset & Liability Verification"])
        sec_c.addChild(QTreeWidgetItem([" Fixed Assets & Physical Verification (CAF-C1)"]))
        sec_c.addChild(QTreeWidgetItem([" Trade Debtors Direct Confirmation (CAF-C2)"]))
        sec_c.addChild(QTreeWidgetItem([" Trade Creditors & Liabilities (CAF-C3)"]))

        sec_d = QTreeWidgetItem([" Section D: Statutory Reports"])
        sec_d.addChild(QTreeWidgetItem([" CARO 2020 21 Clauses Checklist (CAF-D1)"]))
        sec_d.addChild(QTreeWidgetItem([" Tax Audit Form 3CD Workings (CAF-D2)"]))

        caf_root.addChild(sec_a)
        caf_root.addChild(sec_b)
        caf_root.addChild(sec_c)
        caf_root.addChild(sec_d)

        self.wp_tree.addTopLevelItem(caf_root)
        self.wp_tree.expandAll()

    def _filter_tree(self, text: str):
        query = text.strip().lower()
        def filter_item(item):
            match = not query or query in item.text(0).lower()
            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True
            visible = match or child_match
            item.setHidden(not visible)
            return visible

        for i in range(self.wp_tree.topLevelItemCount()):
            filter_item(self.wp_tree.topLevelItem(i))

    def on_tree_item_selected(self, item, col):
        text = item.text(0)
        if "(" in text and ")" in text:
            code = text.split("(")[1].split(")")[0]
            self.index_lbl.setText(f"Index Code: {code} | {text}")
            self.load_working_paper()

    def load_working_paper(self):
        active_id = getattr(self, 'active_engagement_id', 1) or 1

        with get_session() as session:
            wp = session.query(WorkingPaper).filter_by(audit_id=active_id).first()
            if wp:
                self.objective_field.setText(wp.objective or "To verify legal capacity and statutory registration objects under Companies Act 2013.")
                self.procedure_field.setPlainText(wp.procedure or "Inspected certified true copy of MOA/AOA and cross-verified with MCA portal.")
                self.evidence_field.setText(wp.evidence or "MOA_Certified_2024.pdf (SHA-256: 8f3a1...)")
                self.observation_field.setPlainText(wp.observation or "Main objects clause matches registered operations. Authorized capital is ₹1.5 Cr.")
                self.conclusion_field.setText(wp.conclusion or "Verified and found compliant with statutory requirements under SA 230.")
                
                st = wp.status or "Draft"
                if st in ["Reviewed", "Completed"]:
                    self.lbl_prepared.setText(f"Status: {st} (Senior Auditor Signed Off)")
                    self.lbl_prepared.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; background: #e0f2fe; padding: 4px 8px; border-radius: 4px;")
                else:
                    self.lbl_prepared.setText("Status: Draft Prepared")
                    self.lbl_prepared.setStyleSheet("font-size: 11px; font-weight: 700; color: #047857; background: #dcfce7; padding: 4px 8px; border-radius: 4px;")

    def save_working_paper(self):
        active_id = getattr(self, 'active_engagement_id', 1) or 1

        try:
            with get_session() as session:
                wp = session.query(WorkingPaper).filter_by(audit_id=active_id).first()
                if not wp:
                    wp_idx = session.query(WorkingPaperIndex).filter_by(engagement_id=active_id).first()
                    if not wp_idx:
                        wp_idx = WorkingPaperIndex(engagement_id=active_id, section_code="A-100", section_name="Audit Planning & General Index")
                        session.add(wp_idx)
                        session.flush()
                    wp = WorkingPaper(audit_id=active_id, index_id=wp_idx.id)
                    session.add(wp)

                wp.objective = self.objective_field.text().strip()
                wp.procedure = self.procedure_field.toPlainText().strip()
                wp.evidence = self.evidence_field.text().strip()
                wp.observation = self.observation_field.toPlainText().strip()
                wp.conclusion = self.conclusion_field.text().strip()
                wp.status = "Prepared"

                session.commit()
            self._show_app_notification("Working Paper Saved", "Successfully persisted SA 230 audit working paper to persistent database storage.")
        except Exception as e:
            self._show_app_notification("Save Error", f"Could not save working paper: {e}", is_warning=True)

    def review_working_paper(self):
        active_id = getattr(self, 'active_engagement_id', 1) or 1
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                wp_service = WorkingPaperService(wp_repo)
                wp = session.query(WorkingPaper).filter_by(audit_id=active_id).first()
                if wp:
                    wp_service.update_status(wp, "Review")
            self.load_working_paper()
            self._show_app_notification("Senior Review Completed", "Working paper marked as Reviewed by Senior Auditor under SA 230!")
        except Exception as e:
            self._show_app_notification("Review Error", f"Failed to complete senior review: {e}", is_warning=True)

    def approve_working_paper(self):
        active_id = getattr(self, 'active_engagement_id', 1) or 1
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                wp_service = WorkingPaperService(wp_repo)
                wp = session.query(WorkingPaper).filter_by(audit_id=active_id).first()
                if wp:
                    wp_service.update_status(wp, "Completed")
            self.load_working_paper()
            self._show_app_notification("Partner Sign-Off Granted", "Final Partner Sign-off granted for this working paper!")
        except Exception as e:
            self._show_app_notification("Sign-off Error", f"Failed to complete partner sign-off: {e}", is_warning=True)

    def generate_ai_draft(self):
        obj = self.objective_field.text().strip()
        proc = self.procedure_field.toPlainText().strip()
        if not obj or not proc:
            self._show_app_notification("Required Fields Missing", "Please enter Audit Objective and Audit Procedure before generating an AI draft observation.", is_warning=True)
            return

        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("Generating...")
        self.observation_field.clear()
        self.conclusion_field.clear()

        prompt = f"Draft an ICAI audit observation and SA 230 conclusion for objective: '{obj}' and procedure: '{proc}'"
        self.worker = OllamaWorker(raw_query=prompt)
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_chunk(self, text):
        current = self.observation_field.toPlainText()
        self.observation_field.setPlainText(current + text)

    def on_ai_finished(self):
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("⚡ AI Draft Observation")
        text = self.observation_field.toPlainText()
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            conclusion = paragraphs[-1].replace("Conclusion:", "").strip()
            observation = "\n\n".join(paragraphs[:-1]).strip()
            self.observation_field.setPlainText(observation)
            self.conclusion_field.setText(conclusion)
        self._show_app_notification("AI Draft Generated", "Generated ICAI SA 230 audit observation draft successfully.")

    def closeEvent(self, event):
        event.accept()
