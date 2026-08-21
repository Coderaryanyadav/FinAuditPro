"""
AI Audit Analysis Workspace View for FinAuditPro.
3-Column Enterprise Architecture:
Column 1: Audit Evidence Sources & ICAI Prompt Library
Column 2: Primary AI Investigation Copilot Chat Window
Column 3: Audit Findings & Evidence Cards Inspector
"""

from typing import Any
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.domain.entities import Engagement

PROMPT_LIBRARY = [
    ("📦 CARO 2020 Inventory", "Analyze uploaded inventory sheets and physical verification records under CARO 2020 Clause (ii)."),
    ("🤝 Sec 188 Related Party", "Check for related party transactions under Section 188 of Companies Act 2013."),
    ("💰 Sec 185/186 Loans", "Review loan agreements, inter-corporate deposits, and guarantees for Section 185/186 statutory ceiling compliance."),
    ("📈 SA 240 Revenue Anomaly", "Scan sales registers and invoices for SA 240 revenue cut-off anomalies or round-tripping."),
    ("📑 Form 3CD Clause 44", "Break down expenditure split between GST registered and non-registered entities under Clause 44 of Form 3CD."),
    ("⚖️ SA 500 Audit Evidence", "Perform substantive verification on supporting vouchers and check compliance with ICAI SA 500 standards."),
]

QUICK_PILLS = ["Revenue Anomalies", "Vendor Balances", "GST 2B Discrepancies", "Inventory Discrepancies >10%", "Sec 188 Compliance"]


class AIWorkerThread(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, func) -> None:
        super().__init__()
        self.func = func

    def run(self) -> None:
        try:
            res = self.func()
            self.completed.emit(res)
        except Exception as ex:
            self.failed.emit(str(ex))


