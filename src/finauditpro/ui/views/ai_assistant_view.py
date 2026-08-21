"""Local AI Assistant View for FinAuditPro (LM Studio + RAG + AI Findings)."""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.ai_service import AIService
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.domain.entities import Engagement
from finauditpro.ui.theme import CardWidget, MetricCard


class AIWorkerThread(QThread):
    """Worker thread running AI operations off the PySide6 UI loop."""

    token_received = Signal(str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.completed.emit(res)
        except Exception as ex:
            self.failed.emit(str(ex))


class AIAssistantView(QWidget):
    """Primary Local AI Workspace View."""

    ai_changed = Signal()

    def __init__(
        self,
        engagement_service: EngagementService,
        ai_service: AIService,
        document_service: DocumentService | None = None,
        planning_service: AuditPlanningService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        self.ai_service = ai_service
        self.document_service = document_service
        self.planning_service = planning_service

        self.current_engagement: Engagement | None = None
        self.active_thread: AIWorkerThread | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header & Live Status Panel
        header = QHBoxLayout()
        title = QLabel("Local AI Subsystem — LM Studio & Privacy-First RAG Copilot")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")
        header.addWidget(title)
        header.addStretch()

        self.status_btn = QPushButton("Refresh Provider Status")
        self.status_btn.clicked.connect(self._refresh_status)
        header.addWidget(self.status_btn)
        layout.addLayout(header)

        status_card = CardWidget("LM Studio Connection & RAG Index Status")
        status_layout = QHBoxLayout()
        self.card_server = MetricCard("LM Studio Server", "Unknown", "http://localhost:1234/v1")
        self.card_chat = MetricCard("Chat Model", "Unknown", "deepseek-r1-distill-qwen-14b")
        self.card_embed = MetricCard("Embeddings Mode", "Unknown", "FAISS / FTS5 Fallback")

        status_layout.addWidget(self.card_server)
        status_layout.addWidget(self.card_chat)
        status_layout.addWidget(self.card_embed)
        status_card.content_layout.addLayout(status_layout)

        idx_layout = QHBoxLayout()
        self.idx_btn = QPushButton("Build / Re-Index Engagement Vector Store")
        self.idx_btn.clicked.connect(self._on_index_clicked)
        idx_layout.addWidget(self.idx_btn)
        idx_layout.addStretch()
        status_card.content_layout.addLayout(idx_layout)
        layout.addWidget(status_card)

        # 2. Splitter Workspace: Q&A Copilot Left | Proposal Creator Right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Streaming Q&A Workspace
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        qa_box = QGroupBox("Engagement RAG Q&A (Cited Evidence)")
        qa_layout = QVBoxLayout(qa_box)

        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText(
            "Ask audit question (e.g., 'What are the payment terms in vendor contracts?')..."
        )
        self.qa_input.returnPressed.connect(self._on_ask_clicked)

        ask_btn = QPushButton("Execute RAG Query")
        ask_btn.clicked.connect(self._on_ask_clicked)

        input_row = QHBoxLayout()
        input_row.addWidget(self.qa_input)
        input_row.addWidget(ask_btn)
        qa_layout.addLayout(input_row)

        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setPlaceholderText(
            "AI streaming response with inline evidence citations will render here..."
        )
        qa_layout.addWidget(self.response_text)

        # Collapsible Model Reasoning Drawer
        self.reasoning_label = QLabel(
            "▼ Model Reasoning (<think> Block — Model Logic, Not Audit Evidence)"
        )
        self.reasoning_label.setStyleSheet("color: #f59e0b; font-weight: 700; margin-top: 6px;")
        self.reasoning_text = QTextEdit()
        self.reasoning_text.setReadOnly(True)
        self.reasoning_text.setMaximumHeight(120)
        self.reasoning_text.setPlaceholderText("DeepSeek-R1 reasoning tokens...")

        qa_layout.addWidget(self.reasoning_label)
        qa_layout.addWidget(self.reasoning_text)
        left_layout.addWidget(qa_box)
        splitter.addWidget(left_widget)

        # Right: AI Finding Proposal Generator
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        prop_box = QGroupBox("AI-Assisted Finding Proposal Generator")
        prop_layout = QVBoxLayout(prop_box)

        self.prop_input = QTextEdit()
        self.prop_input.setPlaceholderText(
            "Paste audit exception text or describe observation to generate a structured Finding proposal..."
        )

        gen_prop_btn = QPushButton("Generate AI Finding Proposal")
        gen_prop_btn.clicked.connect(self._on_propose_clicked)

        prop_layout.addWidget(QLabel("Exception Context:"))
        prop_layout.addWidget(self.prop_input)
        prop_layout.addWidget(gen_prop_btn)
        right_layout.addWidget(prop_box)
        splitter.addWidget(right_widget)

        layout.addWidget(splitter)
        self._refresh_status()

    def set_engagement(self, engagement_id: str | None) -> None:
        if engagement_id:
            try:
                self.current_engagement = self.engagement_service.get_engagement(engagement_id)
            except Exception:
                self.current_engagement = None
        else:
            self.current_engagement = None

        self._refresh_status()

    def _refresh_status(self) -> None:
        try:
            status = self.ai_service.get_status()
            self.card_server.set_value("CONNECTED" if status.is_server_up else "UNAVAILABLE")
            self.card_chat.set_value("LOADED" if status.chat_model_loaded else "NOT LOADED")
            embed_str = (
                "FAISS (LOADED)" if status.embedding_model_loaded else "FTS5 KEYWORD FALLBACK"
            )
            self.card_embed.set_value(embed_str)
        except Exception:
            self.card_server.set_value("OFFLINE")
            self.card_chat.set_value("OFFLINE")
            self.card_embed.set_value("FTS5 FALLBACK")

    def _on_index_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        self.idx_btn.setEnabled(False)
        self.idx_btn.setText("Indexing Document Vectors...")

        def _work():
            return self.ai_service.index_engagement_documents(self.current_engagement.id)

        thread = AIWorkerThread(_work)
        thread.completed.connect(self._on_index_done)
        thread.failed.connect(self._on_index_error)
        self.active_thread = thread
        thread.start()

    def _on_index_done(self, count: int) -> None:
        self.idx_btn.setEnabled(True)
        self.idx_btn.setText("Build / Re-Index Engagement Vector Store")
        QMessageBox.information(
            self, "Indexing Complete", f"Successfully indexed {count} document chunks."
        )
        self._refresh_status()

    def _on_index_error(self, err: str) -> None:
        self.idx_btn.setEnabled(True)
        self.idx_btn.setText("Build / Re-Index Engagement Vector Store")
        QMessageBox.critical(self, "Indexing Failed", f"Failed to index vectors: {err}")

    def _on_ask_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        q = self.qa_input.text().strip()
        if not q:
            return

        self.response_text.setText("⏳ Executing RAG Query against Local LM Studio AI Model...")
        self.reasoning_text.setText("Waiting for model reasoning (<think>) tokens...")

        def _work():
            return self.ai_service.query_rag(self.current_engagement.id, q)

        thread = AIWorkerThread(_work)
        thread.completed.connect(self._on_ask_done)
        thread.failed.connect(self._on_ask_error)
        self.active_thread = thread
        thread.start()

    def _on_ask_done(self, res) -> None:
        self.response_text.setText(res.response_text)
        if res.reasoning_text:
            self.reasoning_text.setText(res.reasoning_text)
        else:
            self.reasoning_text.clear()
            self.reasoning_text.setPlaceholderText("No reasoning (<think>) tokens generated for this response.")

        if res.retrieved_chunks:
            chunks_summary = "\n\n--- Retrieved Evidence Citing Chunks ---\n"
            for c in res.retrieved_chunks:
                chunks_summary += f"• [{c['chunk_id']}] {c['title']} (Page {c['page_number']})\n"
            self.response_text.append(chunks_summary)

    def _on_ask_error(self, err: str) -> None:
        QMessageBox.critical(self, "RAG Error", f"Query failed: {err}")

    def _on_propose_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(
                self, "No Engagement", "Please select an active audit engagement first."
            )
            return

        ctx = self.prop_input.toPlainText().strip()
        if not ctx:
            QMessageBox.warning(self, "Validation Error", "Please enter exception context text.")
            return

        def _work():
            return self.ai_service.propose_finding(self.current_engagement.id, ctx)

        thread = AIWorkerThread(_work)
        thread.completed.connect(self._on_propose_done)
        thread.failed.connect(self._on_propose_error)
        self.active_thread = thread
        thread.start()

    def _on_propose_done(self, finding) -> None:
        QMessageBox.information(
            self,
            "Proposal Created",
            f"AI Finding Proposal Created!\nTitle: {finding.title}\nSeverity: {finding.severity.value}\nLand in Unified Findings as 'Open' (Auditor Review Required).",
        )

    def _on_propose_error(self, err: str) -> None:
        QMessageBox.critical(self, "Proposal Error", f"Failed to generate proposal: {err}")
