from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, QTextEdit, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from ai.engine import OllamaWorker

def create_styled_button(text, bg_color, text_color, hover_color=None):
    btn = QPushButton(text)
    if hover_color:
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_color}; color: {text_color}; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 11px; }}
            QPushButton:hover {{ background-color: {hover_color}; }}
        """)
    else:
        btn.setStyleSheet(f"background-color: {bg_color}; color: {text_color}; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 11px;")
    return btn

def create_finding_card(title, severity, desc, evidence, border_color, top_border_color, badge_bg, badge_text_color):
    card = QFrame()
    card.setStyleSheet(f"background-color: #ffffff; border: 1px solid {border_color}; border-radius: 8px; margin-bottom: 12px;")
    
    # Left colored strip
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
    v.setContentsMargins(16, 16, 16, 16)
    
    # Header
    h1 = QHBoxLayout()
    t = QLabel(title)
    t.setStyleSheet("font-weight: bold; font-size: 13px; color: #0f172a;")
    b = QLabel(severity)
    b.setStyleSheet(f"background-color: {badge_bg}; color: {badge_text_color}; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;")
    h1.addWidget(t)
    h1.addStretch()
    h1.addWidget(b)
    v.addLayout(h1)
    
    # Desc
    d = QLabel(desc)
    d.setWordWrap(True)
    d.setStyleSheet("color: #475569; font-size: 11px; margin-top: 4px; margin-bottom: 8px;")
    v.addWidget(d)
    
    # Evidence Box
    ev = QFrame()
    ev.setStyleSheet("background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 6px;")
    ev_l = QVBoxLayout(ev)
    ev_l.setContentsMargins(10, 10, 10, 10)
    ev_t = QLabel("EVIDENCE / REFERENCE")
    ev_t.setStyleSheet("color: #64748b; font-size: 9px; font-weight: bold; margin-bottom: 2px;")
    ev_d = QLabel(evidence)
    ev_d.setStyleSheet("color: #0f172a; font-size: 11px; font-family: monospace;")
    ev_l.addWidget(ev_t)
    ev_l.addWidget(ev_d)
    v.addWidget(ev)
    
    # Buttons
    h2 = QHBoxLayout()
    h2.addStretch()
    btn1 = QPushButton("Dismiss")
    btn1.setStyleSheet("background-color: transparent; color: #64748b; font-size: 11px; font-weight: 500; border: none; padding: 4px 8px;")
    btn2 = QPushButton("Review")
    btn2.setStyleSheet(f"background-color: {badge_bg}; color: {badge_text_color}; border: 1px solid {border_color}; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
    h2.addWidget(btn1)
    h2.addWidget(btn2)
    v.addLayout(h2)
    
    clayout.addWidget(content)
    return card

class AIAuditWidget(QWidget):
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
        
        breadcrumbs = QLabel("<b>Workspace</b> <span style='color:#94a3b8;'>/</span> <span style='color:#0ea5e9;'>AI Audit Analysis</span> <span style='color:#94a3b8;'>/</span> <span style='background-color:#f1f5f9; padding:2px 6px; border-radius:4px; font-family:monospace; font-size:11px;'>TechCorp_Q3_Financials</span>")
        breadcrumbs.setStyleSheet("color: #0f172a; font-size: 13px; border: none;")
        header_layout.addWidget(breadcrumbs)
        header_layout.addStretch()
        
        active_badge = QLabel("🟢 AI Engine Active")
        active_badge.setStyleSheet("background-color: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(active_badge)
        
        main_layout.addWidget(header)
        
        # 2. Body Layout (3 Columns)
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
        c1_title = QLabel("DOCUMENT VIEWER")
        c1_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #1e293b; border: none;")
        c1_h_layout.addWidget(c1_title)
        c1_layout.addWidget(c1_header)
        
        doc_scroll = QScrollArea()
        doc_scroll.setWidgetResizable(True)
        doc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        doc_content = QLabel("<b>[Simulated Document View]</b><br/><br/>INVOICE #INV-402<br/>Date: 12-Oct-2025<br/><br/>Item: Software License ($3,000.00)<br/>Item: Consulting ($1,500.00)<br/>Subtotal: $4,500.00<br/>Tax (12%): <span style='color:red;'>$540.00</span><br/><br/>TOTAL: $5,040.00")
        doc_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc_content.setStyleSheet("background-color: #ffffff; margin: 20px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 4px; font-family: monospace; font-size: 12px; color: #64748b;")
        doc_scroll.setWidget(doc_content)
        c1_layout.addWidget(doc_scroll)
        
        # COL 2: AI Chat
        col2 = QFrame()
        col2.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        c2_layout = QVBoxLayout(col2)
        c2_layout.setContentsMargins(0, 0, 0, 0)
        
        c2_header = QFrame()
        c2_header.setFixedHeight(60)
        c2_header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #f1f5f9;")
        c2_h_layout = QHBoxLayout(c2_header)
        bot_icon = QLabel("🤖")
        bot_icon.setFixedSize(32, 32)
        bot_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_icon.setStyleSheet("background-color: #e0f2fe; border-radius: 16px; font-size: 16px; border: none;")
        bot_text = QLabel("<b>FinAudit Copilot</b><br/><span style='color:#64748b; font-size:10px;'>Enterprise Audit Model (Local)</span>")
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
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(16)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_area.setWidget(self.chat_widget)
        c2_layout.addWidget(self.chat_area)
        
        # Chat Input
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #ffffff; border-top: 1px solid #e2e8f0;")
        i_layout = QVBoxLayout(input_frame)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI about this document or findings...")
        self.chat_input.setFixedHeight(40)
        self.chat_input.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0 16px; color: #0f172a; font-size: 13px;")
        
        chips = QHBoxLayout()
        chips.addWidget(QPushButton("Summarize anomalies", styleSheet="background-color: #f1f5f9; color: #475569; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px;"))
        chips.addWidget(QPushButton("Verify tax calculations", styleSheet="background-color: #f1f5f9; color: #475569; border: none; border-radius: 4px; padding: 4px 8px; font-size: 10px;"))
        chips.addStretch()
        
        i_layout.addWidget(self.chat_input)
        i_layout.addLayout(chips)
        c2_layout.addWidget(input_frame)
        
        # COL 3: Findings
        col3 = QFrame()
        col3.setStyleSheet("background-color: #f8fafc;")
        c3_layout = QVBoxLayout(col3)
        c3_layout.setContentsMargins(0, 0, 0, 0)
        
        c3_header = QFrame()
        c3_header.setFixedHeight(60)
        c3_header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        c3_h_layout = QHBoxLayout(c3_header)
        f_title = QLabel("<b>AI Findings Panel</b> <span style='background-color:#fee2e2; color:#b91c1c; font-size:10px; padding:2px 6px; border-radius:8px;'>5 Issues</span><br/><span style='color:#64748b; font-size:11px; font-weight:normal;'>Auto-detected anomalies</span>")
        f_title.setStyleSheet("border: none; font-size: 14px; color: #0f172a;")
        c3_h_layout.addWidget(f_title)
        c3_h_layout.addStretch()
        c3_layout.addWidget(c3_header)
        
        findings_scroll = QScrollArea()
        findings_scroll.setWidgetResizable(True)
        findings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        findings_widget = QWidget()
        f_layout = QVBoxLayout(findings_widget)
        f_layout.setContentsMargins(20, 20, 20, 20)
        f_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        f_layout.addWidget(create_finding_card(
            "Suspicious Entry", "CRITICAL",
            "A manual journal entry for a significant amount ($12,000) was recorded on a weekend.",
            "Ledger: JE-40988 | Date: 14-Oct | User: TEMP",
            "#e9d5ff", "#9333ea", "#f3e8ff", "#7e22ce"
        ))
        
        f_layout.addWidget(create_finding_card(
            "Incorrect Tax Calculation", "HIGH",
            "Tax amount on invoice does not match the expected statutory rate.",
            "Expected 18% ($810), Found 12% ($540)",
            "#fecaca", "#ef4444", "#fef2f2", "#b91c1c"
        ))
        
        f_layout.addWidget(create_finding_card(
            "Duplicate Transaction", "MEDIUM",
            "Identical journal entries found on the same date.",
            "Ledger: JE-40921 repeated on 12-Oct",
            "#fde68a", "#f59e0b", "#fffbeb", "#b45309"
        ))
        
        findings_scroll.setWidget(findings_widget)
        c3_layout.addWidget(findings_scroll)
        
        body_layout.addWidget(col1, 3)
        body_layout.addWidget(col2, 4)
        body_layout.addWidget(col3, 3)
        
        main_layout.addWidget(body)
        
        self.add_message("FinAudit Copilot", "I've ingested the <b>TechCorp Q3 Financials</b> dataset. I have identified <b>5 critical anomalies</b>. How can I help you?", False)
        
        self.chat_input.returnPressed.connect(self.handle_input)
        self.current_ai_bubble = None
        self.worker = None

    def handle_input(self):
        text = self.chat_input.text().strip()
        if not text: return
        self.chat_input.clear()
        
        # Add user message
        self.add_message("CA", text, True)
        
        # Add placeholder AI message
        self.current_ai_bubble = self.add_message("FinAudit Copilot", "Analyzing financial evidence...", False)
        
        from ai.audit_copilot import AuditCopilot
        from ai.context_retriever import ContextRetriever
        from ai.workers import AICopilotWorker
        from PySide6.QtCore import QThreadPool

        try:
            retriever = ContextRetriever()
            copilot = AuditCopilot(context_retriever=retriever)
            
            def run_analysis():
                return copilot.analyze_document(text, engagement_id=1)
                
            self.worker = AICopilotWorker(run_analysis)
            self.worker.signals.result.connect(self.on_copilot_result)
            self.worker.signals.error.connect(self.on_copilot_error)
            QThreadPool.globalInstance().start(self.worker)
        except Exception as e:
            print(f"Copilot Error: {e}")
            if self.current_ai_bubble:
                self.current_ai_bubble.setText(f"Analysis error: {e}")

    def on_copilot_result(self, result):
        if self.current_ai_bubble and isinstance(result, dict):
            summary = result.get("summary", "Analysis completed.")
            severity = result.get("severity", "Low")
            std = result.get("accounting_standard", "SA 240")
            risk = result.get("risk_score", 0)
            
            formatted_resp = f"<b>Summary:</b> {summary}<br/><br/>" \
                             f"<b>Risk Score:</b> {risk}/100 ({severity} Severity)<br/>" \
                             f"<b>Standard:</b> {std}<br/>" \
                             f"<b>Next Step:</b> {result.get('next_audit_procedure', 'Perform verification.')}"
            self.current_ai_bubble.setText(formatted_resp)
        self.current_ai_bubble = None

    def on_copilot_error(self, err_tuple):
        if self.current_ai_bubble:
            self.current_ai_bubble.setText(f"AI Execution Error: {err_tuple[0]}")
        self.current_ai_bubble = None
        
    def add_message(self, sender, text, is_user=False):
        msg = QFrame()
        msg.setStyleSheet("border: none; background: transparent;")
        l = QHBoxLayout(msg)
        l.setContentsMargins(0,0,0,0)
        
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        
        if is_user:
            bubble.setStyleSheet("background-color: #0ea5e9; color: white; padding: 12px 16px; border-radius: 16px; border-top-right-radius: 4px; font-size: 13px;")
            l.addStretch()
            l.addWidget(bubble)
        else:
            icon = QLabel("🤖")
            icon.setFixedSize(28, 28)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("background-color: #e0f2fe; border-radius: 14px; font-size: 14px;")
            bubble.setStyleSheet("background-color: #ffffff; color: #334155; padding: 12px 16px; border-radius: 16px; border-top-left-radius: 4px; border: 1px solid #e2e8f0; font-size: 13px;")
            l.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)
            l.addWidget(bubble)
            l.addStretch()
            
        self.chat_layout.addWidget(msg)
        return bubble
