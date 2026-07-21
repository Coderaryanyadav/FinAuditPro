"""
High-Quality PDF Compiler Engine for FinAuditPro.
Generates Deloitte/EY/PwC-style PDF reports with ReportLab canvas formatting, headers, footers, tables, and security blocks.
"""

from typing import Dict, Any, List, Optional
import os
import tempfile
import logging

from .digital_signature import SignatureBlock
from .qr_verification import QRVerificationManager

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Compiles professional ICAI-standard PDF audit reports."""

    @staticmethod
    def generate_pdf_report(
        client_name: str,
        financial_year: str,
        report_title: str,
        summary_text: str,
        findings: List[Dict[str, Any]],
        signature_block: Optional[SignatureBlock] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Generates PDF report using ReportLab if available, or HTML/text layout fallback."""
        file_path = output_path or os.path.join(tempfile.gettempdir(), f"Audit_Report_{client_name.replace(' ', '_')}.pdf")

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=54,
                leftMargin=54,
                topMargin=54,
                bottomMargin=54
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "TitleStyle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=12
            )
            h2_style = ParagraphStyle(
                "H2Style",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=colors.HexColor("#0ea5e9"),
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                "BodyStyle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                textColor=colors.HexColor("#334155"),
                leading=14
            )

            story = []

            # 1. Header / Cover Title
            story.append(Paragraph("FinAuditPro Enterprise Audit Platform", ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#0ea5e9"))))
            story.append(Spacer(1, 10))
            story.append(Paragraph(report_title, title_style))
            story.append(Paragraph(f"<b>Client:</b> {client_name} | <b>Financial Year:</b> {financial_year}", body_style))
            story.append(Spacer(1, 15))

            # 2. Executive Summary
            story.append(Paragraph("1. Executive Summary", h2_style))
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 15))

            # 3. Findings Table
            story.append(Paragraph("2. Automated Audit Rule & Risk Findings", h2_style))
            table_data = [["Rule ID", "Rule Name", "Category", "Severity", "Risk Score"]]
            
            for f in findings:
                table_data.append([
                    f.get("rule_id", "--"),
                    f.get("rule_name", "Finding"),
                    f.get("category", "Audit"),
                    f.get("severity", "LOW"),
                    f"{f.get('risk_score', 0):.0f}/100"
                ])

            if len(table_data) > 1:
                t = Table(table_data, colWidths=[65, 180, 110, 75, 70])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ]))
                story.append(t)
            story.append(Spacer(1, 20))

            # 4. Digital Signature & Security Block
            if signature_block:
                story.append(Paragraph("3. ICAI Practitioner Signoff & Verification", h2_style))
                sig_text = f"Signed by: <b>{signature_block.ca_name}</b> (Mem No: {signature_block.membership_number})<br/>" \
                           f"Firm: {signature_block.firm_name} (FRN: {signature_block.firm_registration_number})<br/>" \
                           f"UDIN: <b>{signature_block.udin}</b><br/>" \
                           f"Digital SHA-256 Hash: {signature_block.digital_signature_hash[:32]}..."
                story.append(Paragraph(sig_text, body_style))

            doc.build(story)
            logger.info(f"Generated PDF report at {file_path}")
            return file_path
        except ImportError:
            logger.warning("ReportLab not installed. Falling back to HTML/Text report output.")
            txt_path = file_path.replace(".pdf", ".txt")
            with open(txt_path, "w") as f:
                f.write(f"=== {report_title} ===\nClient: {client_name}\nFY: {financial_year}\n\nSummary:\n{summary_text}\n")
            return txt_path
        except Exception as e:
            logger.error(f"Failed to compile PDF report: {e}")
            return file_path
