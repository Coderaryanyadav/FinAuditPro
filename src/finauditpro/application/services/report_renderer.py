"""Pure rendering helpers for statutory audit report artifacts (SA 700, CARO 2020, Summaries)."""

import os
import tempfile
from pathlib import Path
from typing import Any

_MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "finauditpro_matplotlib_config"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(_MPL_CONFIG_DIR)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from finauditpro.domain.export_sanitizer import escape_formula_injection
from finauditpro.domain.report_entities import Report, ReportTypeEnum


class WatermarkedCanvas(canvas.Canvas):  # type: ignore[misc]
    """Draw a prominent watermark on draft reports."""

    def __init__(self, *args: Any, is_draft: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_draft = is_draft

    def showPage(self) -> None:
        if self.is_draft:
            self.saveState()
            self.setFont("Helvetica-Bold", 46)
            self.setFillColor(colors.Color(0.9, 0.2, 0.2, alpha=0.16))
            self.translate(300, 400)
            self.rotate(45)
            self.drawCentredString(0, 0, "DRAFT — NOT FOR ISSUANCE")
            self.restoreState()
        super().showPage()


def _generate_chart(findings: list[dict[str, Any]], chart_path: Path) -> None:
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for finding in findings:
        s = finding.get("severity", "MEDIUM").upper()
        counts[s if s in counts else "MEDIUM"] += 1
    plt.figure(figsize=(4.8, 2.2))
    plt.bar(list(counts), list(counts.values()), color=["#ef4444", "#f59e0b", "#10b981"], width=0.5)
    plt.title("Identified Audit Exceptions by Risk Level", fontsize=9, fontweight="bold")
    plt.ylabel("Exception Count", fontsize=8)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=130)
    plt.close()


def _build_sa700_story(story: list[Any], report: Report, data: dict[str, Any], styles: Any) -> None:
    client_name = data.get("client_name", "the Company")
    fy = data.get("financial_year", "2025-26")
    findings = data.get("findings", [])
    h2 = styles["Heading2"]
    norm = styles["Normal"]

    # SA 705 Opinion Modification Evaluation
    high_findings = [f for f in findings if f.get("severity", "").upper() == "HIGH"]
    is_qualified = len(high_findings) > 0

    story.append(Paragraph("<b>INDEPENDENT AUDITOR'S REPORT</b>", styles["Heading1"]))
    story.append(Paragraph(f"<b>To the Members of {client_name}</b>", norm))
    story.append(Spacer(1, 8))

    if is_qualified:
        story.append(Paragraph("<b>1. Qualified Opinion (SA 705 Revised)</b>", h2))
        story.append(
            Paragraph(
                f"We have audited the financial statements of <b>{client_name}</b> ({fy}). "
                f"In our opinion and to the best of our information and according to the explanations given to us, "
                f"<b>except for the effects of the matter(s) described in the Basis for Qualified Opinion section of our report</b>, "
                f"the aforesaid financial statements give a true and fair view in conformity with the accounting principles generally accepted in India.",
                norm,
            )
        )
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>2. Basis for Qualified Opinion</b>", h2))
        for hf in high_findings:
            title = hf.get("title", "Material Audit Exception")
            desc = hf.get(
                "description", "Material exception identified during substantive testing."
            )
            story.append(Paragraph(f"• <b>{title}</b>: {desc}", norm))
        story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("<b>1. Unmodified Opinion (SA 700)</b>", h2))
        story.append(
            Paragraph(
                f"We have audited the financial statements of <b>{client_name}</b>, which comprise the Balance Sheet as at "
                f"March 31, 2026, the Statement of Profit and Loss, and the Statement of Cash Flows for the year then ended ({fy}), "
                f"and notes to the financial statements, including a summary of significant accounting policies.<br/>"
                f"In our opinion and to the best of our information and according to the explanations given to us, the aforesaid "
                f"financial statements give the information required by the Companies Act, 2013 in the manner so required and give a "
                f"true and fair view in conformity with the accounting principles generally accepted in India.",
                norm,
            )
        )
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>2. Basis for Opinion (SA 200 / SA 500)</b>", h2))
        story.append(
            Paragraph(
                "We conducted our audit in accordance with the Standards on Auditing (SAs) specified under section 143(10) of the Act. "
                "Our responsibilities under those Standards are further described in the Auditor’s Responsibilities section of our report. "
                "We believe that the audit evidence we have obtained is sufficient and appropriate to provide a basis for our opinion.",
                norm,
            )
        )
        story.append(Spacer(1, 8))

    story.append(Paragraph("<b>3. Key Audit Matters (SA 701)</b>", h2))
    if findings:
        story.append(
            Paragraph(
                f"Key audit matters are those matters that, in our professional judgment, were of most significance in our audit. "
                f"During the audit period, {len(findings)} reportable audit observations were assessed and tested:",
                norm,
            )
        )
    else:
        story.append(Paragraph("No reportable Key Audit Matters identified for disclosure.", norm))
    story.append(Spacer(1, 8))


