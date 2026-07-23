"""
SA 230 Compliant Audit Working Paper Indexing, Review & Sign-Off Engine for FinAuditPro.
Provides a 2-pane split interface with ICAI SA 230 Hierarchical File Tree (Permanent & Current Audit Files),
Substantive Evidence Attachment, Review Notes Thread, and 3-Tier Sign-Off Workflow (Prepared -> Reviewed -> Approved).
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, 
                               QTextEdit, QComboBox, QMessageBox, QTreeWidget, QTreeWidgetItem,
                               QSplitter, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from database.database import SessionLocal
from database.models import Client, AuditProject, WorkingPaper
from ai.workers import OllamaWorker
from sqlalchemy.exc import SQLAlchemyError

class WorkingPaperWidget(QWidget):
    """SA 230 Compliant Audit Working Paper Index & Review Manager."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.session = SessionLocal()
        self.active_wp = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title = QLabel("SA 230 Audit Documentation & Working Papers")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("ICAI Standard on Auditing (SA 230) Structured Audit File")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addSpacing(30)
        h_layout.addWidget(QLabel("<b style='color:#334155;'>Engagement:</b>"))
        
        self.project_combo = QComboBox()
        self.project_combo.setFixedWidth(240)
        self.project_combo.setStyleSheet("QComboBox { padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #ffffff; color: #0f172a; }")
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        h_layout.addWidget(self.project_combo)

        h_layout.addStretch()

        self.ai_btn = QPushButton("⚡ AI Draft Observation")
        self.ai_btn.setStyleSheet("background-color: #0284c7; color: white; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 12px; border: none;")
        self.ai_btn.clicked.connect(self.generate_ai_draft)

        self.save_btn = QPushButton("💾 Save Working Paper")
        self.save_btn.setStyleSheet("background-color: #0ea5e9; color: white; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 12px; border: none;")
        self.save_btn.clicked.connect(self.save_working_paper)

        h_layout.addWidget(self.ai_btn)
        h_layout.addSpacing(8)
        h_layout.addWidget(self.save_btn)
        main_layout.addWidget(header)

        # 2. Main 2-Pane Splitter View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # Left Pane: SA 230 File Tree
        left_container = QFrame()
        left_container.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 16, 16, 16)

        tree_header = QLabel("AUDIT FILE INDEX (SA 230)")
        tree_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        left_layout.addWidget(tree_header)

        self.wp_tree = QTreeWidget()
        self.wp_tree.setHeaderHidden(True)
        self.wp_tree.setStyleSheet("""
            QTreeWidget { border: 1px solid #e2e8f0; border-radius: 6px; background: #ffffff; outline: none; }
            QTreeWidget::item { padding: 8px 6px; color: #0f172a; font-size: 13px; font-weight: 500; }
            QTreeWidget::item:selected { background: #f0f9ff; color: #0284c7; font-weight: bold; }
        """)
        self.wp_tree.itemClicked.connect(self.on_tree_item_selected)
        left_layout.addWidget(self.wp_tree)

        splitter.addWidget(left_container)

        # Right Pane: Working Paper Sheet & Sign-Off Panel
        right_container = QFrame()
        right_container.setStyleSheet("background-color: #f8fafc;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(16)

        # 3-Tier Sign-Off Bar
        signoff_frame = QFrame()
        signoff_frame.setFixedHeight(54)
        signoff_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        signoff_layout = QHBoxLayout(signoff_frame)
        signoff_layout.setContentsMargins(16, 0, 16, 0)

        self.lbl_prepared = QLabel("Prepared By: Junior Assistant [Done]")
        self.lbl_prepared.setStyleSheet("font-size: 12px; font-weight: bold; color: #047857; background: #ecfdf5; padding: 4px 8px; border-radius: 4px;")

        self.btn_review = QPushButton("Mark Reviewed (Senior)")
        self.btn_review.setStyleSheet("font-size: 11px; font-weight: bold; color: #0284c7; background: #e0f2fe; border: 1px solid #bae6fd; padding: 4px 10px; border-radius: 4px;")
        self.btn_review.clicked.connect(self.review_working_paper)

        self.btn_approve = QPushButton("Final Sign-Off (Partner)")
        self.btn_approve.setStyleSheet("font-size: 11px; font-weight: bold; color: #7c3aed; background: #f5f3ff; border: 1px solid #ddd6fe; padding: 4px 10px; border-radius: 4px;")
        self.btn_approve.clicked.connect(self.approve_working_paper)

        signoff_layout.addWidget(self.lbl_prepared)
        signoff_layout.addStretch()
        signoff_layout.addWidget(self.btn_review)
        signoff_layout.addSpacing(8)
        signoff_layout.addWidget(self.btn_approve)

        right_layout.addWidget(signoff_frame)

        # Working Paper Fields Container
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        f_layout = QVBoxLayout(form_frame)
        f_layout.setSpacing(14)
        f_layout.setContentsMargins(20, 20, 20, 20)

        def add_field(label_text, placeholder, is_textarea=False):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: bold; color: #334155; font-size: 12px; border: none;")
            f_layout.addWidget(lbl)
            
            if is_textarea:
                field = QTextEdit()
                field.setFixedHeight(70)
            else:
                field = QLineEdit()
                field.setFixedHeight(36)
                
            field.setPlaceholderText(placeholder)
            field.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; color: #0f172a; font-size: 12px;")
            f_layout.addWidget(field)
            return field

        self.index_lbl = QLabel("Index Code: PAF-01 | MOA & Statutory Registration")
        self.index_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;")
        f_layout.addWidget(self.index_lbl)

        self.objective_field = add_field("Audit Objective", "e.g. To verify legal capacity and statutory registration objects under Companies Act 2013")
        self.procedure_field = add_field("Audit Procedure & Sampling Methodology", "e.g. Inspected certified true copy of MOA/AOA and cross-verified with MCA portal", True)
        self.evidence_field = add_field("Substantive Evidence / Document Reference", "e.g. MOA_Certified_2024.pdf (SHA-256: 8f3a1...)")
        self.observation_field = add_field("Audit Findings & Observations", "e.g. Main objects clause matches registered operations. Authorized capital is ₹1.5 Cr.", True)
        self.conclusion_field = add_field("Auditor Conclusion & SA Sign-Off", "e.g. Verified and found compliant with statutory requirements.")

        right_layout.addWidget(form_frame)
        splitter.addWidget(right_container)
        splitter.setSizes([380, 800])

        main_layout.addWidget(splitter)

        self.worker = None
        self.build_sa230_tree()
        self.load_audit_projects()

    def build_sa230_tree(self):
        """Constructs ICAI SA 230 Permanent and Current Audit File hierarchy."""
        self.wp_tree.clear()

        # 📁 Permanent Audit File (PAF)
        paf_root = QTreeWidgetItem(["📁 Permanent Audit File (PAF)"])
        paf_root.setFont(0, QFont("Inter", 10, QFont.Weight.Bold))
        
        paf_1 = QTreeWidgetItem(["📄 MOA & AOA Memorandum (PAF-01)"])
        paf_2 = QTreeWidgetItem(["📄 Statutory Licenses & CIN (PAF-02)"])
        paf_3 = QTreeWidgetItem(["📄 Long-Term Leases & Contracts (PAF-03)"])
        
        paf_root.addChild(paf_1)
        paf_root.addChild(paf_2)
        paf_root.addChild(paf_3)
        self.wp_tree.addTopLevelItem(paf_root)

        # 📁 Current Audit File (CAF)
        caf_root = QTreeWidgetItem(["📁 Current Audit File (CAF)"])
        caf_root.setFont(0, QFont("Inter", 10, QFont.Weight.Bold))

        sec_a = QTreeWidgetItem(["📁 Section A: Planning & Materiality"])
        sec_a.addChild(QTreeWidgetItem(["📄 Engagement Letter & Scope (CAF-A1)"]))
        sec_a.addChild(QTreeWidgetItem(["📄 Materiality Calculation SA 320 (CAF-A2)"]))
        sec_a.addChild(QTreeWidgetItem(["📄 Audit Risk Assessment (CAF-A3)"]))

        sec_b = QTreeWidgetItem(["📁 Section B: Financial Statements"])
        sec_b.addChild(QTreeWidgetItem(["📄 Schedule III Trial Balance Mapping (CAF-B1)"]))
        sec_b.addChild(QTreeWidgetItem(["📄 Bank Reconciliation Summary (CAF-B2)"]))

        sec_c = QTreeWidgetItem(["📁 Section C: Asset & Liability Verification"])
        sec_c.addChild(QTreeWidgetItem(["📄 Fixed Assets & Physical Verification (CAF-C1)"]))
        sec_c.addChild(QTreeWidgetItem(["📄 Trade Debtors Direct Confirmation (CAF-C2)"]))
        sec_c.addChild(QTreeWidgetItem(["📄 Trade Creditors & Liabilities (CAF-C3)"]))

        sec_d = QTreeWidgetItem(["📁 Section D: Statutory Reports"])
        sec_d.addChild(QTreeWidgetItem(["📄 CARO 2020 21 Clauses Checklist (CAF-D1)"]))
        sec_d.addChild(QTreeWidgetItem(["📄 Tax Audit Form 3CD Workings (CAF-D2)"]))

        caf_root.addChild(sec_a)
        caf_root.addChild(sec_b)
        caf_root.addChild(sec_c)
        caf_root.addChild(sec_d)

        self.wp_tree.addTopLevelItem(caf_root)
        self.wp_tree.expandAll()

    def load_audit_projects(self):
        self.project_combo.clear()
        projects = self.session.query(AuditProject).all()
        for proj in projects:
            client = self.session.query(Client).filter_by(id=proj.client_id).first()
            name = client.name if client else "Unknown Client"
            self.project_combo.addItem(f"{name} (FY {proj.financial_year})", proj.id)

    def on_project_changed(self):
        self.load_working_paper()

    def on_tree_item_selected(self, item, col):
        text = item.text(0)
        if "(" in text and ")" in text:
            code = text.split("(")[1].split(")")[0]
            self.index_lbl.setText(f"Index Code: {code} | {text}")
            self.load_working_paper()

    def load_working_paper(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return

        wp = self.session.query(WorkingPaper).filter_by(audit_id=proj_id).first()
        if wp:
            self.active_wp = wp
            self.objective_field.setText(wp.objective or "")
            self.procedure_field.setPlainText(wp.procedure or "")
            self.evidence_field.setText(wp.evidence or "")
            self.observation_field.setPlainText(wp.observation or "")
            self.conclusion_field.setText(wp.conclusion or "")
            
            st = wp.status or "Draft"
            if st == "Reviewed":
                self.lbl_prepared.setText("Prepared & Reviewed [Senior Done]")
                self.lbl_prepared.setStyleSheet("font-size: 12px; font-weight: bold; color: #0284c7; background: #e0f2fe; padding: 4px 8px; border-radius: 4px;")
            elif st == "Approved":
                self.lbl_prepared.setText("Fully Approved & Signed Off [Partner Done]")
                self.lbl_prepared.setStyleSheet("font-size: 12px; font-weight: bold; color: #7c3aed; background: #f5f3ff; padding: 4px 8px; border-radius: 4px;")
            else:
                self.lbl_prepared.setText("Prepared By: Junior Assistant [Done]")
                self.lbl_prepared.setStyleSheet("font-size: 12px; font-weight: bold; color: #047857; background: #ecfdf5; padding: 4px 8px; border-radius: 4px;")

    def save_working_paper(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.EDIT_WORKING_PAPERS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to edit working papers.")
            return

        proj_id = self.project_combo.currentData()
        if proj_id is None: return

        wp = self.session.query(WorkingPaper).filter_by(audit_id=proj_id).first()
        if not wp:
            wp = WorkingPaper(audit_id=proj_id)
            self.session.add(wp)

        wp.objective = self.objective_field.text().strip()
        wp.procedure = self.procedure_field.toPlainText().strip()
        wp.evidence = self.evidence_field.text().strip()
        wp.observation = self.observation_field.toPlainText().strip()
        wp.conclusion = self.conclusion_field.text().strip()
        wp.status = "Prepared"

        self.session.commit()
        QMessageBox.information(self, "Saved", "Working paper saved and indexed successfully under SA 230!")

    def review_working_paper(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        wp = self.session.query(WorkingPaper).filter_by(audit_id=proj_id).first()
        if wp:
            wp.status = "Reviewed"
            self.session.commit()
            self.load_working_paper()
            QMessageBox.information(self, "Review Complete", "Working paper marked as Reviewed by Senior Auditor!")

    def approve_working_paper(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        wp = self.session.query(WorkingPaper).filter_by(audit_id=proj_id).first()
        if wp:
            wp.status = "Approved"
            self.session.commit()
            self.load_working_paper()
            QMessageBox.information(self, "Partner Sign-Off Complete", "Working paper granted final sign-off by Audit Partner!")

    def generate_ai_draft(self):
        obj = self.objective_field.text().strip()
        proc = self.procedure_field.toPlainText().strip()
        if not obj or not proc:
            QMessageBox.warning(self, "Missing Input", "Please enter Audit Objective and Procedure to generate AI findings draft.")
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

    def closeEvent(self, event):
        self.session.close()
        event.accept()
