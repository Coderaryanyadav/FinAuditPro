"""
AI Audit Analysis & RAG Copilot Widget for FinAuditPro.
Provides Document Inspection, Real-Time Token Streaming LLM Chat,
Pre-Packaged ICAI/CARO 2020 Prompt Library, and One-Click Working Paper Finding Ingestion.
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from ai.workers import OllamaWorker
from sqlalchemy.exc import SQLAlchemyError

PROMPT_LIBRARY = [
    ("📋 CARO 2020 Clause (ii) Inventory", "Analyze uploaded inventory sheets and physical verification records under CARO 2020 Clause (ii). Highlight any discrepancies > 10%."),
    ("⚖️ Sec 188 Related Party Transactions", "Check for related party transactions under Section 188 of Companies Act 2013 and verify if arm's length pricing evidence is present."),
    ("💰 Sec 185/186 Loans & Investments", "Review loan agreements, inter-corporate deposits, and guarantees for Section 185/186 statutory ceiling compliance."),
    ("📈 Revenue Recognition SA 240", "Scan sales registers and invoices for SA 240 fraud risk indicators, revenue cut-off anomalies, or round-tripping."),
    ("🔍 Tax Audit Form 3CD Clause 44", "Break down expenditure split between GST registered and non-registered entities under Clause 44 of Form 3CD.")
]

def create_finding_card(title, severity, desc, evidence, border_color, top_border_color, badge_bg, badge_text_color, on_add_wp_cb=None):
    card = QFrame()
    card.setStyleSheet(f"background-color: #ffffff; border: 1px solid {border_color}; border-radius: 8px; margin-bottom: 12px;")
    
    strip = QFrame(card)
    strip.setFixedWidth(4)
    strip.setStyleSheet(f"background-color: {top_border_color}; border-top-left-radius: 8px; border-bottom-left-radius: 8px; border: none;")
    
    clayout = QHBoxLayout(card)
    clayout.setContentsMargins(0, 0, 0, 0)
    clayout.setSpacing(0)
    clayout.addWidget(strip)
    
    content = QFrame()
    content.setStyleSheet("border: none;")
    v = QVBoxLayout(content)
    v.setContentsMargins(14, 14, 14, 14)
    
    h1 = QHBoxLayout()
    t = QLabel(title)
    t.setStyleSheet("font-weight: bold; font-size: 13px; color: #0f172a;")
    b = QLabel(severity)
    b.setStyleSheet(f"background-color: {badge_bg}; color: {badge_text_color}; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;")
    h1.addWidget(t)
    h1.addStretch()
    h1.addWidget(b)
    v.addLayout(h1)
    
    d = QLabel(desc)
    d.setWordWrap(True)
    d.setStyleSheet("color: #475569; font-size: 11px; margin-top: 4px; margin-bottom: 8px;")
    v.addWidget(d)
    
    ev = QFrame()
    ev.setStyleSheet("background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 6px;")
    ev_l = QVBoxLayout(ev)
    ev_l.setContentsMargins(8, 8, 8, 8)
    ev_t = QLabel("EVIDENCE / CITATION SOURCE")
    ev_t.setStyleSheet("color: #64748b; font-size: 9px; font-weight: bold; margin-bottom: 2px;")
    ev_d = QLabel(evidence)
    ev_d.setStyleSheet("color: #0f172a; font-size: 11px; font-family: monospace;")
    ev_l.addWidget(ev_t)
    ev_l.addWidget(ev_d)
    v.addWidget(ev)
    
    h2 = QHBoxLayout()
    h2.addStretch()
    btn_add = QPushButton("➕ Add to SA 230 Working Papers")
    btn_add.setStyleSheet(f"background-color: #0ea5e9; color: white; border: none; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
    if on_add_wp_cb:
        btn_add.clicked.connect(lambda: on_add_wp_cb(title, desc, evidence))
    h2.addWidget(btn_add)
    v.addLayout(h2)
    
    clayout.addWidget(content)
    return card

class AIAuditWidget(QWidget):
    """Interactive RAG AI Copilot & Anomaly Inspector Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("AI Audit Copilot & Anomalies Detector")
        title.setStyleSheet("color: #0f172a; font-size: 15px; font-weight: bold; border: none;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        active_badge = QLabel("🟢 Ollama Local RAG Engine Active")
        active_badge.setStyleSheet("background-color: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(active_badge)
        
        main_layout.addWidget(header)
        
        # 2. 3-Column Split View
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        # COL 1: Source Document
        col1 = QFrame()
        col1.setStyleSheet("background-color: #f1f5f9; border-right: 1px solid #e2e8f0;")
        c1_layout = QVBoxLayout(col1)
        c1_layout.setContentsMargins(0, 0, 0, 0)
        
        c1_header = QFrame()
        c1_header.setFixedHeight(40)
        c1_header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        c1_h_layout = QHBoxLayout(c1_header)
        c1_title = QLabel("RAG SOURCE CONTEXT")
        c1_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #1e293b; border: none;")
        c1_h_layout.addWidget(c1_title)
        c1_layout.addWidget(c1_header)
        
        doc_scroll = QScrollArea()
        doc_scroll.setWidgetResizable(True)
        doc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.doc_content = QLabel()
        self.doc_content.setWordWrap(True)
        self.doc_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.doc_content.setStyleSheet("background-color: #ffffff; margin: 10px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 4px; font-family: monospace; font-size: 11px; color: #334155;")
        self.load_active_document_view()
        doc_scroll.setWidget(self.doc_content)
        c1_layout.addWidget(doc_scroll)
        
        # COL 2: AI Chat & Prompt Library
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(0, 0, 0, 0)
        
        c2_header = QFrame()
        c2_header.setFixedHeight(50)
        c2_header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #f1f5f9;")
        c2_h_layout = QHBoxLayout(c2_header)
        bot_icon = QLabel("🤖")
        bot_icon.setFixedSize(28, 28)
        bot_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_icon.setStyleSheet("background-color: #e0f2fe; border-radius: 14px; font-size: 14px; border: none;")
        bot_text = QLabel("<b>FinAudit Copilot</b> <span style='color:#64748b; font-size:11px;'>(Local AI Model)</span>")
        bot_text.setStyleSheet("border: none; font-size: 13px; color: #0f172a;")
        c2_h_layout.addWidget(bot_icon)
        c2_h_layout.addWidget(bot_text)
        c2_h_layout.addStretch()
        c2_layout.addWidget(c2_header)
        
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_area.setStyleSheet("background-color: #f8fafc;")
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_area.setWidget(self.chat_widget)
        c2_layout.addWidget(self.chat_area)
        
        # Prompt Chips Layout
        prompt_frame = QFrame()
        prompt_frame.setStyleSheet("background-color: #ffffff; border-top: 1px solid #e2e8f0; padding: 6px;")
        p_layout = QVBoxLayout(prompt_frame)
        p_layout.setContentsMargins(10, 8, 10, 8)
        
        chips_lbl = QLabel("ICAI AUDIT PROMPT LIBRARY:")
        chips_lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b; border: none;")
        p_layout.addWidget(chips_lbl)

        chips_scroll = QScrollArea()
        chips_scroll.setFixedHeight(40)
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chips_w = QWidget()
        chips_l = QHBoxLayout(chips_w)
        chips_l.setContentsMargins(0, 0, 0, 0)
        chips_l.setSpacing(6)

        for chip_title, chip_prompt in PROMPT_LIBRARY:
            btn = QPushButton(chip_title)
            btn.setStyleSheet("background-color: #f1f5f9; color: #0ea5e9; font-weight: bold; border: 1px solid #bae6fd; border-radius: 4px; padding: 4px 8px; font-size: 10px;")
            btn.clicked.connect(lambda _, p=chip_prompt: self.execute_prompt(p))
            chips_l.addWidget(btn)

        chips_scroll.setWidget(chips_w)
        p_layout.addWidget(chips_scroll)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI Copilot about revenue, inventory, tax, or legal compliance...")
        self.chat_input.setFixedHeight(36)
        self.chat_input.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 0 12px; color: #0f172a; font-size: 12px;")
        self.chat_input.returnPressed.connect(self.handle_input)
        p_layout.addWidget(self.chat_input)

        c2_layout.addWidget(prompt_frame)
        
        # COL 3: AI Findings List
        col3 = QFrame()
        col3.setStyleSheet("background-color: #f8fafc;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(0, 0, 0, 0)
        
        c3_header = QFrame()
        c3_header.setFixedHeight(50)
        c3_header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        c3_h_layout = QHBoxLayout(c3_header)
        f_title = QLabel("<b>AI FINDINGS & ANOMALIES</b>")
        f_title.setStyleSheet("border: none; font-size: 12px; color: #0f172a;")
        c3_h_layout.addWidget(f_title)
        c3_h_layout.addStretch()
        c3_layout.addWidget(c3_header)
        
        findings_scroll = QScrollArea()
        findings_scroll.setWidgetResizable(True)
        findings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        findings_widget = QWidget()
        self.f_layout = QVBoxLayout(findings_widget)
        self.f_layout.setContentsMargins(16, 16, 16, 16)
        self.f_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.load_database_findings()
        
        findings_scroll.setWidget(findings_widget)
        c3_layout.addWidget(findings_scroll)
        
        body_layout.addWidget(col1, 3)
        body_layout.addWidget(col2, 4)
        body_layout.addWidget(col3, 3)
        
        main_layout.addWidget(body)
        
        self.add_message("FinAudit Copilot", "Welcome to AI Audit Analysis. Select a prompt from the ICAI Library or ask any question about the client's financial documents.", False)
        self.current_ai_bubble = None
        self.worker = None

    def execute_prompt(self, prompt_text: str):
        self.chat_input.setText(prompt_text)
        self.handle_input()

    def handle_input(self):
        text = self.chat_input.text().strip()
        if not text: return
        self.chat_input.clear()
        
        self.add_message("You", text, True)
        self.current_ai_bubble = self.add_message("FinAudit Copilot", "", False)
        
        doc_context = self.doc_content.text()
        system_prompt = f"You are FinAudit Copilot, an expert AI Chartered Accountant assistant adhering strictly to ICAI Standards on Auditing (SA 200-790) and Companies Act 2013.\n\nFinancial Document Context:\n{doc_context[:2000]}"

        self.worker = OllamaWorker(raw_query=text, system_prompt=system_prompt)
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_chunk(self, text):
        if self.current_ai_bubble:
            lbl = self.current_ai_bubble.findChild(QLabel)
            if lbl:
                lbl.setText(lbl.text() + text)

    def on_ai_finished(self):
        self.current_ai_bubble = None

    def add_message(self, sender, message, is_user=False):
        bubble_frame = QFrame()
        if is_user:
            bubble_frame.setStyleSheet("background-color: #0ea5e9; color: white; border-radius: 8px; margin-left: 30px;")
        else:
            bubble_frame.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 8px; margin-right: 30px;")
            
        b_layout = QVBoxLayout(bubble_frame)
        b_layout.setContentsMargins(10, 8, 10, 8)
        
        lbl_sender = QLabel(sender)
        lbl_sender.setStyleSheet("font-size: 10px; font-weight: bold; border: none;" + ("color: #e0f2fe;" if is_user else "color: #64748b;"))
        
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 12px; border: none;" + ("color: white;" if is_user else "color: #0f172a;"))
        
        b_layout.addWidget(lbl_sender)
        b_layout.addWidget(lbl_msg)
        
        self.chat_layout.addWidget(bubble_frame)
        return bubble_frame

    def load_active_document_view(self):
        try:
            from database.database import SessionLocal
            from database.models import Document
            session = SessionLocal()
            doc = session.query(Document).order_by(Document.id.desc()).first()
            if doc and os.path.exists(doc.file_path):
                with open(doc.file_path, "r", errors="ignore") as f:
                    content = f.read(1500)
                self.doc_content.setText(f"<b>ACTIVE DOCUMENT: {doc.file_name}</b><br/><br/>" + content.replace("\n", "<br/>"))
            else:
                self.doc_content.setText("<b>NO DOCUMENT INDEXED</b><br/><br/>Upload client Trial Balance or Financial Statements to view RAG context.")
            session.close()
        except Exception as e:
            self.doc_content.setText(f"Document load status: {e}")

    def load_database_findings(self):
        try:
            from database.database import SessionLocal
            from database.models import Finding
            session = SessionLocal()
            active_id = getattr(self, 'active_engagement_id', None)
            findings = session.query(Finding).filter_by(audit_id=active_id).all() if active_id else session.query(Finding).all()
            session.close()

            if not findings:
                empty_card = QFrame()
                empty_card.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px;")
                e_layout = QVBoxLayout(empty_card)
                e_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl2 = QLabel("<b>No Anomalies Flagged</b><br/><span style='color: #64748b; font-size: 11px;'>Ingest documents or execute prompts to trigger AI analysis.</span>")
                lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl2.setStyleSheet("color: #0f172a; font-size: 12px; border: none;")
                e_layout.addWidget(lbl2)
                self.f_layout.addWidget(empty_card)
                return

            for f in findings:
                sev = getattr(f, 'severity', 'LOW') or getattr(f, 'risk_level', 'LOW')
                card = create_finding_card(
                    "AI Audit Flag", sev.upper(),
                    f.description,
                    f"Impact: ₹ {getattr(f, 'financial_impact', 0) or 0:,.2f}",
                    "#fecaca" if sev.upper() in ["HIGH", "CRITICAL"] else "#fde68a",
                    "#ef4444" if sev.upper() in ["HIGH", "CRITICAL"] else "#f59e0b",
                    "#fef2f2" if sev.upper() in ["HIGH", "CRITICAL"] else "#fffbeb",
                    "#b91c1c" if sev.upper() in ["HIGH", "CRITICAL"] else "#b45309",
                    on_add_wp_cb=self.add_finding_to_working_paper
                )
                self.f_layout.addWidget(card)
        except Exception as e:
            lbl = QLabel(f"Findings load status: {e}")
            lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            self.f_layout.addWidget(lbl)

    def add_finding_to_working_paper(self, title, desc, evidence):
        try:
            from database.database import SessionLocal
            from database.models import WorkingPaper, AuditProject
            session = SessionLocal()
            active_id = getattr(self, 'active_engagement_id', None)
            if not active_id:
                proj = session.query(AuditProject).order_by(AuditProject.id.desc()).first()
                if proj: active_id = proj.id

            if active_id:
                wp = session.query(WorkingPaper).filter_by(audit_id=active_id).first()
                if not wp:
                    from database.models import WorkingPaperIndex
                    wp_idx = session.query(WorkingPaperIndex).filter_by(engagement_id=active_id).first()
                    if not wp_idx:
                        wp_idx = WorkingPaperIndex(engagement_id=active_id, ref_code="A-100", title="Audit Planning & General Index")
                        session.add(wp_idx)
                        session.flush()
                    wp = WorkingPaper(audit_id=active_id, index_id=wp_idx.id)
                    session.add(wp)
                wp.observation = f"{wp.observation or ''}\n• [AI Finding] {title}: {desc}".strip()
                wp.evidence = f"{wp.evidence or ''}\n• {evidence}".strip()
                session.commit()
                QMessageBox.information(self, "Added to Working Papers", f"Successfully ingested finding '{title}' into SA 230 Working Papers!")
            else:
                QMessageBox.warning(self, "No Engagement", "Please select or create an audit project first.")
            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Ingestion Error", f"Failed to ingest finding: {e}")

    def closeEvent(self, event):
        self.session.close()
        event.accept()
