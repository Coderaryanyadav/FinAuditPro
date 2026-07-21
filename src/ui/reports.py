from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QMarginsF
from PySide6.QtGui import QPdfWriter, QTextDocument, QPageLayout, QPageSize
from database.database import SessionLocal
from database.models import Client, Finding

class ReportsWidget(QWidget):
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
        
        title = QLabel("Report Generator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        h_layout.addWidget(title)
        
        h_layout.addStretch()
        
        preview_btn = QPushButton("Preview")
        preview_btn.setStyleSheet("background-color: #f1f5f9; color: #475569; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px;")
        
        export_btn = QPushButton("Export PDF")
        export_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        export_btn.clicked.connect(self.export_pdf)
        
        h_layout.addWidget(preview_btn)
        h_layout.addWidget(export_btn)
        main_layout.addWidget(header)
        
        # Body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(32, 32, 32, 32)
        b_layout.setSpacing(24)
        
        # Generator controls
        controls_frame = QFrame()
        controls_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        c_layout = QHBoxLayout(controls_frame)
        
        c_lbl = QLabel("Generate Audit Report")
        c_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #0f172a; border: none;")
        
        gen_btn = QPushButton("Refresh Report Draft")
        gen_btn.setStyleSheet("background-color: #0ea5e9; color: white; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        gen_btn.clicked.connect(self.load_report_draft)
        
        c_layout.addWidget(c_lbl)
        c_layout.addStretch()
        c_layout.addWidget(gen_btn)
        
        b_layout.addWidget(controls_frame)
        
        # Mock Report Editor
        editor_frame = QFrame()
        editor_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        e_layout = QVBoxLayout(editor_frame)
        
        editor_title = QLabel("Report Draft Editor")
        editor_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a; padding: 12px; border-bottom: 1px solid #e2e8f0;")
        e_layout.addWidget(editor_title)
        
        self.editor_content = QLabel()
        self.editor_content.setStyleSheet("background-color: #f8fafc; margin: 16px; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; color: #334155; line-height: 1.6;")
        self.editor_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        e_layout.addWidget(self.editor_content)
        b_layout.addWidget(editor_frame)
        b_layout.addStretch()
        
        scroll.setWidget(body)
        main_layout.addWidget(scroll)
        
        self.load_report_draft()
        
    def load_report_draft(self):
        client = self.session.query(Client).first()
        client_name = client.name if client else "TechCorp Solutions Pvt Ltd"
        
        findings = self.session.query(Finding).all()
        matters_html = ""
        for f in findings:
            parts = f.description.split("|")
            issue = parts[0].strip() if parts else f.description
            matters_html += f"<li><b>{issue}</b> - Flagged as {f.risk_level} Risk</li>"
            
        if not matters_html:
            matters_html = "<li>No critical audit matters detected.</li>"
            
        report_html = f"""
        <b>Audit Report Draft Summary</b><br/>
        ------------------------------------------<br/>
        <b>Executive Summary</b><br/>
        We have completed the offline financial verification and audit procedures for <b>{client_name}</b>. 
        Based on data verification and algorithmic risk parsing, our local audit engine notes the following summary findings.<br/><br/>
        
        <b>Key Audit Matters Identified:</b><br/>
        <ul>
            {matters_html}
        </ul>
        <br/>
        <i>Drafted automatically by FinAudit Copilot (Offline CA Assistant)</i>
        """
        self.editor_content.setText(report_html)

    def export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Audit Report as PDF",
            "Audit_Report.pdf",
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return
            
        try:
            # QTextDocument parses internal html formats beautifully
            doc = QTextDocument()
            doc.setHtml(self.editor_content.text())
            
            # Setup PDF Writer
            writer = QPdfWriter(file_path)
            writer.setPageSize(QPageSize.PageSizeId.A4)
            writer.setPageMargins(QMarginsF(40, 40, 40, 40))
            
            doc.print_(writer)
            
            QMessageBox.information(self, "Export Successful", f"PDF report successfully exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while generating PDF:\n{str(e)}")

    def closeEvent(self, event):
        self.session.close()
        event.accept()