def _build_caro_story(story: list[Any], data: dict[str, Any], styles: Any) -> None:
    client_name = data.get("client_name", "the Company")
    findings = data.get("findings", [])
    norm = styles["Normal"]

    story.append(
        Paragraph("<b>ANNEXURE 'A' TO THE INDEPENDENT AUDITOR'S REPORT</b>", styles["Heading1"])
    )
    story.append(
        Paragraph(
            f"Referred to in paragraph 1 under 'Report on Other Legal and Regulatory Requirements' section of our report to the members "
            f"of <b>{client_name}</b> of even date on the financial statements for the year ended March 31, 2026.<br/>"
            f"In terms of the information and explanations sought by us and given by the Company and the books of account and records "
            f"examined by us in the normal course of audit, and to the best of our knowledge and belief, we state that:",
            norm,
        )
    )
    story.append(Spacer(1, 10))

    # Check for linked findings dynamically per CARO clause
    has_stat_dues_finding = any(
        "statutory" in f.get("title", "").lower() or "tax" in f.get("title", "").lower()
        for f in findings
    )
    stat_dues_text = (
        "Undisputed statutory dues have been regularly deposited, except for matters noted in Audit Exception Register."
        if has_stat_dues_finding
        else "Regular in depositing undisputed statutory dues (GST, PF, ESI, Income Tax) with appropriate authorities."
    )

    caro_items = [
        (
            "Clause (i)",
            "Property, Plant & Equipment",
            "Proper records maintained; physical verification conducted at reasonable intervals; no material discrepancies.",
        ),
        (
            "Clause (ii)",
            "Inventory Physical Verification",
            "Physical verification conducted by management; coverage and procedure appropriate; discrepancies < 10%.",
        ),
        (
            "Clause (iii)",
            "Loans & Investments",
            "Loans, investments, guarantees granted are not prejudicial to the interest of the Company.",
        ),
        ("Clause (vii)", "Statutory Dues Regularity", stat_dues_text),
        (
            "Clause (ix)",
            "Borrowings Default",
            "No default in repayment of loans or other borrowings or in the payment of interest thereon to any lender.",
        ),
        (
            "Clause (xiii)",
            "Related Party Transactions",
            "Compliance with sections 177 and 188 of Companies Act 2013 for all related party transactions.",
        ),
        (
            "Clause (xvii)",
            "Cash Loss Incurrence",
            "The Company has not incurred cash losses in the financial year and in the immediately preceding financial year.",
        ),
    ]
    rows = [["Clause", "Statutory Head", "Auditor Observation & Compliance State"]]
    for c, h, o in caro_items:
        rows.append([c, h, o])

    t = Table(rows, colWidths=[1.1 * inch, 1.8 * inch, 4.2 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))


def render_pdf(report: Report, data: dict[str, Any], pdf_path: Path, is_draft: bool) -> None:
    """Render a PDF from supplied report data without performing database access."""
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
    )
    story = [Paragraph(f"<b>FinAuditPro — {report.title}</b>", title_style), Spacer(1, 6)]
    story.append(
        Paragraph(
            f"<b>Data As-Of:</b> {data.get('as_of', '')[:19]} | <b>Generated By:</b> {report.generated_by}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 10))

    if report.report_type == ReportTypeEnum.SA_700_AUDIT_REPORT:
        _build_sa700_story(story, report, data, styles)
    elif report.report_type == ReportTypeEnum.CARO_2020_REPORT:
        _build_caro_story(story, data, styles)

    # Findings Table & Chart
    findings = data.get("findings", [])
    chart_path = None
    if findings:
        chart_path = pdf_path.with_suffix(".chart.png")
        _generate_chart(findings, chart_path)
        if chart_path.exists():
            story.extend([RLImage(chart_path, width=4.2 * inch, height=1.9 * inch), Spacer(1, 10)])

    story.append(Paragraph("<b>Audit Findings & Procedure Summary</b>", styles["Heading2"]))
    rows = [["Title", "Severity", "Status", "Amount (Paise)", "Source"]]
    rows.extend(
        [
            [
                escape_formula_injection(item.get("title", "")),
                escape_formula_injection(item.get("severity", "")),
                escape_formula_injection(item.get("status", "")),
                str(item.get("amount_paise", 0)),
                "[AI]" if item.get("is_ai_generated") else "Deterministic",
            ]
            for item in findings
        ]
    )
    if len(rows) == 1:
        rows.append(["No adverse findings recorded.", "LOW", "Compliant", "0", "Standard"])
    table = Table(rows, colWidths=[2.6 * inch, 0.9 * inch, 1.1 * inch, 1.3 * inch, 1.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
        )
    )
    story.append(table)
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: WatermarkedCanvas(*args, is_draft=is_draft, **kwargs),
    )
    if chart_path and chart_path.exists():
        chart_path.unlink(missing_ok=True)
