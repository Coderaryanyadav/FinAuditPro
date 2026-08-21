"""
PDF Compilation Script for FinAuditPro Enterprise Documentation.
Compiles Markdown specification into an IEEE-standard professional PDF document.
"""

import os
import sys

def compile_pdf():
    md_path = "docs/FinAuditPro_Enterprise_Documentation.md"
    pdf_path = "docs/FinAuditPro_Enterprise_Documentation.pdf"

    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        return

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor("#0f172a"), spaceAfter=12)
        h1_style = ParagraphStyle("DocH1", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=colors.HexColor("#0ea5e9"), spaceBefore=14, spaceAfter=6)
        h2_style = ParagraphStyle("DocH2", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#0284c7"), spaceBefore=10, spaceAfter=4)
        body_style = ParagraphStyle("DocBody", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#334155"), leading=13.5)

        story = []

        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                story.append(Spacer(1, 4))
                continue

            if line_str.startswith("# "):
                story.append(Paragraph(line_str.replace("# ", ""), title_style))
                story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0ea5e9"), spaceBefore=4, spaceAfter=12))
            elif line_str.startswith("## "):
                story.append(Paragraph(line_str.replace("## ", ""), h1_style))
            elif line_str.startswith("### "):
                story.append(Paragraph(line_str.replace("### ", ""), h2_style))
            elif line_str.startswith("---"):
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=6))
            else:
                formatted_line = line_str.replace("**", "<b>").replace("**", "</b>")
                story.append(Paragraph(formatted_line, body_style))

        doc.build(story)
        print(f"Successfully compiled IEEE Enterprise Documentation PDF -> {pdf_path}")
    except ImportError:
        print("ReportLab not available. Creating plain text PDF representation.")
        with open(md_path, "r", encoding="utf-8") as f_in:
            content = f_in.read()
        with open(pdf_path.replace(".pdf", ".txt"), "w", encoding="utf-8") as f_out:
            f_out.write(content)
        print(f"Saved text documentation -> {pdf_path.replace('.pdf', '.txt')}")

if __name__ == "__main__":
    compile_pdf()
