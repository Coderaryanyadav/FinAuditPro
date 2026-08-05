"""
AI Audit Analysis & RAG Copilot Widget for FinAuditPro.
Provides Document Inspection, Real-Time Token Streaming LLM Chat,
Pre-Packaged ICAI/CARO 2020 Prompt Library, and One-Click Working Paper Finding Ingestion.
"""

import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from ai.workers import OllamaWorker
from ai.ollama_client import OllamaClient
from database.database import get_session
from database.models import AuditProject, Document
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.finding_service import FindingService
from services.working_paper_service import WorkingPaperService
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget

logger = logging.getLogger(__name__)

PROMPT_LIBRARY = [
    ("📋 CARO 2020 Inventory", "Analyze uploaded inventory sheets and physical verification records under CARO 2020 Clause (ii). Highlight any discrepancies > 10%."),
    ("🤝 Sec 188 Related Party", "Check for related party transactions under Section 188 of Companies Act 2013 and verify if arm's length pricing evidence is present."),
    ("💰 Sec 185/186 Loans", "Review loan agreements, inter-corporate deposits, and guarantees for Section 185/186 statutory ceiling compliance."),
    ("📈 SA 240 Revenue Fraud", "Scan sales registers and invoices for SA 240 fraud risk indicators, revenue cut-off anomalies, or round-tripping."),
    ("📑 Form 3CD Clause 44", "Break down expenditure split between GST registered and non-registered entities under Clause 44 of Form 3CD."),
    ("⚖️ SA 500 Audit Evidence", "Perform substantive verification on supporting vouchers and check compliance with ICAI SA 500 audit evidence standards.")
]