class AIAssistantView(QWidget):
    """Enterprise 3-Column AI Investigation Copilot Workspace Widget."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        parent = None
        for a in args:
            if isinstance(a, QWidget):
                parent = a
                break

        super().__init__(parent)

        self.ai_service = None
        self.document_service = None
        self.engagement_service = None

        for a in args:
            if hasattr(a, "get_engagement") or hasattr(a, "get_engagement_by_id") or hasattr(a, "create_engagement"):
                self.engagement_service = a
            elif hasattr(a, "query_rag") or hasattr(a, "check_status"):
                self.ai_service = a
            elif hasattr(a, "list_documents"):
                self.document_service = a

        if not self.ai_service:
            self.ai_service = kwargs.get("ai_service")

        self.current_engagement: Engagement | None = None
        self.active_thread: AIWorkerThread | None = None

        self._init_ui()

    def set_engagement(self, engagement_id: Any) -> None:
        if isinstance(engagement_id, Engagement):
            self.set_active_engagement(engagement_id)
            return
        if hasattr(self, "engagement_service") and self.engagement_service:
            try:
                fn = getattr(self.engagement_service, "get_engagement", None) or getattr(self.engagement_service, "get_engagement_by_id", None)
                if fn:
                    eng = fn(str(engagement_id))
                    if eng:
                        self.set_active_engagement(eng)
                        return
            except Exception:
                pass
        self.refresh_provider_status()

    def set_active_engagement(self, engagement: Engagement | None) -> None:
        self.current_engagement = engagement
        self.refresh_provider_status()
        self._load_evidence_documents()

    def refresh_provider_status(self) -> None:
        if not self.ai_service or not hasattr(self.ai_service, "check_status"):
            self.lbl_chat_status.setText("● Rule Engine Fallback Active")
            self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #d97706; background: #fef3c7; padding: 4px 12px; border-radius: 10px;")
            return

        try:
            status = self.ai_service.check_status()
            if status and getattr(status, "chat_model_loaded", False):
                self.lbl_chat_status.setText("● Local AI RAG Active (Connected)")
                self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #047857; background: #dcfce7; padding: 4px 12px; border-radius: 10px;")
                return
        except Exception:
            pass

        self.lbl_chat_status.setText("● Rule Engine Fallback Active")
        self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #d97706; background: #fef3c7; padding: 4px 12px; border-radius: 10px;")

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("AI Audit Analysis Workspace")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; border: none;")
        subtitle = QLabel("AI-powered RAG evidence scanner, anomaly detection, and ICAI statutory compliance copilot.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)
        h_layout.addStretch()

        self.lbl_chat_status = QLabel("● Checking Engine...")
        self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 800; color: #64748b;")
        h_layout.addWidget(self.lbl_chat_status)

        btn_scan = QPushButton("⚡ Run ICAI Audit Scan")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet("background-color: #0284c7; color: #ffffff; font-size: 12px; font-weight: 700; border-radius: 6px; padding: 7px 16px; border: none;")
        btn_scan.clicked.connect(self._on_run_icai_scan)
        h_layout.addSpacing(12)
        h_layout.addWidget(btn_scan)

        main_layout.addWidget(header)

        # 2. Metric Strip
        strip = QFrame()
        strip.setFixedHeight(54)
        strip.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        s_layout = QHBoxLayout(strip)
        s_layout.setContentsMargins(24, 0, 24, 0)
        s_layout.setSpacing(16)

        self.lbl_total_findings = self._create_metric_badge("TOTAL FINDINGS", "0", "#0284c7", "#e0f2fe")
        self.lbl_high_risk = self._create_metric_badge("CRITICAL / HIGH", "0", "#dc2626", "#fee2e2")
        self.lbl_med_risk = self._create_metric_badge("MEDIUM RISK", "0", "#d97706", "#fef3c7")
        self.lbl_unresolved = self._create_metric_badge("UNRESOLVED", "0", "#dc2626", "#fee2e2")
        self.lbl_sources = self._create_metric_badge("EVIDENCE SOURCES", "0", "#047857", "#dcfce7")

        for b in [self.lbl_total_findings, self.lbl_high_risk, self.lbl_med_risk, self.lbl_unresolved, self.lbl_sources]:
            s_layout.addWidget(b)
        s_layout.addStretch()
        main_layout.addWidget(strip)

        # 3. 3-Column Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e1e8f4; }")

        # Column 1
        col1 = QFrame()
        col1.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        c1_layout = QVBoxLayout(col1)
        c1_layout.setContentsMargins(16, 16, 16, 16)
        c1_layout.setSpacing(10)

        c1_title = QLabel("📄 AUDIT EVIDENCE SOURCES")
        c1_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px;")
        c1_layout.addWidget(c1_title)

        self.doc_sources_list = QListWidget()
        self.doc_sources_list.setStyleSheet("QListWidget { border: 1px solid #e1e8f4; border-radius: 8px; background-color: #ffffff; }")
        c1_layout.addWidget(self.doc_sources_list, 1)

        c1_prompts_title = QLabel("ICAI AUDIT PROMPT LIBRARY")
        c1_prompts_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px; margin-top: 6px;")
        c1_layout.addWidget(c1_prompts_title)

        prompt_scroll = QScrollArea()
        prompt_scroll.setWidgetResizable(True)
        prompt_scroll.setFrameShape(QFrame.Shape.NoFrame)
        prompt_scroll.setFixedHeight(210)
        prompt_widget = QWidget()
        pw_layout = QVBoxLayout(prompt_widget)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(6)

        for title_str, prompt_str in PROMPT_LIBRARY:
            btn = QPushButton(title_str)
            btn.setToolTip(prompt_str)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background-color: #f8fafc; color: #0284c7; font-size: 11px; font-weight: 600; border: 1px solid #bae6fd; border-radius: 6px; padding: 7px 10px; text-align: left; }")
            btn.clicked.connect(lambda checked=False, p=prompt_str: self._on_prompt_pill_clicked(p))
            pw_layout.addWidget(btn)

        prompt_scroll.setWidget(prompt_widget)
        c1_layout.addWidget(prompt_scroll)
        splitter.addWidget(col1)

        # Column 2
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(16, 16, 16, 16)
        c2_layout.setSpacing(10)

        c2_title = QLabel("🤖 AI AUDIT INVESTIGATION COPILOT")
        c2_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px;")
        c2_layout.addWidget(c2_title)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("FinAuditPro AI Copilot\n\nWelcome to AI Audit Analysis. Select an evidence document from the left, run an ICAI prompt, or ask any question about the client's financial records.")
        self.chat_display.setStyleSheet("QTextEdit { border: 1px solid #e1e8f4; border-radius: 8px; background-color: #f8fafc; padding: 12px; font-size: 13px; color: #0f172a; }")
        c2_layout.addWidget(self.chat_display, 1)

        self.reasoning_display = QTextEdit()
        self.reasoning_display.setReadOnly(True)
        self.reasoning_display.setMaximumHeight(80)
        self.reasoning_display.setPlaceholderText("Model reasoning (<think>) tokens...")
        self.reasoning_display.setStyleSheet("QTextEdit { border: 1px solid #fde68a; border-radius: 6px; background-color: #fffbeb; padding: 6px; font-size: 11px; color: #92400e; }")
        c2_layout.addWidget(self.reasoning_display)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(6)
        for pill in QUICK_PILLS:
            pbtn = QPushButton(pill)
            pbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            pbtn.setStyleSheet("QPushButton { background-color: #f1f5f9; color: #0284c7; font-size: 10px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 8px; }")
            pbtn.clicked.connect(lambda checked=False, p=pill: self._on_prompt_pill_clicked(f"Analyze {p} in financial records."))
            pills_row.addWidget(pbtn)
        pills_row.addStretch()
        c2_layout.addLayout(pills_row)

        input_row = QHBoxLayout()
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText("Ask AI Copilot about financial evidence, SA 500 compliance, or GST anomalies...")
        self.qa_input.setStyleSheet("QLineEdit { border: 1px solid #cbd5e1; border-radius: 6px; padding: 9px 12px; font-size: 13px; color: #0f172a; background: #ffffff; }")
        self.qa_input.returnPressed.connect(self._on_ask_clicked)

        btn_send = QPushButton("Send Prompt ➔")
        btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_send.setStyleSheet("QPushButton { background-color: #0284c7; color: #ffffff; font-size: 12px; font-weight: 700; border-radius: 6px; padding: 9px 16px; border: none; }")
        btn_send.clicked.connect(self._on_ask_clicked)

        input_row.addWidget(self.qa_input, 1)
        input_row.addWidget(btn_send)
        c2_layout.addLayout(input_row)

        splitter.addWidget(col2)

        # Column 3
        col3 = QFrame()
        col3.setStyleSheet("background-color: #ffffff;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(16, 16, 16, 16)
        c3_layout.setSpacing(10)

        c3_title = QLabel("🔍 AUDIT FINDINGS & EVIDENCE")
        c3_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; letter-spacing: 0.8px;")
        c3_layout.addWidget(c3_title)

        self.findings_display = QTextEdit()
        self.findings_display.setReadOnly(True)
        self.findings_display.setPlaceholderText("No Anomalies Flagged\n\nExecute prompts or run ICAI scan to trigger AI evidence analysis.")
        self.findings_display.setStyleSheet("QTextEdit { border: 1px solid #e1e8f4; border-radius: 8px; background-color: #ffffff; padding: 12px; font-size: 12px; color: #334155; }")
        c3_layout.addWidget(self.findings_display, 1)

        splitter.addWidget(col3)
        splitter.setSizes([260, 480, 320])
        main_layout.addWidget(splitter, 1)

        self.refresh_provider_status()

    def _create_metric_badge(self, title: str, val: str, fg: str, bg: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"background-color: {bg}; border-radius: 6px; padding: 4px 12px;")
        l = QHBoxLayout(f)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {fg};")
        v = QLabel(val)
        v.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {fg};")
        l.addWidget(t)
        l.addWidget(v)
        return f

    def _load_evidence_documents(self) -> None:
        self.doc_sources_list.clear()
        if not self.current_engagement or not self.document_service:
            return

        docs = self.document_service.list_documents(self.current_engagement.id)
        for doc in docs:
            self.doc_sources_list.addItem(QListWidgetItem(f"📄 {doc.original_filename}"))

    def _on_prompt_pill_clicked(self, prompt_str: str) -> None:
        self.qa_input.setText(prompt_str)
        self._on_ask_clicked()

    def _on_run_icai_scan(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Active Audit", "Please select an active audit engagement first.")
            return

        self.qa_input.setText("Perform full ICAI statutory audit scan (CARO 2020, Sec 188, SA 240) on uploaded documents.")
        self._on_ask_clicked()

    def _on_ask_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return

        q = self.qa_input.text().strip()
        if not q or not self.ai_service or not hasattr(self.ai_service, "query_rag"):
            return

        self.chat_display.setText("⏳ Executing RAG Query against Local LM Studio AI Model...")
        self.reasoning_display.setText("Waiting for model reasoning (<think>) tokens...")

        def _work():
            return self.ai_service.query_rag(self.current_engagement.id, q)

        thread = AIWorkerThread(_work)
        thread.completed.connect(self._on_ask_done)
        thread.failed.connect(self._on_ask_error)
        self.active_thread = thread
        thread.start()

    def _on_ask_done(self, res) -> None:
        self.chat_display.setText(res.response_text)
        if getattr(res, "reasoning_text", None):
            self.reasoning_display.setText(res.reasoning_text)
        else:
            self.reasoning_display.setText("No reasoning (<think>) tokens generated.")

        if getattr(res, "retrieved_chunks", None):
            findings_text = "=== RETRIEVED EVIDENCE CHUNKS ===\n\n"
            for c in res.retrieved_chunks:
                findings_text += f"• [{c['chunk_id']}] {c['title']} (Page {c['page_number']})\n"
            self.findings_display.setText(findings_text)
        else:
            self.findings_display.setText("No specific evidence anomalies flagged.")

    def _on_ask_error(self, err: str) -> None:
        QMessageBox.critical(self, "RAG Error", f"Query failed: {err}")
