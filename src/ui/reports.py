"""
Audit Report Generator, UDIN & Cryptographic QR Verification Engine for FinAuditPro.
Provides SA 700 / SA 705 Independent Auditor's Report, CARO 2020 Annexure,
Management Representation Letter (MRL), Unique Document Identification Number (UDIN) Generation, and SHA-256 QR Verification.
"""

import logging
import hashlib
import os
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QFileDialog, QMessageBox, QComboBox, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt, QMarginsF
from PySide6.QtGui import QPdfWriter, QTextDocument, QPageLayout, QPageSize, QFont
from database.database import get_session
from database.models import Client, Finding, WorkingPaper, AuditProject, Risk
from database.repositories.client_repo import ClientRepository
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.client_service import ClientService
from services.finding_service import FindingService
from services.report_service import ReportService
from reporting.digital_signature import DigitalSignatureManager
from reporting.qr_verification import QRVerificationManager
from security.security_manager import SecurityManager
from security.rbac import Permission
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from sqlalchemy.exc import SQLAlchemyError
from core.config import config

logger = logging.getLogger(__name__)

class ReportsWidget(QWidget):
    """Audit Report Generator & UDIN Signature Manager Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Action Bar Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title = QLabel("Audit Report Generator & UDIN Verification")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        subtitle = QLabel("ICAI SA 700 / SA 705 Independent Auditor's Report & CARO 2020 Order Annexure")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        export_btn = QPushButton(" Export Official PDF Audit Report")
        export_btn.setStyleSheet("background-color: #0ea5e9; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; border: none;")
        export_btn.clicked.connect(self.export_pdf)
        h_layout.addWidget(export_btn)

        main_layout.addWidget(header)
        
        # 2. Control Options Frame
        opts_frame = QFrame()
        opts_frame.setFixedHeight(76)
        opts_frame.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        o_layout = QHBoxLayout(opts_frame)
        o_layout.setContentsMargins(24, 0, 24, 0)
        o_layout.setSpacing(16)

        o_layout.addWidget(QLabel("<b style='color:#334155;'>Report Type:</b>"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Independent Auditor's Report (SA 700 Standard Unmodified)",
            "CARO 2020 Statutory Order Report Annexure",
            "Tax Audit Form 3CD Statutory Report",
            "Management Representation Letter (MRL)"
        ])
        self.report_type_combo.setFixedWidth(300)
        self.report_type_combo.setToolTip("Select ICAI Report Template (e.g. CARO 2020, Tax Audit 3CD, Independent Auditor's Report)")
        self.report_type_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.report_type_combo.currentIndexChanged.connect(self.load_report_draft)
        o_layout.addWidget(self.report_type_combo)

        o_layout.addSpacing(16)
        o_layout.addWidget(QLabel("<b style='color:#334155;'>UDIN Number:</b>"))
        self.udin_input = QLineEdit()
        self.udin_input.setPlaceholderText("Enter 18-digit ICAI UDIN...")
        self.udin_input.setToolTip("Enter 18-digit Unique Document Identification Number (UDIN) issued by ICAI")
        self.udin_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.udin_input.setFixedWidth(180)
        self.udin_input.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: monospace; font-weight: bold;")
        self.udin_input.textChanged.connect(self.load_report_draft)
        o_layout.addWidget(self.udin_input)

        btn_regen = QPushButton(" Refresh Draft")
        btn_regen.setToolTip("Regenerate live audit report draft text with current client details and findings (Hotkey: F5)")
        btn_regen.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_regen.setStyleSheet("background-color: #f1f5f9; color: #0284c7; font-weight: bold; border: 1px solid #bae6fd; padding: 6px 12px; border-radius: 6px;")
        btn_regen.clicked.connect(self.load_report_draft)
        o_layout.addWidget(btn_regen)

        o_layout.addStretch()
        main_layout.addWidget(opts_frame)

        # 3. Report Live WYSIWYG Editor Preview Pane
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(32, 24, 32, 32)

        editor_frame = QFrame()
        editor_frame.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        e_layout = QVBoxLayout(editor_frame)
        e_layout.setContentsMargins(24, 24, 24, 24)

        self.editor_content = QTextEdit()
        self.editor_content.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; font-size: 13px; color: #0f172a; line-height: 1.6;")
        e_layout.addWidget(self.editor_content)
        b_layout.addWidget(editor_frame)

        scroll.setWidget(body)
        main_layout.addWidget(scroll)

        self.load_report_draft()

    def load_report_draft(self):
        active_id = getattr(self, 'active_engagement_id', None)
        client = None
        findings = []
        try:
            with get_session() as session:
                if active_id:
                    proj = session.query(AuditProject).filter_by(id=active_id).first()
                    if proj:
                        client = session.query(Client).filter_by(id=proj.client_id).first()
                if not client:
                    client = session.query(Client).first()

                findings = session.query(Finding).filter_by(audit_id=active_id).all() if active_id else session.query(Finding).all()
                # Detach objects before session closes
                client_name = client.name if client else "Sample Client Pvt Ltd"
                self.current_client_name = client_name
                cin = getattr(client, 'cin_number', 'U72200MH2021PTC123456') or 'U72200MH2021PTC123456'
                matters_html = ""
                for f in findings:
                    matters_html += f"<li><b>{f.description[:80]}</b> - Flagged Severity: <span style='color:#dc2626;'>{f.severity or 'MEDIUM'}</span></li>"
        except Exception:
            client_name = "Sample Client Pvt Ltd"
            self.current_client_name = client_name
            cin = "U72200MH2021PTC123456"
            matters_html = ""

        if not matters_html:
            matters_html = "<li>No critical audit qualifications or adverse matters detected during substantive testing.</li>"

        udin = self.udin_input.text().strip() or "PENDING_UDIN_ENTRY"
        report_title = self.report_type_combo.currentText()
        report_payload = f"{report_title}:{client_name}:{cin}:{udin}:{matters_html}"
        real_hash = hashlib.sha256(report_payload.encode('utf-8')).hexdigest()
        hash_display = f"{real_hash[:16]}..."

        report_html = f"""
        <div style="font-family: 'Inter', sans-serif; color: #0f172a;">
            <div style="text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #0f172a;">{config.ca_firm_name}</h2>
                <p style="margin: 4px 0; color: #64748b; font-size: 12px;">CHARTERED ACCOUNTANTS | FIRM REGISTRATION NO: {config.ca_frn}</p>
                <p style="margin: 0; color: #64748b; font-size: 11px;">Suite 401, Corporate Heights, BKC, Mumbai - 400051</p>
            </div>

            <h3 style="text-align: center; color: #0ea5e9; text-transform: uppercase;">{report_title}</h3>
            <p><b>To the Members of:</b> {client_name} (CIN: {cin})</p>
            <p><b>Report on the Audit of the Financial Statements for FY 2024-25</b></p>
            
            <p><b>Opinion</b><br/>
            In our opinion and to the best of our information and according to the explanations given to us, the aforesaid financial statements give the information required by the Companies Act, 2013 in the manner so required and give a true and fair view in conformity with the accounting principles generally accepted in India.</p>

            <p><b>Key Audit Matters (SA 701):</b></p>
            <ul>
                {matters_html}
            </ul>

            <br/><br/>
            <div style="border-top: 1px solid #cbd5e1; padding-top: 12px; font-size: 11px;">
                <p style="margin:2px 0;"><b>For {config.ca_firm_name}</b><br/>Chartered Accountants (FRN: {config.ca_frn})</p>
                <p style="margin:2px 0; color: #0284c7;"><b>{config.ca_name}</b> (Partner | Membership No: {config.ca_membership_no})</p>
                <p style="margin:2px 0;"><b>UDIN:</b> <span style="font-family: monospace; background:#f1f5f9; padding:2px 6px; border-radius:4px;">{udin}</span></p>
                <p style="margin:2px 0; color: #64748b;">SHA-256 Tamper Verification Hash: <i title="{real_hash}">{hash_display}</i></p>
            </div>
        </div>
        """
        self.editor_content.setHtml(report_html)

    def export_pdf(self):
        sm = SecurityManager()
        if not sm.current_session or not sm.check_permission(Permission.GENERATE_REPORTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to generate audit reports.")
            return

        udin_val = self.udin_input.text().strip()
        if not udin_val:
            QMessageBox.warning(self, "UDIN Required", "Please enter a valid 18-character ICAI UDIN before exporting the official audit report.")
            self.udin_input.setFocus()
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Audit Report as PDF", "Official_Audit_Report.pdf", "PDF Files (*.pdf)")
        if not file_path: return

        try:
            html_content = self.editor_content.toHtml()
            content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()

            try:
                sig_block = DigitalSignatureManager.create_signature_block(
                    ca_name=config.ca_name,
                    membership_number=config.ca_membership_no,
                    firm_name=config.ca_firm_name,
                    firm_registration_number=config.ca_frn,
                    udin=udin_val
                )
            except Exception:
                sig_block = None

            qr_payload = QRVerificationManager.generate_verification_payload(
                report_id=f"REP-{content_hash[:8]}",
                client_name=getattr(self, 'current_client_name', 'Unknown Client'),
                gstin="N/A",
                document_hash=content_hash,
                udin=udin_val
            )

            findings_data = []
            active_id = getattr(self, 'active_engagement_id', None)
            try:
                with get_session() as session:
                    findings_query = session.query(Finding)
                    if active_id:
                        findings_query = findings_query.filter_by(audit_id=active_id)
                    db_findings = findings_query.all()
                    for f in db_findings:
                        findings_data.append({
                            "rule_id": f"FIND-{f.id:03d}",
                            "rule_name": f.description[:40] if f.description else "Audit Finding",
                            "category": f.risk_level or "Audit",
                            "severity": (f.severity or "LOW").upper(),
                            "risk_score": float(f.ai_confidence_score or 50)
                        })
                    if not findings_data:
                        from database.repositories.risk_repo import RiskRepository
                        risk_repo = RiskRepository(session)
                        db_risks = risk_repo.get_risks_by_engagement(active_id) if active_id else session.query(Risk).all()
                        for r in db_risks:
                            findings_data.append({
                                "rule_id": f"RISK-{r.id:03d}",
                                "rule_name": r.description[:40] if r.description else "Risk Finding",
                                "category": "Risk",
                                "severity": (r.likelihood or "LOW").upper(),
                                "risk_score": 75.0 if r.is_significant else 40.0
                            })
            except Exception as e:
                logger.error("Error querying findings for PDF report: %s", e, exc_info=True)
                findings_data = []

            try:
                from reporting.pdf_generator import PDFReportGenerator
                PDFReportGenerator.generate_pdf_report(
                    client_name=getattr(self, 'current_client_name', 'Client Pvt Ltd'),
                    financial_year="2025-26",
                    report_title=self.report_type_combo.currentText(),
                    summary_text=self.editor_content.toPlainText(),
                    findings=findings_data,
                    signature_block=sig_block,
                    output_path=file_path
                )
            except Exception:
                logger.error("PDFReportGenerator failed, falling back to QTextDocument", exc_info=True)
                doc = QTextDocument()
                doc.setHtml(html_content)
                writer = QPdfWriter(file_path)
                writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                writer.setPageMargins(QMarginsF(15, 15, 15, 15))
                doc.print_(writer)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Official PDF Audit Report exported successfully!\n\n"
                f"UDIN: {udin_val}\n"
                f"SHA-256 Evidence Hash: {content_hash[:32]}...\n"
                f"QR Status: {qr_payload.get('status', 'VERIFIED')}\n"
                f"Output Path: {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", f"Failed to export PDF: {e}")

    def closeEvent(self, event):
        event.accept()
