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
from finauditpro.ui.theme import CardWidget

PROMPT_LIBRARY = [
    ("CARO 2020 Inventory", "Analyze uploaded inventory sheets under CARO 2020 Clause (ii)."),
    (
        "Sec 188 Related Party",
        "Check for related party transactions under Section 188 of Companies Act 2013.",
    ),
    ("Sec 185/186 Loans", "Review loan agreements and guarantees for Section 185/186 compliance."),
    ("SA 240 Revenue Anomaly", "Scan sales registers for SA 240 revenue cut-off anomalies."),
    (
        "Form 3CD Clause 44",
        "Break down expenditure split between GST registered and non-registered entities.",
    ),
    (
        "SA 500 Audit Evidence",
        "Perform substantive verification on supporting vouchers per SA 500.",
    ),
]

QUICK_PILLS = [
    "Revenue Anomalies",
    "Vendor Balances",
    "GST 2B Discrepancies",
    "Inventory >10%",
    "Sec 188",
]


class AIWorkerThread(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, func: Any) -> None:
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
        parent = next((a for a in args if isinstance(a, QWidget)), None)
        super().__init__(parent)

        self.ai_service = None
        self.document_service = None
        self.engagement_service = None

        for a in args:
            if hasattr(a, "get_engagement") or hasattr(a, "create_engagement"):
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
                fn = getattr(self.engagement_service, "get_engagement", None) or getattr(
                    self.engagement_service, "get_engagement_by_id", None
                )
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
            self.lbl_chat_status.setText("● Offline Rule Engine Active")
            self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #D97706;")
            return

        try:
            status = self.ai_service.check_status()
            if status and getattr(status, "chat_model_loaded", False):
                self.lbl_chat_status.setText("● Local AI RAG Connected")
                self.lbl_chat_status.setStyleSheet(
                    "font-size: 11px; font-weight: 700; color: #15803D;"
                )
                return
        except Exception:
            pass

        self.lbl_chat_status.setText("● Offline Rule Engine Active")
        self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #D97706;")

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        # 1. Header Bar
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background: transparent; border: none;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(0, 0, 0, 0)

        left_v = QVBoxLayout()
        left_v.setSpacing(2)
        title = QLabel("AI Copilot & Investigation")
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; border: none; background: transparent;"
        )
        subtitle = QLabel(
            "Local offline LLM RAG engine, ICAI audit prompt library, and anomaly detection."
        )
        subtitle.setStyleSheet(
            "font-size: 12px; color: #64748B; border: none; background: transparent;"
        )
        left_v.addWidget(title)
        left_v.addWidget(subtitle)
        hdr_layout.addLayout(left_v)
        hdr_layout.addStretch()

        self.lbl_chat_status = QLabel("● Checking Engine...")
        self.lbl_chat_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        hdr_layout.addWidget(self.lbl_chat_status)

        btn_scan = QPushButton("⚡ Run ICAI Audit Scan")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 16px; border: none; } QPushButton:hover { background-color: #1D4ED8; }"
        )
        btn_scan.clicked.connect(self._on_run_icai_scan)
        hdr_layout.addWidget(btn_scan)
        main_layout.addWidget(hdr_frame)

        # 2. 3-Column Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; width: 1px; }")

        # Column 1: Evidence Sources & Prompts
        col1 = CardWidget("EVIDENCE & PROMPTS")
        c1_layout = col1.content_layout

        self.doc_sources_list = QListWidget()
        self.doc_sources_list.setStyleSheet(
            "QListWidget { border: 1px solid #E2E8F0; border-radius: 6px; background-color: #F8FAFC; }"
        )
        c1_layout.addWidget(self.doc_sources_list, 1)

        p_lbl = QLabel("ICAI PROMPT LIBRARY")
        p_lbl.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; margin-top: 4px;"
        )
        c1_layout.addWidget(p_lbl)

        prompt_scroll = QScrollArea()
        prompt_scroll.setWidgetResizable(True)
        prompt_scroll.setFrameShape(QFrame.Shape.NoFrame)
        prompt_scroll.setFixedHeight(160)
        prompt_widget = QWidget()
        pw_layout = QVBoxLayout(prompt_widget)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(4)

        for title_str, prompt_str in PROMPT_LIBRARY:
            btn = QPushButton(title_str)
            btn.setToolTip(prompt_str)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: #F8FAFC; color: #2563EB; font-size: 11px; font-weight: 600; border: 1px solid #BFDBFE; border-radius: 4px; padding: 5px 8px; text-align: left; }"
            )
            btn.clicked.connect(lambda checked=False, p=prompt_str: self._on_prompt_pill_clicked(p))
            pw_layout.addWidget(btn)

        prompt_scroll.setWidget(prompt_widget)
        c1_layout.addWidget(prompt_scroll)
        splitter.addWidget(col1)

        # Column 2: Chat & Reasoning
        col2 = CardWidget("INVESTIGATION COPILOT")
        c2_layout = col2.content_layout

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText(
            "FinAuditPro AI Copilot\n\nAsk questions about financial evidence, verify statutory CARO 2020 clauses, or analyze trial balance anomalies."
        )
        self.chat_display.setStyleSheet(
            "QTextEdit { border: 1px solid #E2E8F0; border-radius: 6px; background-color: #F8FAFC; padding: 10px; font-size: 13px; color: #0F172A; }"
        )
        c2_layout.addWidget(self.chat_display, 1)

        self.reasoning_display = QTextEdit()
        self.reasoning_display.setReadOnly(True)
        self.reasoning_display.setMaximumHeight(65)
        self.reasoning_display.setPlaceholderText("Model reasoning tokens (<think>)...")
        self.reasoning_display.setStyleSheet(
            "QTextEdit { border: 1px solid #FDE68A; border-radius: 4px; background-color: #FFFBEB; padding: 4px; font-size: 11px; color: #92400E; }"
        )
        c2_layout.addWidget(self.reasoning_display)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(4)
        for pill in QUICK_PILLS:
            pbtn = QPushButton(pill)
            pbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            pbtn.setStyleSheet(
                "QPushButton { background-color: #F1F5F9; color: #2563EB; font-size: 10px; font-weight: 600; border: 1px solid #E2E8F0; border-radius: 4px; padding: 2px 6px; }"
            )
            pbtn.clicked.connect(
                lambda checked=False, p=pill: self._on_prompt_pill_clicked(
                    f"Analyze {p} in financial records."
                )
            )
            pills_row.addWidget(pbtn)
        pills_row.addStretch()
        c2_layout.addLayout(pills_row)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText(
            "Ask AI Copilot about evidence, SA 500 compliance, or GST anomalies..."
        )
        self.qa_input.setStyleSheet(
            "QLineEdit { border: 1px solid #CBD5E1; border-radius: 6px; padding: 7px 10px; font-size: 12px; background: #FFFFFF; }"
        )
        self.qa_input.returnPressed.connect(self._on_ask_clicked)

        btn_send = QPushButton("Send →")
        btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_send.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 12px; font-weight: 600; border-radius: 6px; padding: 7px 14px; border: none; }"
        )
        btn_send.clicked.connect(self._on_ask_clicked)

        input_row.addWidget(self.qa_input, 1)
        input_row.addWidget(btn_send)
        c2_layout.addLayout(input_row)
        splitter.addWidget(col2)

        # Column 3: Findings & Evidence
        col3 = CardWidget("FINDINGS & EVIDENCE")
        c3_layout = col3.content_layout

        self.findings_display = QTextEdit()
        self.findings_display.setReadOnly(True)
        self.findings_display.setPlaceholderText(
            "No anomalies flagged.\n\nExecute prompts or run an ICAI scan to generate evidence references."
        )
        self.findings_display.setStyleSheet(
            "QTextEdit { border: 1px solid #E2E8F0; border-radius: 6px; background-color: #FFFFFF; padding: 10px; font-size: 12px; color: #334155; }"
        )
        c3_layout.addWidget(self.findings_display, 1)
        splitter.addWidget(col3)

        splitter.setSizes([240, 460, 300])
        main_layout.addWidget(splitter, 1)

        self.refresh_provider_status()

    def _load_evidence_documents(self) -> None:
        self.doc_sources_list.clear()
        if not self.current_engagement or not self.document_service:
            return
        fn = getattr(self.document_service, "list_documents_for_engagement", None) or getattr(
            self.document_service, "list_documents", None
        )
        if fn:
            docs = fn(self.current_engagement.id)
            for doc in docs:
                name = getattr(doc, "filename", getattr(doc, "original_filename", "Document"))
                self.doc_sources_list.addItem(QListWidgetItem(f"📄 {name}"))


    def _on_prompt_pill_clicked(self, prompt_str: str) -> None:
        self.qa_input.setText(prompt_str)
        self._on_ask_clicked()

    def _resolve_active_engagement(self) -> Engagement | None:
        if self.current_engagement:
            return self.current_engagement
        win = self.window()
        if hasattr(win, "current_engagement") and win.current_engagement:
            self.set_active_engagement(win.current_engagement)
            return self.current_engagement
        if hasattr(win, "eng_selector_combo"):
            data = win.eng_selector_combo.currentData()
            if data and str(data).startswith("eng:") and hasattr(win, "set_active_engagement"):
                win.set_active_engagement(str(data)[4:])
                return self.current_engagement
        return None

    def _on_run_icai_scan(self) -> None:
        if not self._resolve_active_engagement():
            QMessageBox.warning(
                self, "No Active Audit", "Please select an active audit engagement first."
            )
            return
        self.qa_input.setText(
            "Perform full ICAI statutory audit scan (CARO 2020, Sec 188, SA 240) on uploaded documents."
        )
        self._on_ask_clicked()

    def _on_ask_clicked(self) -> None:
        if not self._resolve_active_engagement():
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        q = self.qa_input.text().strip()
        if not q or not self.ai_service or not hasattr(self.ai_service, "query_rag") or not self.current_engagement:
            return

        self.chat_display.setText("⏳ Executing RAG Query against Local LM Studio AI Model...")
        self.reasoning_display.setText("Waiting for model reasoning (<think>) tokens...")

        eng_id = self.current_engagement.id
        ai_svc = self.ai_service

        def _work() -> Any:
            return ai_svc.query_rag(eng_id, q)

        thread = AIWorkerThread(_work)
        thread.completed.connect(self._on_ask_done)
        thread.failed.connect(self._on_ask_error)
        self.active_thread = thread
        thread.start()

    def _on_ask_done(self, res: Any) -> None:
        self.chat_display.setText(res.response_text)

        self.reasoning_display.setText(
            getattr(res, "reasoning_text", "") or "No reasoning (<think>) tokens generated."
        )

        if getattr(res, "retrieved_chunks", None):
            findings_text = "=== RETRIEVED EVIDENCE CHUNKS ===\n\n"
            for c in res.retrieved_chunks:
                findings_text += f"• [{c['chunk_id']}] {c['title']} (Page {c['page_number']})\n"
            self.findings_display.setText(findings_text)
        else:
            self.findings_display.setText("No specific evidence anomalies flagged.")

    def _on_ask_error(self, err: str) -> None:
        QMessageBox.critical(self, "RAG Error", f"Query failed: {err}")
