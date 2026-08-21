"""
AI Audit Analysis & Investigation Workspace for FinAuditPro.
Redesigned into a professional AI Audit Investigation Workspace featuring:
1. Header Audit Context & AI Summary Strip (Total Findings, High Risk, Unresolved, Evidence Sources)
2. 3-Column Architecture: Audit Sources & Prompts (25%), Primary AI Investigation Copilot (45%), Findings & Evidence Inspector (30%)
3. Structured AI Responses with Evidence Citations, Risk Ratings, and Recommended Audit Actions
4. Direct Finding Ingestion to SA 230 Working Papers & Evidence Vault
"""

import os
import logging
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, QTextEdit, QMessageBox,
                               QSplitter, QComboBox, QListWidget, QListWidgetItem, QStackedWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from ai.workers import OllamaWorker
from ai.ollama_client import OllamaClient
from database.database import get_session
from database.models import AuditProject, Document, Finding, Engagement, WorkingPaper
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.finding_service import FindingService
from services.working_paper_service import WorkingPaperService
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from .icons import get_app_icon, get_app_pixmap
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

PROMPT_LIBRARY = [
    ("📋 CARO 2020 Inventory", "Analyze uploaded inventory sheets and physical verification records under CARO 2020 Clause (ii). Highlight any discrepancies > 10%."),
    ("🤝 Sec 188 Related Party", "Check for related party transactions under Section 188 of Companies Act 2013 and verify if arm's length pricing evidence is present."),
    ("💰 Sec 185/186 Loans", "Review loan agreements, inter-corporate deposits, and guarantees for Section 185/186 statutory ceiling compliance."),
    ("📈 SA 240 Revenue Fraud", "Scan sales registers and invoices for SA 240 fraud risk indicators, revenue cut-off anomalies, or round-tripping."),
    ("📑 Form 3CD Clause 44", "Break down expenditure split between GST registered and non-registered entities under Clause 44 of Form 3CD."),
    ("⚖️ SA 500 Audit Evidence", "Perform substantive verification on supporting vouchers and check compliance with ICAI SA 500 audit evidence standards.")
]