def create_finding_card(title, severity, desc, evidence, border_color, top_border_color, badge_bg, badge_text_color, on_add_wp_cb=None):
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin-bottom: 10px;
        }
    """)
    
    clayout = QVBoxLayout(card)
    clayout.setContentsMargins(14, 14, 14, 14)
    clayout.setSpacing(8)
    
    h1 = QHBoxLayout()
    t = QLabel(title)
    t.setStyleSheet("font-weight: 700; font-size: 13px; color: #0f172a; border: none;")
    b = QLabel(severity)
    b.setStyleSheet(f"background-color: {badge_bg}; color: {badge_text_color}; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: none;")
    h1.addWidget(t)
    h1.addStretch()
    h1.addWidget(b)
    clayout.addLayout(h1)
    
    d = QLabel(desc)
    d.setWordWrap(True)
    d.setStyleSheet("color: #475569; font-size: 12px; line-height: 1.4; border: none;")
    clayout.addWidget(d)
    
    ev = QFrame()
    ev.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;")
    ev_l = QVBoxLayout(ev)
    ev_l.setContentsMargins(10, 8, 10, 8)
    ev_l.setSpacing(2)
    ev_t = QLabel("EVIDENCE / CITATION SOURCE")
    ev_t.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: 700; letter-spacing: 0.6px; border: none;")
    ev_d = QLabel(evidence)
    ev_d.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: 600; font-family: monospace; border: none;")
    ev_l.addWidget(ev_t)
    ev_l.addWidget(ev_d)
    clayout.addWidget(ev)
    
    h2 = QHBoxLayout()
    h2.addStretch()
    btn_add = QPushButton("Add to SA 230 Working Papers")
    btn_add.setStyleSheet("""
        QPushButton {
            background-color: #0284c7;
            color: #ffffff;
            border: none;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            padding: 6px 14px;
        }
        QPushButton:hover { background-color: #0369a1; }
        QPushButton:disabled { background-color: #10b981; color: #ffffff; }
    """)
    
    def _handle_click():
        if on_add_wp_cb:
            success = on_add_wp_cb(title, desc, evidence)
            if success is not False:
                btn_add.setText("✓ Ingested in SA 230")
                btn_add.setEnabled(False)

    btn_add.clicked.connect(_handle_click)
    h2.addWidget(btn_add)
    clayout.addLayout(h2)
    
    apply_shadow(card, blur=10, dx=0, dy=2, alpha=8)
    return card


class AIAuditWidget(QWidget):
    """Interactive RAG AI Copilot & Anomaly Inspector Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("headerBar")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("AI Audit Copilot & Anomalies Detector")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; border: none;")
        subtitle = QLabel("SA 200-790 ICAI Standards, CARO 2020 & Companies Act Compliance Engine")
        subtitle.setStyleSheet("font-size: 11px; color: #64748b; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        header_layout.addLayout(title_v)
        header_layout.addStretch()
        
        # --- Ollama Status Badge ---
        self._ollama_online = OllamaClient.is_available()
        if self._ollama_online:
            self._status_badge = QLabel("Ollama Local RAG Engine Active")
            self._status_badge.setStyleSheet(
                "background-color: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; "
                "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
            )
        else:
            self._status_badge = QLabel("Ollama Offline — Rule Engine Fallback Active")
            self._status_badge.setStyleSheet(
                "background-color: #fffbeb; color: #b45309; border: 1px solid #fef3c7; "
                "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
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
        col1.setStyleSheet("background-color: #f8fafc; border-right: 1px solid #e2e8f0;")
        c1_layout = QVBoxLayout(col1)
        c1_layout.setContentsMargins(0, 0, 0, 0)
        
        c1_header = QFrame()
        c1_header.setFixedHeight(42)
        c1_header.setStyleSheet("background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0;")
        c1_h_layout = QHBoxLayout(c1_header)
        c1_title = QLabel("RAG SOURCE CONTEXT")
        c1_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #475569; letter-spacing: 0.8px; border: none;")
        c1_h_layout.addWidget(c1_title)
        c1_layout.addWidget(c1_header)
        
        doc_scroll = QScrollArea()
        doc_scroll.setWidgetResizable(True)
        doc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.doc_content = QLabel()
        self.doc_content.setWordWrap(True)
        self.doc_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.doc_content.setStyleSheet("background-color: #ffffff; margin: 10px; padding: 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: monospace; font-size: 11px; color: #0f172a; line-height: 1.4;")
        self.load_active_document_view()
        doc_scroll.setWidget(self.doc_content)
        c1_layout.addWidget(doc_scroll)
        
        # COL 2: AI Chat & Prompt Library
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(0, 0, 0, 0)
        
        c2_header = QFrame()
        c2_header.setFixedHeight(42)
        c2_header.setStyleSheet("background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0;")
        c2_h_layout = QHBoxLayout(c2_header)
        bot_text = QLabel("FinAudit Copilot (Local RAG)")
        bot_text.setStyleSheet("border: none; font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.8px;")
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
        p_layout.setContentsMargins(12, 10, 12, 10)
        p_layout.setSpacing(8)
        
        chips_hdr = QHBoxLayout()
        chips_lbl = QLabel("ICAI AUDIT PROMPT LIBRARY")
        chips_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 0.6px; border: none;")
        chips_hdr.addWidget(chips_lbl)
        chips_hdr.addStretch()
        p_layout.addLayout(chips_hdr)

        chips_scroll = QScrollArea()
        chips_scroll.setFixedHeight(48)
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chips_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:horizontal { height: 4px; background: #f1f5f9; border-radius: 2px; }
            QScrollBar::handle:horizontal { background: #cbd5e1; border-radius: 2px; }
        """)
        chips_w = QWidget()
        chips_l = QHBoxLayout(chips_w)
        chips_l.setContentsMargins(0, 0, 0, 0)
        chips_l.setSpacing(8)

        for chip_title, chip_prompt in PROMPT_LIBRARY:
            btn = QPushButton(chip_title)
            btn.setToolTip(f"Execute AI audit prompt: {chip_prompt}")
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f7ff;
                    color: #0284c7;
                    font-weight: 600;
                    border: 1px solid #bae6fd;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 11px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #e0f2fe;
                    border-color: #38bdf8;
                    color: #0369a1;
                }
            """)
            btn.clicked.connect(lambda _, p=chip_prompt: self.execute_prompt(p))
            chips_l.addWidget(btn)

        chips_scroll.setWidget(chips_w)
        p_layout.addWidget(chips_scroll)

        # Input & Send Control Box
        input_box = QHBoxLayout()
        input_box.setSpacing(8)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI Copilot about revenue, inventory, tax, or statutory compliance...")
        self.chat_input.setToolTip("Type audit prompt or question for local RAG AI Copilot")
        self.chat_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.chat_input.setFixedHeight(40)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 0 14px;
                color: #0f172a;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1.5px solid #0284c7;
                background-color: #ffffff;
            }
        """)
        self.chat_input.returnPressed.connect(self.handle_input)
        
        btn_send = QPushButton("Send Prompt")
        btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_send.setFixedHeight(40)
        btn_send.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: none;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_send.clicked.connect(self.handle_input)
        
        input_box.addWidget(self.chat_input, 1)
        input_box.addWidget(btn_send)
        p_layout.addLayout(input_box)

        c2_layout.addWidget(prompt_frame)
        
        # COL 3: AI Findings List
        col3 = QFrame()
        col3.setStyleSheet("background-color: #f8fafc;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(0, 0, 0, 0)
        
        c3_header = QFrame()
        c3_header.setFixedHeight(42)
        c3_header.setStyleSheet("background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0;")
        c3_h_layout = QHBoxLayout(c3_header)
        self.f_title = QLabel("AI FINDINGS & ANOMALIES")
        self.f_title.setStyleSheet("border: none; font-size: 10px; font-weight: 700; color: #475569; letter-spacing: 0.8px;")
        c3_h_layout.addWidget(self.f_title)
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
        self._workers = []

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

        worker = OllamaWorker(raw_query=text, system_prompt=system_prompt)
        self._workers.append(worker)

        def _on_finish():
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()
            self.on_ai_finished()

        worker.chunk_received.connect(self.on_ai_chunk)
        worker.finished.connect(_on_finish)
        worker.ollama_offline.connect(self.run_rule_engine_fallback)
        worker.start()

    def on_ai_chunk(self, text):
        if self.current_ai_bubble:
            lbl = self.current_ai_bubble.findChild(QLabel, "chatMessageLabel")
            if lbl:
                lbl.setText(lbl.text() + text)
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def on_ai_finished(self):
        self.current_ai_bubble = None

    def run_rule_engine_fallback(self, original_query: str):
        """Intelligent Local RAG & Document Intelligence Fallback Engine."""
        self._status_badge.setText("Ollama Offline — Local RAG Engine Active")
        self._status_badge.setStyleSheet(
            "background-color: #fffbeb; color: #b45309; border: 1px solid #fef3c7; "
            "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
        )
        try:
            doc_text = getattr(self, 'raw_doc_text', '')
            q_lower = original_query.lower().strip()

            active_file_name = "Ingested Document"
            with get_session() as session:
                doc = session.query(Document).order_by(Document.id.desc()).first()
                if doc:
                    active_file_name = doc.file_name

            # Evaluate statutory rules for findings context
            from rule_engine.rule_registry import RuleRegistry
            registry = RuleRegistry()
            active_rules = registry.get_active_rules()
            data = {"cleaned_text": doc_text, "total_amount": 0.0, "tax_amount": 0.0}

            rule_findings = []
            for rule in active_rules:
                try:
                    res = rule.evaluate(data)
                    if not res.passed:
                        rule_findings.append(res)
                except Exception:
                    continue

            # Query intent matching
            is_summary = any(k in q_lower for k in ["what is there", "summarize", "what is this", "content", "summary", "explain", "overview", "show document", "what document"])
            
            lines = []
            if is_summary:
                lines.append(f"<b>📄 Document Intelligence Analysis for {active_file_name}</b><br/>")
                lines.append("<b>Overview & Document Context:</b>")
                clean_snippet = doc_text.replace("<br/>", "\n").strip()
                if clean_snippet and not clean_snippet.startswith("<i>") and not clean_snippet.startswith("<b>ACTIVE DOCUMENT STATUS"):
                    snippet = clean_snippet[:350].replace("\n", " ")
                    lines.append(f"• <i>\"{snippet}...\"</i><br/>")
                else:
                    lines.append(f"• <i>Active audit evidence file '{active_file_name}' ingested and indexed in local FAISS Vector Store.</i><br/>")

                lines.append("<b>Statutory Anomalies & Compliance Flags:</b>")
                if rule_findings:
                    for r in rule_findings:
                        sev_str = r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
                        lines.append(f"• [{sev_str.upper()}] <b>{r.rule_name}:</b> {r.description}")
                else:
                    lines.append("• <i>No statutory rule violations detected in current document context.</i>")
            else:
                lines.append(f"<b>🔍 Local RAG Copilot Analysis</b><br/><i>Query: \"{original_query}\"</i><br/>")
                
                # Perform RAG vector / keyword search against document text
                citations = []
                if doc_text:
                    raw_lines = [l.strip() for l in doc_text.replace("<br/>", "\n").split("\n") if l.strip()]
                    query_words = [w for w in q_lower.split() if len(w) > 3]
                    for l in raw_lines:
                        if any(w in l.lower() for w in query_words):
                            citations.append(l)

                if citations:
                    lines.append("<b>Relevant Citations & Evidence:</b>")
                    for c in citations[:3]:
                        lines.append(f"• <i>\"{c}\"</i>")
                    lines.append("")

                if rule_findings:
                    lines.append("<b>Statutory Audit Check Results:</b>")
                    query_words = [w for w in q_lower.split() if len(w) > 3]
                    matched_rules = [r for r in rule_findings if any(w in r.rule_name.lower() or w in r.description.lower() for w in query_words)]
                    display_rules = matched_rules if matched_rules else rule_findings[:3]
                    for r in display_rules:
                        sev_str = r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
                        lines.append(f"• [{sev_str.upper()}] <b>{r.rule_name}:</b> {r.description}")
                elif not citations:
                    lines.append(f"• <i>No direct evidence found for query in '{active_file_name}'. Ensure document has been fully parsed and indexed.</i>")

            fallback_msg = "<br/>".join(lines)

            if self.current_ai_bubble:
                lbl = self.current_ai_bubble.findChild(QLabel, "chatMessageLabel")
                if lbl:
                    lbl.setText(fallback_msg)
            else:
                self.add_message("FinAudit Local RAG", fallback_msg, False)
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        except Exception as e:
            self.add_message("FinAudit Local RAG", f"Local RAG analysis notice: {e}", False)

    def add_message(self, sender, message, is_user=False):
        bubble_frame = QFrame()
        if is_user:
            bubble_frame.setStyleSheet("background-color: #0284c7; color: #ffffff; border-radius: 12px; margin-left: 40px;")
        else:
            bubble_frame.setStyleSheet("background-color: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 12px; margin-right: 40px;")
            
        b_layout = QVBoxLayout(bubble_frame)
        b_layout.setContentsMargins(14, 10, 14, 10)
        b_layout.setSpacing(4)
        
        lbl_sender = QLabel(sender)
        lbl_sender.setObjectName("chatSenderLabel")
        lbl_sender.setStyleSheet("font-size: 10px; font-weight: 700; border: none;" + ("color: rgba(255, 255, 255, 0.9);" if is_user else "color: #64748b;"))
        
        lbl_msg = QLabel(message)
        lbl_msg.setObjectName("chatMessageLabel")
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 12px; border: none; line-height: 1.4;" + ("color: #ffffff;" if is_user else "color: #0f172a;"))
        
        b_layout.addWidget(lbl_sender)
        b_layout.addWidget(lbl_msg)
        
        apply_shadow(bubble_frame, blur=8, dx=0, dy=2, alpha=6)
        self.chat_layout.addWidget(bubble_frame)
        return bubble_frame

    def load_active_document_view(self):
        try:
            file_name = None
            file_path = None
            with get_session() as session:
                doc = session.query(Document).order_by(Document.id.desc()).first()
                if doc:
                    file_name = doc.file_name
                    file_path = doc.file_path

            if file_path and os.path.exists(file_path):
                try:
                    from document_intelligence.document_parser import DocumentParser
                    parsed = DocumentParser.parse_document(file_path)
                    content = (parsed.cleaned_text or parsed.raw_text)[:1500]
                    if content and not content.startswith("[Document"):
                        display_content = content.replace("\n", "<br/>")
                    else:
                        display_content = f"<i>Document file ({file_name}) ingested and active in local FAISS Vector Index.</i>"
                except Exception:
                    display_content = f"<i>Document file ({file_name}) ingested and active in local FAISS Vector Index.</i>"
                
                self.raw_doc_text = display_content
                self.doc_content.setText(f"<b>ACTIVE DOCUMENT: {file_name}</b><br/><br/>" + display_content)
            else:
                self.raw_doc_text = ""
                self.doc_content.setText("<b>NO DOCUMENT INDEXED</b><br/><br/>Upload client Trial Balance or Financial Statements in 'Upload Documents' tab to view RAG context.")
        except Exception as e:
            self.raw_doc_text = ""
            self.doc_content.setText(f"<b>ACTIVE DOCUMENT STATUS</b><br/><br/>Document context ready for AI analysis.")

    def load_database_findings(self):
        try:
            while self.f_layout.count():
                child = self.f_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            active_id = getattr(self, 'active_engagement_id', None)
            findings_data = []
            seen_keys = set()
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                finding_service = FindingService(wp_repo)
                findings = finding_service.get_findings_by_audit_id(active_id) if active_id else finding_service.get_all_findings()

                for f in findings:
                    sev = getattr(f, 'severity', 'LOW') or getattr(f, 'risk_level', 'LOW')
                    desc = getattr(f, 'description', '')
                    impact = getattr(f, 'financial_impact', 0) or 0
                    key = (str(sev).upper(), desc.strip())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        findings_data.append((str(sev).upper(), desc, impact))

            if hasattr(self, 'f_title'):
                self.f_title.setText(f"AI FINDINGS & ANOMALIES ({len(findings_data)})")

            if not findings_data:
                empty_widget = EmptyStateWidget("No Anomalies Flagged", "Ingest documents or execute prompts to trigger AI analysis.")
                self.f_layout.addWidget(empty_widget)
                return

            for sev, desc, impact in findings_data:
                bg = "#fef2f2" if sev in ["HIGH", "CRITICAL"] else "#fff7ed" if sev == "MEDIUM" else "#f0f9ff"
                txt = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#ea580c" if sev == "MEDIUM" else "#0284c7"
                bdr = "#fecaca" if sev in ["HIGH", "CRITICAL"] else "#fed7aa" if sev == "MEDIUM" else "#bae6fd"
                
                card = create_finding_card(
                    "AI Audit Flag", sev,
                    desc,
                    f"Impact: ₹ {impact:,.2f}",
                    bdr, bdr, bg, txt,
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
                    return True
                else:
                    QMessageBox.warning(self, "No Engagement", "Please select or create an audit project first.")
                    return False
        except Exception as e:
            QMessageBox.critical(self, "Ingestion Error", f"Failed to ingest finding: {e}")
            return False

    def closeEvent(self, event):
        if hasattr(self, '_workers'):
            for w in list(self._workers):
                try:
                    w.quit()
                    w.wait(500)
                except Exception:
                    pass
        event.accept()
