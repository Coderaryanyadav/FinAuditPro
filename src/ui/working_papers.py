from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QLineEdit, 
                               QTextEdit, QComboBox, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import Client, AuditProject, WorkingPaper
from ai.engine import OllamaWorker

class WorkingPaperWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.session = SessionLocal()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("Working Paper Generator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        h_layout.addWidget(title)
        
        # Select project dropdown
        h_layout.addSpacing(40)
        proj_lbl = QLabel("Audit Project:")
        proj_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold;")
        h_layout.addWidget(proj_lbl)
        
        self.project_combo = QComboBox()
        self.project_combo.setFixedWidth(260)
        self.project_combo.setStyleSheet("QComboBox { padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #ffffff; color: #0f172a; }")
        self.project_combo.currentIndexChanged.connect(self.load_working_paper)
        h_layout.addWidget(self.project_combo)
        
        h_layout.addStretch()
        
        self.ai_btn = QPushButton("Generate AI Draft")
        self.ai_btn.setStyleSheet("background-color: #8b5cf6; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px;")
        self.ai_btn.clicked.connect(self.generate_ai_draft)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        self.save_btn.clicked.connect(self.save_working_paper)
        
        h_layout.addWidget(self.ai_btn)
        h_layout.addWidget(self.save_btn)
        main_layout.addWidget(header)
        
        # Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(32, 32, 32, 32)
        b_layout.setSpacing(24)
        
        # Form
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        f_layout = QVBoxLayout(form_frame)
        f_layout.setSpacing(16)
        f_layout.setContentsMargins(24, 24, 24, 24)
        
        def add_field(label_text, placeholder, is_textarea=False):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: bold; color: #334155; font-size: 13px; border: none;")
            f_layout.addWidget(lbl)
            
            if is_textarea:
                field = QTextEdit()
                field.setFixedHeight(80)
            else:
                field = QLineEdit()
                field.setFixedHeight(40)
                
            field.setPlaceholderText(placeholder)
            field.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #0f172a; font-size: 13px;")
            f_layout.addWidget(field)
            return field
            
        self.objective_field = add_field("Audit Objective", "e.g., To verify existence and valuation of inventory")
        self.procedure_field = add_field("Procedure", "e.g., Physical verification and reconciliation with ledger", True)
        self.evidence_field = add_field("Evidence", "e.g., Inventory sheet signed by management")
        self.observation_field = add_field("Observation", "e.g., Discrepancy of 5% noted in raw materials", True)
        self.conclusion_field = add_field("Conclusion", "e.g., Requires adjustment entry to align physical and book stock")
        
        b_layout.addWidget(form_frame)
        b_layout.addStretch()
        
        scroll.setWidget(body)
        main_layout.addWidget(scroll)
        
        self.worker = None
        self.load_audit_projects()
        
    def load_audit_projects(self):
        self.project_combo.clear()
        projects = self.session.query(AuditProject).all()
        for proj in projects:
            client = self.session.query(Client).filter_by(id=proj.client_id).first()
            name = client.name if client else "Unknown Client"
            display_text = f"{name} ({proj.financial_year})"
            self.project_combo.addItem(display_text, proj.id)
            
    def load_working_paper(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        
        wp = self.session.query(WorkingPaper).filter_by(audit_id=proj_id).first()
        if wp:
            self.objective_field.setText(wp.objective or "")
            self.procedure_field.setPlainText(wp.procedure or "")
            self.evidence_field.setText(wp.evidence or "")
            self.observation_field.setPlainText(wp.observation or "")
            self.conclusion_field.setText(wp.conclusion or "")
        else:
            self.objective_field.clear()
            self.procedure_field.clear()
            self.evidence_field.clear()
            self.observation_field.clear()
            self.conclusion_field.clear()

    def save_working_paper(self):
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
        
        self.session.commit()
        QMessageBox.information(self, "Saved", "Working paper saved successfully!")

    def generate_ai_draft(self):
        obj = self.objective_field.text().strip()
        proc = self.procedure_field.toPlainText().strip()
        
        if not obj or not proc:
            QMessageBox.warning(self, "Missing Fields", "Please fill in Audit Objective and Procedure to generate AI observation and conclusion draft.")
            return
            
        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("Generating...")
        
        # Clear output fields
        self.observation_field.clear()
        self.conclusion_field.clear()
        
        prompt = f"Draft an audit observation and conclusion based on objective: '{obj}' and procedure: '{proc}'"
        
        self.worker = OllamaWorker(raw_query=prompt)
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_chunk(self, text):
        # We write observation and then split/parse conclusion
        current = self.observation_field.toPlainText()
        self.observation_field.setPlainText(current + text)

    def on_ai_finished(self):
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("Generate AI Draft")
        
        # Dynamic layout separation: Split last paragraph of observation into conclusion
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
