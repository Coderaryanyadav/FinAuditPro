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
from ai.ollama_client import OllamaClient
from sqlalchemy.exc import SQLAlchemyError
from database.database import get_session
from database.models import AuditProject, Document
from database.repositories.document_repo import DocumentRepository
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.document_service import DocumentService
from services.finding_service import FindingService
from services.working_paper_service import WorkingPaperService
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget

PROMPT_LIBRARY = [
    (" CARO 2020 Clause (ii) Inventory", "Analyze uploaded inventory sheets and physical verification records under CARO 2020 Clause (ii). Highlight any discrepancies > 10%."),
    (" Sec 188 Related Party Transactions", "Check for related party transactions under Section 188 of Companies Act 2013 and verify if arm's length pricing evidence is present."),
    (" Sec 185/186 Loans & Investments", "Review loan agreements, inter-corporate deposits, and guarantees for Section 185/186 statutory ceiling compliance."),
    (" Revenue Recognition SA 240", "Scan sales registers and invoices for SA 240 fraud risk indicators, revenue cut-off anomalies, or round-tripping."),
    (" Tax Audit Form 3CD Clause 44", "Break down expenditure split between GST registered and non-registered entities under Clause 44 of Form 3CD.")
]

def create_finding_card(title, severity, desc, evidence, border_color, top_border_color, badge_bg, badge_text_color, on_add_wp_cb=None):
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 12px;
            margin-bottom: 12px;
        }
    """)
    
    clayout = QVBoxLayout(card)
    clayout.setContentsMargins(14, 14, 14, 14)
    clayout.setSpacing(8)
    
    h1 = QHBoxLayout()
    t = QLabel(title)
    t.setStyleSheet("font-weight: 600; font-size: 13px; color: #1d1d1f; border: none;")
    b = QLabel(severity)
    b.setStyleSheet(f"background-color: {badge_bg}; color: {badge_text_color}; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 5px; border: none;")
    h1.addWidget(t)
    h1.addStretch()
    h1.addWidget(b)
    clayout.addLayout(h1)
    
    d = QLabel(desc)
    d.setWordWrap(True)
    d.setStyleSheet("color: #6e6e73; font-size: 12px; border: none;")
    clayout.addWidget(d)
    
    ev = QFrame()
    ev.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e5e5ea; border-radius: 8px;")
    ev_l = QVBoxLayout(ev)
    ev_l.setContentsMargins(10, 8, 10, 8)
    ev_l.setSpacing(2)
    ev_t = QLabel("EVIDENCE / CITATION SOURCE")
    ev_t.setStyleSheet("color: #86868b; font-size: 9px; font-weight: 600; letter-spacing: 0.5px; border: none;")
    ev_d = QLabel(evidence)
    ev_d.setStyleSheet("color: #1d1d1f; font-size: 11px; font-family: monospace; border: none;")
    ev_l.addWidget(ev_t)
    ev_l.addWidget(ev_d)
    clayout.addWidget(ev)
    
    h2 = QHBoxLayout()
    h2.addStretch()
    btn_add = QPushButton("Add to SA 230 Working Papers")
    btn_add.setStyleSheet("""
        QPushButton {
            background-color: #007aff;
            color: #ffffff;
            border: none;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QPushButton:hover { background-color: #0062cc; }
    """)
    if on_add_wp_cb:
        btn_add.clicked.connect(lambda: on_add_wp_cb(title, desc, evidence))
    h2.addWidget(btn_add)
    clayout.addLayout(h2)
    
    apply_shadow(card, blur=12, dx=0, dy=2, alpha=6)
    return card

class AIAuditWidget(QWidget):
    """Interactive RAG AI Copilot & Anomaly Inspector Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5f5f7;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Bar — Apple Header
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("headerBar")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e5e5ea;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("AI Audit Copilot & Anomalies Detector")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.4px; border: none;")
        subtitle = QLabel("SA 200-790 ICAI Standards, CARO 2020 & Companies Act Compliance")
        subtitle.setStyleSheet("font-size: 12px; color: #6e6e73; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        header_layout.addLayout(title_v)
        header_layout.addStretch()
        
        # --- Ollama Status Badge (dynamic) ---
        self._ollama_online = OllamaClient.is_available()
        if self._ollama_online:
            self._status_badge = QLabel("Ollama Local RAG Engine Active")
            self._status_badge.setStyleSheet(
                "background-color: #e8f2ff; color: #007aff; border: 1px solid #cce4ff; "
                "border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: 600;"
            )
        else:
            self._status_badge = QLabel("Ollama Offline — Rule Engine Fallback Active")
            self._status_badge.setStyleSheet(
                "background-color: #fff8e6; color: #b36b00; border: 1px solid #ffe0b2; "
                "border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: 600;"
            )
        header_layout.addWidget(self._status_badge)
        
        main_layout.addWidget(header)
        
        # 2. 3-Column Split View
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        # COL 1: Source Document
        col1 = QFrame()
        col1.setStyleSheet("background-color: #f5f5f7; border-right: 1px solid #e5e5ea;")
        c1_layout = QVBoxLayout(col1)
        c1_layout.setContentsMargins(0, 0, 0, 0)
        
        c1_header = QFrame()
        c1_header.setFixedHeight(42)
        c1_header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e5ea;")
        c1_h_layout = QHBoxLayout(c1_header)
        c1_title = QLabel("RAG SOURCE CONTEXT")
        c1_title.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b; letter-spacing: 0.8px; border: none;")
        c1_h_layout.addWidget(c1_title)
        c1_layout.addWidget(c1_header)
        
        doc_scroll = QScrollArea()
        doc_scroll.setWidgetResizable(True)
        doc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.doc_content = QLabel()
        self.doc_content.setWordWrap(True)
        self.doc_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.doc_content.setStyleSheet("background-color: #ffffff; margin: 10px; padding: 16px; border: 1px solid #e5e5ea; border-radius: 10px; font-family: monospace; font-size: 11px; color: #1d1d1f;")
        self.load_active_document_view()
        doc_scroll.setWidget(self.doc_content)
        c1_layout.addWidget(doc_scroll)
        
        # COL 2: AI Chat & Prompt Library
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e5e5ea;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(0, 0, 0, 0)
        
        c2_header = QFrame()
        c2_header.setFixedHeight(42)
        c2_header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e5ea;")
        c2_h_layout = QHBoxLayout(c2_header)
        bot_text = QLabel("FinAudit Copilot (Local RAG)")
        bot_text.setStyleSheet("border: none; font-size: 11px; font-weight: 600; color: #86868b; letter-spacing: 0.8px;")
        c2_h_layout.addWidget(bot_text)
        c2_h_layout.addStretch()
        c2_layout.addWidget(c2_header)
        
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_area.setStyleSheet("background-color: #f5f5f7;")
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_area.setWidget(self.chat_widget)
        c2_layout.addWidget(self.chat_area)
        
        # Prompt Chips Layout
        prompt_frame = QFrame()
        prompt_frame.setStyleSheet("background-color: #ffffff; border-top: 1px solid #e5e5ea; padding: 6px;")
        p_layout = QVBoxLayout(prompt_frame)
        p_layout.setContentsMargins(10, 8, 10, 8)
        
        chips_lbl = QLabel("ICAI AUDIT PROMPT LIBRARY:")
        chips_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #86868b; letter-spacing: 0.5px; border: none;")
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
            btn.setToolTip(f"Execute AI audit prompt: {chip_title}")
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f2f7ff;
                    color: #007aff;
                    font-weight: 600;
                    border: 1px solid #cce4ff;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #e8f2ff; }
            """)
            btn.clicked.connect(lambda _, p=chip_prompt: self.execute_prompt(p))
            chips_l.addWidget(btn)

        chips_scroll.setWidget(chips_w)
        p_layout.addWidget(chips_scroll)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI Copilot about revenue, inventory, tax, or legal compliance...")
        self.chat_input.setToolTip("Type audit prompt or question for local RAG AI Copilot")
        self.chat_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.chat_input.setFixedHeight(38)
        self.chat_input.setStyleSheet("background-color: #f2f2f7; border: 1px solid #e5e5ea; border-radius: 8px; padding: 0 12px; color: #1d1d1f; font-size: 12px;")
        self.chat_input.returnPressed.connect(self.handle_input)
        p_layout.addWidget(self.chat_input)

        c2_layout.addWidget(prompt_frame)
        
        # COL 3: AI Findings List
        col3 = QFrame()
        col3.setStyleSheet("background-color: #f5f5f7;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(0, 0, 0, 0)
        
        c3_header = QFrame()
        c3_header.setFixedHeight(42)
        c3_header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e5ea;")
        c3_h_layout = QHBoxLayout(c3_header)
        f_title = QLabel("AI FINDINGS & ANOMALIES")
        f_title.setStyleSheet("border: none; font-size: 10px; font-weight: 600; color: #86868b; letter-spacing: 0.8px;")
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
        
        doc_context = getattr(self, 'raw_doc_text', '')
        system_prompt = f"You are FinAudit Copilot, an expert AI Chartered Accountant assistant adhering strictly to ICAI Standards on Auditing (SA 200-790) and Companies Act 2013.\n\nFinancial Document Context:\n{doc_context[:2000]}"

        self.worker = OllamaWorker(raw_query=text, system_prompt=system_prompt)
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.ollama_offline.connect(self.run_rule_engine_fallback)
        self.worker.start()

    def on_ai_chunk(self, text):
        if self.current_ai_bubble:
            lbl = self.current_ai_bubble.findChild(QLabel, "chatMessageLabel")
            if lbl:
                lbl.setText(lbl.text() + text)
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def on_ai_finished(self):
        self.current_ai_bubble = None

    def run_rule_engine_fallback(self, original_query: str):
        """Auto-fallback: run all active audit rules against current document context."""
        self._status_badge.setText("Ollama Offline — Rule Engine Fallback Active")
        self._status_badge.setStyleSheet(
            "background-color: #fff8e6; color: #b36b00; border: 1px solid #ffe0b2; "
            "border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: 600;"
        )
        try:
            from rule_engine.rule_registry import RuleRegistry
            registry = RuleRegistry()
            active_rules = registry.get_active_rules()

            # Build a minimal data dict from raw document context available in the widget
            doc_text = getattr(self, 'raw_doc_text', '')
            data = {"cleaned_text": doc_text, "total_amount": 0.0, "tax_amount": 0.0}

            results = []
            for rule in active_rules:
                try:
                    result = rule.evaluate(data)
                    if not result.passed:
                        results.append(result)
                except Exception:
                    continue

            if results:
                summary_lines = [f"**Rule Engine Fallback Analysis** — {len(results)} issue(s) detected:\n"]
                for r in results[:10]:  # Cap display at 10 findings
                    summary_lines.append(
                        f"• [{r.severity.value if hasattr(r.severity, 'value') else r.severity}] "
                        f"{r.rule_name}: {r.description}"
                    )
                if len(results) > 10:
                    summary_lines.append(f"... and {len(results) - 10} more rules flagged issues.")
                fallback_msg = "\n".join(summary_lines)
            else:
                fallback_msg = (
                    "**Rule Engine Fallback Analysis** — No statutory violations detected in current document context. "
                    "Upload client financial statements for deeper rule-based analysis."
                )

            if self.current_ai_bubble:
                lbl = self.current_ai_bubble.findChild(QLabel, "chatMessageLabel")
                if lbl:
                    lbl.setText(fallback_msg)
            else:
                self.add_message("Rule Engine (Fallback)", fallback_msg, False)
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        except Exception as e:
            self.add_message("Rule Engine (Fallback)", f"Rule engine analysis error: {e}", False)

    def add_message(self, sender, message, is_user=False):
        bubble_frame = QFrame()
        if is_user:
            bubble_frame.setStyleSheet("background-color: #007aff; color: #ffffff; border-radius: 12px; margin-left: 30px;")
        else:
            bubble_frame.setStyleSheet("background-color: #ffffff; color: #1d1d1f; border: 1px solid #e5e5ea; border-radius: 12px; margin-right: 30px;")
            
        b_layout = QVBoxLayout(bubble_frame)
        b_layout.setContentsMargins(12, 10, 12, 10)
        b_layout.setSpacing(4)
        
        lbl_sender = QLabel(sender)
        lbl_sender.setObjectName("chatSenderLabel")
        lbl_sender.setStyleSheet("font-size: 10px; font-weight: 600; border: none;" + ("color: rgba(255, 255, 255, 0.85);" if is_user else "color: #86868b;"))
        
        lbl_msg = QLabel(message)
        lbl_msg.setObjectName("chatMessageLabel")
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 12px; border: none;" + ("color: #ffffff;" if is_user else "color: #1d1d1f;"))
        
        b_layout.addWidget(lbl_sender)
        b_layout.addWidget(lbl_msg)
        
        apply_shadow(bubble_frame, blur=10, dx=0, dy=2, alpha=6)
        self.chat_layout.addWidget(bubble_frame)
        return bubble_frame

    def load_active_document_view(self):
        try:
            with get_session() as session:
                doc = session.query(Document).order_by(Document.id.desc()).first()
                if doc and os.path.exists(doc.file_path):
                    with open(doc.file_path, "r", errors="ignore") as f:
                        content = f.read(1500)
                    self.raw_doc_text = content
                    self.doc_content.setText(f"<b>ACTIVE DOCUMENT: {doc.file_name}</b><br/><br/>" + content.replace("\n", "<br/>"))
                else:
                    self.raw_doc_text = ""
                    self.doc_content.setText("<b>NO DOCUMENT INDEXED</b><br/><br/>Upload client Trial Balance or Financial Statements in 'Upload Documents' tab to view RAG context.")
        except Exception as e:
            self.raw_doc_text = ""
            self.doc_content.setText(f"Document load status: {e}")

    def load_database_findings(self):
        try:
            # Clear old widgets from layout first to prevent layout corruption / duplicates
            while self.f_layout.count():
                child = self.f_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            active_id = getattr(self, 'active_engagement_id', None)
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                finding_service = FindingService(wp_repo)
                findings = finding_service.get_findings_by_audit_id(active_id) if active_id else finding_service.get_all_findings()

            if not findings:
                empty_widget = EmptyStateWidget("No Anomalies Flagged", "Ingest documents or execute prompts to trigger AI analysis.")
                self.f_layout.addWidget(empty_widget)
                return

            for f in findings:
                sev = getattr(f, 'severity', 'LOW') or getattr(f, 'risk_level', 'LOW')
                card = create_finding_card(
                    "AI Audit Flag", str(sev).upper(),
                    f.description,
                    f"Impact: ₹ {getattr(f, 'financial_impact', 0) or 0:,.2f}",
                    "#ffebeb" if str(sev).upper() in ["HIGH", "CRITICAL"] else "#fff8e6",
                    "#ff3b30" if str(sev).upper() in ["HIGH", "CRITICAL"] else "#ff9500",
                    "#ffebeb" if str(sev).upper() in ["HIGH", "CRITICAL"] else "#fff8e6",
                    "#ff3b30" if str(sev).upper() in ["HIGH", "CRITICAL"] else "#b36b00",
                    on_add_wp_cb=self.add_finding_to_working_paper
                )
                self.f_layout.addWidget(card)
        except Exception as e:
            error_widget = ErrorStateWidget("Findings Load Failed", str(e))
            self.f_layout.addWidget(error_widget)

    def add_finding_to_working_paper(self, title, desc, evidence):
        try:
            active_id = getattr(self, 'active_engagement_id', None)
            with get_session() as session:
                if not active_id:
                    proj = session.query(AuditProject).order_by(AuditProject.id.desc()).first()
                    if proj: active_id = proj.id

                if active_id:
                    wp_repo = WorkingPaperRepository(session)
                    wp_service = WorkingPaperService(wp_repo)
                    wp_service.add_observation(
                        audit_id=active_id,
                        observation=f"[AI Finding] {title}: {desc}",
                        evidence=evidence
                    )
                    QMessageBox.information(self, "Added to Working Papers", f"Successfully ingested finding '{title}' into SA 230 Working Papers!")
                else:
                    QMessageBox.warning(self, "No Engagement", "Please select or create an audit project first.")
        except Exception as e:
            QMessageBox.critical(self, "Ingestion Error", f"Failed to ingest finding: {e}")

    def closeEvent(self, event):
        event.accept()
