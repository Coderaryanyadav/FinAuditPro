"""Context-Aware In-Workflow AI Copilot Drawer for FinAuditPro.

Persistent slide-over panel accessible across any engagement phase via Cmd+K / Ctrl+K.
"""

from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos_copilot import CopilotContextDTO
from finauditpro.domain.entities import Engagement


class CopilotWorkerThread(QThread):
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


class AICopilotDrawer(QFrame):
    """Slide-over persistent AI Copilot Drawer with Context Awareness."""

    closed = Signal()

    def __init__(self, ai_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ai_service = ai_service
        self.context = CopilotContextDTO()
        self.current_engagement: Engagement | None = None
        self.active_thread: CopilotWorkerThread | None = None
        self.setFixedWidth(380)
        self.setObjectName("ai_copilot_drawer")
        self.setStyleSheet("""
            QFrame#ai_copilot_drawer {
                background-color: #1a1e24;
                border-left: 1px solid #2d3540;
            }
        """)
        self._init_ui()

    def set_context(self, context: CopilotContextDTO) -> None:
        """Update active operational context and refresh dynamic prompts."""
        self.context = context
        view_lbl = context.current_view or "Command Center"
        client_lbl = context.client or "Global Workspace"
        self.lbl_context.setText(f"View: {view_lbl} | {client_lbl}")
        self._update_quick_prompts(view_lbl)

    def set_engagement(self, engagement: Engagement | None) -> None:
        self.current_engagement = engagement
        if engagement:
            audit_t = engagement.audit_type.value if hasattr(engagement.audit_type, "value") else str(engagement.audit_type)
            self.context = CopilotContextDTO(
                client=self.context.client,
                client_id=self.context.client_id,
                financial_year=engagement.financial_year,
                engagement=audit_t,
                engagement_id=engagement.id,
                current_view=self.context.current_view,
            )
            self.lbl_context.setText(f"Active: {audit_t} ({engagement.financial_year})")
        else:
            self.lbl_context.setText("Active: Global Workspace (No Engagement)")

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🤖 AI Audit Copilot")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        self.lbl_context = QLabel("View: Command Center | Global Workspace")
        self.lbl_context.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_box.addWidget(title)
        title_box.addWidget(self.lbl_context)
        hdr.addLayout(title_box)
        hdr.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet("background: transparent; color: #94a3b8; font-size: 14px; border: none;")
        btn_close.clicked.connect(self.closed.emit)
        hdr.addWidget(btn_close)
        layout.addLayout(hdr)

        # Quick Prompts
        lbl_quick = QLabel("Contextual Statutory Prompts (Cmd+K)")
        lbl_quick.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b;")
        layout.addWidget(lbl_quick)

        self.quick_widget = QWidget()
        self.quick_box = QVBoxLayout(self.quick_widget)
        self.quick_box.setContentsMargins(0, 0, 0, 0)
        self.quick_box.setSpacing(6)
        layout.addWidget(self.quick_widget)
        self._update_quick_prompts("Command Center")

        # Chat scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: 1px solid #2d3540; border-radius: 8px;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        self.scroll.setWidget(self.chat_container)
        layout.addWidget(self.scroll, 1)

        # Input box
        input_bar = QHBoxLayout()
        self.inp_query = QLineEdit()
        self.inp_query.setPlaceholderText("Ask audit query or Cmd+K...")
        self.inp_query.setStyleSheet("""
            QLineEdit {
                background: #0f172a; border: 1px solid #334155; border-radius: 6px;
                padding: 8px 12px; color: #f8fafc; font-size: 12px;
            }
            QLineEdit:focus { border-color: #3b82f6; }
        """)
        self.inp_query.returnPressed.connect(self._handle_send)
        input_bar.addWidget(self.inp_query)

        self.btn_send = QPushButton("Ask")
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #3b82f6; color: #ffffff; border: 1px solid transparent;
                border-radius: 6px; padding: 8px 14px; font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        self.btn_send.clicked.connect(self._handle_send)
        input_bar.addWidget(self.btn_send)
        layout.addLayout(input_bar)

    def _update_quick_prompts(self, view_name: str) -> None:
        # Clear existing quick prompt buttons
        while self.quick_box.count():
            item = self.quick_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        prompt_map = {
            "Client Workspace": [
                ("Missing Documents", "What documents are still missing for this client?"),
                ("Engagement Summary", "Summarize active engagements and audit status."),
            ],
            "Documents": [
                ("Summarize Document", "Summarize this document and identify important audit evidence."),
                ("PII & Contract Scan", "Scan for sensitive terms and key contract obligations."),
            ],
            "TB/GL Scrutiny": [
                ("Unusual Transactions", "Show unusual transactions or round-sum journal entries."),
                ("Section 40A(3) Scan", "Check for cash payments exceeding statutory limits."),
            ],
            "Working Papers": [
                ("Supporting Evidence", "Find supporting evidence for this conclusion."),
                ("CARO 2020 Clause Check", "Verify physical inventory & asset title deed compliance."),
            ],
            "Reconciliations": [
                ("Explain Unmatched Entries", "Explain these unmatched entries and exceptions."),
                ("GST 2B vs Purchase Scan", "Highlight ITC mismatches exceeding threshold."),
            ],
            "Work Center": [
                ("Attention Items", "What needs my attention across tasks and review notes?"),
                ("Pending AI Tasks", "List AI-suggested tasks requiring human confirmation."),
            ],
        }

        default_prompts = [
            ("What Needs Attention?", "What needs my attention?"),
            ("CARO 2020 Review", "Analyze uploaded inventory & fixed asset evidence under CARO 2020."),
            ("Sec 188 Related Party Scan", "Check for related party transactions under Section 188."),
        ]

        prompts = prompt_map.get(view_name, default_prompts)
        for label, text in prompts:
            btn = QPushButton(f"💡 {label}")
            btn.setStyleSheet("""
                QPushButton {
                    background: #22272e; color: #cbd5e1; border: 1px solid #334155;
                    border-radius: 6px; padding: 5px 8px; font-size: 11px; text-align: left;
                }
                QPushButton:hover { background: #2d3540; border-color: #3b82f6; color: #ffffff; }
            """)
            btn.clicked.connect(lambda _, t=text: self._send_prompt(t))
            self.quick_box.addWidget(btn)

    def _send_prompt(self, text: str) -> None:
        self.inp_query.setText(text)
        self._handle_send()

    def _handle_send(self) -> None:
        text = self.inp_query.text().strip()
        if not text:
            return
        self.inp_query.clear()
        self._add_message(text, is_user=True)

        if not self.ai_service:
            self._add_message("Local AI service is not initialized.", is_user=False)
            return

        self.btn_send.setEnabled(False)
        self.inp_query.setEnabled(False)
        loading_lbl = QLabel("  Synthesizing AI Advisory evidence...")
        loading_lbl.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        self.chat_layout.addWidget(loading_lbl)

        def do_query() -> Any:
            if hasattr(self.ai_service, "query_copilot"):
                return self.ai_service.query_copilot(self.context, text)
            eng_id = self.context.engagement_id or (self.current_engagement.id if self.current_engagement else None)
            return self.ai_service.query_rag(prompt=text, engagement_id=eng_id)

        self.active_thread = CopilotWorkerThread(do_query)

        def on_done(res: Any) -> None:
            self.chat_layout.removeWidget(loading_lbl)
            loading_lbl.deleteLater()
            self.btn_send.setEnabled(True)
            self.inp_query.setEnabled(True)
            ans = getattr(res, "response_text", str(res))
            citations = getattr(res, "evidence_citations", getattr(res, "retrieved_chunks", []))
            self._add_message(ans, is_user=False, citations=citations)

        def on_fail(err: str) -> None:
            self.chat_layout.removeWidget(loading_lbl)
            loading_lbl.deleteLater()
            self.btn_send.setEnabled(True)
            self.inp_query.setEnabled(True)
            self._add_message(f"### 🤖 AI Advisory\n\n**Notice:** Copilot error: {err}", is_user=False)

        self.active_thread.completed.connect(on_done)
        self.active_thread.failed.connect(on_fail)
        self.active_thread.start()

    def _add_message(self, text: str, is_user: bool, citations: list[Any] | None = None) -> None:
        bubble = QFrame()
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(10, 8, 10, 8)
        b_layout.setSpacing(4)

        if is_user:
            bubble.setStyleSheet("background: #1e293b; border-radius: 8px; border: 1px solid #334155;")
            sender = QLabel("Auditor")
            sender.setStyleSheet("font-size: 10px; font-weight: 700; color: #93c5fd;")
        else:
            bubble.setStyleSheet("background: #0f172a; border-radius: 8px; border: 1px solid #1e293b;")
            sender = QLabel("FinAudit AI Copilot (Advisory)")
            sender.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8;")

        b_layout.addWidget(sender)

        content = QLabel(text)
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 12px; color: #f1f5f9; line-height: 1.4;")
        b_layout.addWidget(content)

        if citations:
            c_box = QHBoxLayout()
            c_box.setSpacing(4)
            lbl_c = QLabel("Citations:")
            lbl_c.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
            c_box.addWidget(lbl_c)
            for c in citations[:3]:
                doc_name = c.get("title", c.get("document_name", "Evidence")) if isinstance(c, dict) else str(c)
                tag = QLabel(doc_name[:22])
                tag.setStyleSheet("background: #334155; color: #cbd5e1; border-radius: 4px; font-size: 9px; padding: 2px 4px;")
                c_box.addWidget(tag)
            c_box.addStretch()
            b_layout.addLayout(c_box)

        self.chat_layout.addWidget(bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