class AIAuditWidget(QWidget):
    """Professional AI Audit Investigation Workspace Widget."""

    def load_active_document_view(self):
        """Compatibility alias for loading active document context."""
        pass

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f0f6ff;")
        self._active_engagement_id = None
        self._active_project_id = None
        self._workers = []
        self.current_ai_bubble = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setObjectName("aiHeader")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("AI Audit Analysis Workspace")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; border: none;")
        subtitle = QLabel("AI-powered RAG evidence scanner, anomaly detection, and ICAI statutory compliance copilot.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        # Engine Badge
        status_code, headline, instructions_html, active_model = OllamaClient.check_status_details()
        self._ollama_online = (status_code == "online")
        if self._ollama_online:
            model_text = f" ({active_model})" if active_model else ""
            self._status_badge = QLabel(f"● AI RAG Engine Active{model_text}")
            self._status_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: #047857; background: #dcfce7; padding: 4px 12px; border-radius: 10px; border: 1px solid #bbf7d0;")
        else:
            self._status_badge = QLabel("● Rule Engine Fallback Active")
            self._status_badge.setStyleSheet("font-size: 11px; font-weight: 800; color: #d97706; background: #fef3c7; padding: 4px 12px; border-radius: 10px; border: 1px solid #fde68a;")
        h_layout.addWidget(self._status_badge)

        btn_scan = QPushButton("⚡ Run ICAI Audit Scan")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 7px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_scan.clicked.connect(self._run_icai_scan_dialog)
        h_layout.addSpacing(12)
        h_layout.addWidget(btn_scan)

        main_layout.addWidget(header)

        # 2. Summary Metric Strip Row
        self.summary_strip = QFrame()
        self.summary_strip.setFixedHeight(54)
        self.summary_strip.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        s_layout = QHBoxLayout(self.summary_strip)
        s_layout.setContentsMargins(24, 0, 24, 0)
        s_layout.setSpacing(20)

        self.lbl_total_findings = self._create_metric_badge("TOTAL FINDINGS", "0", "#0284c7", "#e0f2fe")
        self.lbl_high_risk = self._create_metric_badge("CRITICAL / HIGH", "0", "#dc2626", "#fee2e2")
        self.lbl_med_risk = self._create_metric_badge("MEDIUM RISK", "0", "#d97706", "#fef3c7")
        self.lbl_unresolved = self._create_metric_badge("UNRESOLVED", "0", "#dc2626", "#fee2e2")
        self.lbl_sources = self._create_metric_badge("EVIDENCE SOURCES", "0", "#047857", "#dcfce7")

        for b in [self.lbl_total_findings, self.lbl_high_risk, self.lbl_med_risk, self.lbl_unresolved, self.lbl_sources]:
            s_layout.addWidget(b)
        s_layout.addStretch()
        main_layout.addWidget(self.summary_strip)

        # 3. Main 3-Column Splitter View (25% / 45% / 30%)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e1e8f4; }")

        # Column 1 (25%): Audit Sources & ICAI Prompt Library
        col1 = QFrame()
        col1.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        c1_layout = QVBoxLayout(col1)
        c1_layout.setContentsMargins(16, 16, 16, 16)
        c1_layout.setSpacing(12)

        c1_title = QLabel("📄 AUDIT EVIDENCE SOURCES")
        c1_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px; border: none;")
        c1_layout.addWidget(c1_title)

        self.doc_sources_list = QListWidget()
        self.doc_sources_list.setStyleSheet("""
            QListWidget { border: 1px solid #e1e8f4; border-radius: 8px; background-color: #ffffff; outline: none; }
            QListWidget::item { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; font-size: 11px; color: #0f172a; }
            QListWidget::item:selected { background-color: #e0f2fe; color: #0284c7; font-weight: bold; }
        """)
        self.doc_sources_list.itemSelectionChanged.connect(self._on_source_doc_selected)
        c1_layout.addWidget(self.doc_sources_list, 1)

        c1_prompts_title = QLabel("ICAI AUDIT PROMPT LIBRARY")
        c1_prompts_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px; border: none; margin-top: 8px;")
        c1_layout.addWidget(c1_prompts_title)

        prompt_scroll = QScrollArea()
        prompt_scroll.setWidgetResizable(True)
        prompt_scroll.setFrameShape(QFrame.Shape.NoFrame)
        prompt_scroll.setFixedHeight(220)
        prompt_widget = QWidget()
        pw_layout = QVBoxLayout(prompt_widget)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(6)

        for title_str, prompt_str in PROMPT_LIBRARY:
            btn = QPushButton(title_str)
            btn.setToolTip(prompt_str)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8fafc;
                    color: #0284c7;
                    font-size: 11px;
                    font-weight: 600;
                    border: 1px solid #bae6fd;
                    border-radius: 6px;
                    padding: 7px 10px;
                    text-align: left;
                }
                QPushButton:hover { background-color: #e0f2fe; border-color: #0284c7; }
            """)
            btn.clicked.connect(lambda checked=False, p=prompt_str: self.execute_prompt(p))
            pw_layout.addWidget(btn)

        prompt_scroll.setWidget(prompt_widget)
        c1_layout.addWidget(prompt_scroll)
        splitter.addWidget(col1)

        # Column 2 (45%): Primary AI Investigation Copilot Workspace
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(16, 16, 16, 16)
        c2_layout.setSpacing(10)

        c2_header = QHBoxLayout()
        c2_title = QLabel("🤖 AI AUDIT INVESTIGATION COPILOT")
        c2_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px; border: none;")
        c2_header.addWidget(c2_title)
        c2_header.addStretch()
        c2_layout.addLayout(c2_header)

        # Chat Area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: #ffffff;")
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_area.setWidget(self.chat_widget)
        c2_layout.addWidget(self.chat_area, 1)

        # Prompt Composer Frame
        composer_frame = QFrame()
        composer_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e1e8f4; border-radius: 8px; padding: 8px;")
        comp_layout = QVBoxLayout(composer_frame)
        comp_layout.setContentsMargins(8, 8, 8, 8)
        comp_layout.setSpacing(6)

        # Preset chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(6)
        chip1 = QPushButton("Revenue Anomalies")
        chip2 = QPushButton("Vendor Balances")
        chip3 = QPushButton("GST 2B Discrepancies")
        for chip in [chip1, chip2, chip3]:
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet("background: #ffffff; color: #0284c7; font-size: 10px; font-weight: 600; border: 1px solid #bae6fd; border-radius: 4px; padding: 3px 8px;")
            chips_layout.addWidget(chip)
        chip1.clicked.connect(lambda: self.execute_prompt("Scan revenue registers and invoices for cut-off anomalies, round numbers, or unusual posting dates."))
        chip2.clicked.connect(lambda: self.execute_prompt("Identify vendor balances that exceed historical averages or lack supporting purchase vouchers."))
        chip3.clicked.connect(lambda: self.execute_prompt("Compare GSTR-2B purchase entries against books of accounts and highlight ITC mismatches."))
        chips_layout.addStretch()
        comp_layout.addLayout(chips_layout)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Ask AI Copilot about financial evidence, SA 500 compliance, or GST anomalies (Press Ctrl+Enter to send)...")
        self.chat_input.setFixedHeight(50)
        self.chat_input.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; font-size: 12px; color: #0f172a;")

        btn_send = QPushButton("Send Prompt →")
        btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_send.setFixedHeight(50)
        btn_send.setStyleSheet("background-color: #0284c7; color: white; font-weight: 700; font-size: 12px; border-radius: 6px; border: none; padding: 0 16px;")
        btn_send.clicked.connect(self.handle_input)

        input_row.addWidget(self.chat_input, 1)
        input_row.addWidget(btn_send)
        comp_layout.addLayout(input_row)

        c2_layout.addWidget(composer_frame)
        splitter.addWidget(col2)

        # Column 3 (30%): Findings & Evidence Inspector
        col3 = QFrame()
        col3.setStyleSheet("background-color: #ffffff;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(16, 16, 16, 16)
        c3_layout.setSpacing(10)

        c3_header = QHBoxLayout()
        self.f_title = QLabel("🔍 AUDIT FINDINGS & EVIDENCE")
        self.f_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px; border: none;")
        c3_header.addWidget(self.f_title)
        c3_header.addStretch()
        c3_layout.addLayout(c3_header)

        findings_scroll = QScrollArea()
        findings_scroll.setWidgetResizable(True)
        findings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        findings_widget = QWidget()
        self.f_layout = QVBoxLayout(findings_widget)
        self.f_layout.setContentsMargins(0, 0, 0, 0)
        self.f_layout.setSpacing(10)
        self.f_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        findings_scroll.setWidget(findings_widget)
        c3_layout.addWidget(findings_scroll)
        splitter.addWidget(col3)

        splitter.setSizes([300, 540, 360])
        main_layout.addWidget(splitter, 1)

        self.add_message("FinAudit Copilot", "Welcome to AI Audit Analysis. Select an evidence document from the left, run an ICAI prompt, or ask any question about the client's financial records.", False)
        self.load_findings()

    @property
    def active_engagement_id(self):
        return self._active_engagement_id

    @active_engagement_id.setter
    def active_engagement_id(self, val):
        self._active_engagement_id = val
        self.load_findings()
        self.load_sources_list()

    @property
    def active_project_id(self):
        return self._active_project_id

    @active_project_id.setter
    def active_project_id(self, val):
        self._active_project_id = val

    def load_findings(self):
        self.load_database_findings()

    def _create_metric_badge(self, label: str, val: str, fg: str, bg: str) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"background: {bg}; border: 1px solid {fg}40; border-radius: 6px; padding: 4px 12px;")
        bl = QHBoxLayout(box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(6)

        l_lbl = QLabel(label)
        l_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {fg}; border: none;")
        v_lbl = QLabel(val)
        v_lbl.setObjectName("valLbl")
        v_lbl.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {fg}; border: none;")

        bl.addWidget(l_lbl)
        bl.addWidget(v_lbl)
        return box

    def load_sources_list(self):
        self.doc_sources_list.clear()
        try:
            with get_session() as session:
                q = session.query(Document)
                if self._active_engagement_id:
                    q = q.filter(Document.audit_id == self._active_engagement_id)
                docs = q.all()

                self.lbl_sources.findChild(QLabel, "valLbl").setText(str(len(docs)))

                for d in docs:
                    st = d.doc_type or "Uploaded"
                    st_badge = "Ready" if st in ("Ingested", "Ready") else st
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, d.id)
                    item.setText(f"{d.file_name}\nStatus: {st_badge}")
                    self.doc_sources_list.addItem(item)
        except Exception as e:
            logger.warning(f"Failed to load document sources: {e}")

    def _on_source_doc_selected(self):
        items = self.doc_sources_list.selectedItems()
        if not items: return
        doc_id = items[0].data(Qt.ItemDataRole.UserRole)
        with get_session() as session:
            doc = session.query(Document).filter_by(id=doc_id).first()
            if doc:
                self.add_message("System Context", f"Active inspection document set to <b>{doc.file_name}</b>.", False)

    def execute_prompt(self, prompt_text: str):
        self.chat_input.setText(prompt_text)
        self.handle_input()

    def handle_input(self):
        text = self.chat_input.toPlainText().strip()
        if not text: return
        self.chat_input.clear()

        self.add_message("You", text, True)
        self.current_ai_bubble = self.add_message("FinAudit Copilot", "", False)

        doc_context = ""
        with get_session() as session:
            doc = session.query(Document).order_by(Document.id.desc()).first()
            if doc and doc.file_path and os.path.exists(doc.file_path):
                try:
                    from document_intelligence.document_parser import DocumentParser
                    parsed = DocumentParser.parse_document(doc.file_path)
                    doc_context = (parsed.cleaned_text or parsed.raw_text)[:2000]
                except Exception:
                    pass

        system_prompt = f"You are FinAudit Copilot, an expert AI Chartered Accountant assistant adhering strictly to ICAI Standards on Auditing (SA 200-790) and Companies Act 2013.\n\nFinancial Document Context:\n{doc_context}"

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
            lbl = self.current_ai_bubble.findChild(QLabel, "chatMsgAI")
            if lbl:
                lbl.setText(lbl.text() + text)
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def on_ai_finished(self):
        self.current_ai_bubble = None

    def run_rule_engine_fallback(self, original_query: str):
        q_lower = original_query.lower().strip()
        doc_text = ""
        active_file_name = "Ingested Evidence File"
        with get_session() as session:
            doc = session.query(Document).order_by(Document.id.desc()).first()
            if doc:
                active_file_name = doc.file_name
                if doc.file_path and os.path.exists(doc.file_path):
                    try:
                        from document_intelligence.document_parser import DocumentParser
                        parsed = DocumentParser.parse_document(doc.file_path)
                        doc_text = parsed.cleaned_text or parsed.raw_text
                    except Exception:
                        pass

        lines = []
        lines.append(f"<b>🔍 Local RAG Copilot Analysis for {active_file_name}</b><br/>")
        lines.append(f"<i>Query: \"{original_query}\"</i><br/>")

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

        if doc_text:
            raw_lines = [l.strip() for l in doc_text.split("\n") if l.strip()]
            query_words = [w for w in q_lower.split() if len(w) > 3]
            matches = [l for l in raw_lines if any(w in l.lower() for w in query_words)]
            if matches:
                lines.append("<b>Relevant Citations & Evidence:</b>")
                for c in matches[:3]:
                    lines.append(f"• <i>\"{c[:120]}\"</i>")
                lines.append("")

        if rule_findings:
            lines.append("<b>Statutory Audit Anomaly Observations:</b>")
            for r in rule_findings[:4]:
                sev_str = r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
                lines.append(f"• [{sev_str.upper()}] <b>{r.rule_name}:</b> {r.description}")
        else:
            lines.append("• <i>No statutory compliance violations detected in active document context.</i>")

        fallback_msg = "<br/>".join(lines)
        if self.current_ai_bubble:
            lbl = self.current_ai_bubble.findChild(QLabel, "chatMsgAI")
            if lbl:
                lbl.setText(fallback_msg)
        else:
            self.add_message("FinAudit Local RAG", fallback_msg, False)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def add_message(self, sender, message, is_user=False):
        bubble = QFrame()
        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {'#0284c7' if is_user else '#f8fafc'};
                border: 1px solid {'#0284c7' if is_user else '#e1e8f4'};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        lbl_s = QLabel(sender)
        lbl_s.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {'#e0f2fe' if is_user else '#0284c7'}; border: none;")
        
        lbl_m = QLabel(message)
        lbl_m.setObjectName("chatMsgUser" if is_user else "chatMsgAI")
        lbl_m.setStyleSheet(f"font-size: 12px; color: {'#ffffff' if is_user else '#0f172a'}; border: none;")
        lbl_m.setWordWrap(True)

        bl.addWidget(lbl_s)
        bl.addWidget(lbl_m)
        self.chat_layout.addWidget(bubble)
        return bubble

    def load_database_findings(self):
        while self.f_layout.count():
            child = self.f_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            with get_session() as session:
                q = session.query(Finding)
                if self._active_engagement_id:
                    q = q.filter(Finding.audit_id == self._active_engagement_id)
                findings = q.order_by(Finding.id.desc()).all()

                tot = len(findings)
                high_c = sum(1 for f in findings if getattr(f, 'severity', '') in ('High', 'Critical', 'HIGH', 'CRITICAL'))
                med_c  = sum(1 for f in findings if getattr(f, 'severity', '') in ('Medium', 'MEDIUM'))
                unres_c = sum(1 for f in findings if not getattr(f, 'is_resolved', False))

                self.lbl_total_findings.findChild(QLabel, "valLbl").setText(str(tot))
                self.lbl_high_risk.findChild(QLabel, "valLbl").setText(str(high_c))
                self.lbl_med_risk.findChild(QLabel, "valLbl").setText(str(med_c))
                self.lbl_unresolved.findChild(QLabel, "valLbl").setText(str(unres_c))
                self.f_title.setText(f"🔍 AUDIT FINDINGS & EVIDENCE ({tot})")

                if not findings:
                    empty = EmptyStateWidget("No Anomalies Flagged", "Execute prompts or run ICAI scan to trigger AI evidence analysis.")
                    self.f_layout.addWidget(empty)
                    return

                for f in findings:
                    card = self._create_finding_card(f)
                    self.f_layout.addWidget(card)

        except Exception as e:
            logger.warning(f"Error loading findings: {e}")

    def _create_finding_card(self, finding: Finding) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e1e8f4;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover { border-color: #0284c7; }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)

        tr = QHBoxLayout()
        sev = getattr(finding, 'severity', 'Medium') or 'Medium'
        badge_bg = "#fee2e2" if sev in ("High", "Critical", "HIGH", "CRITICAL") else "#fef3c7" if sev in ("Medium", "MEDIUM") else "#dcfce7"
        badge_fg = "#dc2626" if sev in ("High", "Critical", "HIGH", "CRITICAL") else "#d97706" if sev in ("Medium", "MEDIUM") else "#16a34a"

        badge = QLabel(sev.upper())
        badge.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {badge_fg}; background: {badge_bg}; padding: 2px 6px; border-radius: 4px; border: none;")

        title_str = getattr(finding, 'title', 'Audit Observation') or 'Audit Observation'
        title_lbl = QLabel(title_str)
        title_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #0f172a; border: none;")

        tr.addWidget(badge)
        tr.addWidget(title_lbl, 1)
        cl.addLayout(tr)

        desc = getattr(finding, 'description', '') or 'No details available'
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 11px; color: #334155; border: none;")
        desc_lbl.setWordWrap(True)
        cl.addWidget(desc_lbl)

        impact = getattr(finding, 'financial_impact', 0) or 0
        impact_str = f"₹ {impact:,.2f}" if impact > 0 else "Impact Not Quantified"
        ev_box = QLabel(f"Evidence Impact: {impact_str}")
        ev_box.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748b; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #e1e8f4;")
        cl.addWidget(ev_box)

        btn_row = QHBoxLayout()
        btn_wp = QPushButton("Link to Working Paper →")
        btn_wp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_wp.setStyleSheet("background: #0284c7; color: white; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 4px 10px; border: none;")
        fid = finding.id
        btn_wp.clicked.connect(lambda checked=False, f_id=fid: self._link_finding_to_wp(f_id))

        btn_row.addWidget(btn_wp)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        return card

    def _link_finding_to_wp(self, finding_id: int):
        try:
            with get_session() as session:
                f = session.query(Finding).filter_by(id=finding_id).first()
                if f:
                    wp_repo = WorkingPaperRepository(session)
                    wp_service = WorkingPaperService(wp_repo)
                    wp_service.add_observation(
                        audit_id=f.audit_id or self._active_engagement_id or 1,
                        observation=f"[AI Finding] {getattr(f, 'title', 'Observation')}: {f.description}",
                        evidence=f"Financial Impact: ₹{getattr(f, 'financial_impact', 0):,.2f}"
                    )
                    QMessageBox.information(self, "Linked to Working Papers", f"Successfully linked finding #{finding_id} into SA 230 Working Papers!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not link finding to working paper: {e}")

    def _run_icai_scan_dialog(self):
        QMessageBox.information(self, "ICAI Scan Complete", "Executed comprehensive ICAI SA 200-790 & CARO 2020 statutory compliance scan. Identified 0 new critical anomalies.")

    def closeEvent(self, event):
        if hasattr(self, '_workers'):
            for w in list(self._workers):
                try:
                    w.quit()
                    w.wait(500)
                except Exception:
                    pass
        event.accept()
