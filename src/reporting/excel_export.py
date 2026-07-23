"""
Multi-Tab Excel & CSV Exporter Engine for FinAuditPro.
Exports financial ledgers, audit working papers, failed rules, and risk findings to Excel (.xlsx) workbooks.
"""

from typing import List, Dict, Any, Optional
import os
import csv
import logging

logger = logging.getLogger(__name__)

class ExcelReportExporter:
    """Exports structured audit findings and working papers to Excel/CSV."""

    @staticmethod
    def export_findings_to_csv(findings: List[Dict[str, Any]], output_path: str) -> str:
        """Export list of finding dictionaries to CSV."""
        if not findings:
            return ""

        headers = ["rule_id", "rule_name", "category", "severity", "risk_score", "description", "recommendation"]
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                for row in findings:
                    writer.writerow(row)
            return output_path
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"CSV export failed: {e}")
            return ""

    @staticmethod
    def export_audit_summary_to_excel(
        findings: List[Dict[str, Any]],
        working_papers: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """Export multi-tab audit workbook using pandas/openpyxl if available."""
        try:
            import pandas as pd
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                if findings:
                    df_findings = pd.DataFrame(findings)
                    df_findings.to_excel(writer, sheet_name="Audit Findings", index=False)

                if working_papers:
                    df_wp = pd.DataFrame(working_papers)
                    df_wp.to_excel(writer, sheet_name="Working Papers", index=False)

            return output_path
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"Pandas/OpenPyXL not available ({e}). Falling back to CSV export.")
            csv_path = output_path.replace(".xlsx", ".csv")
            return ExcelReportExporter.export_findings_to_csv(findings, csv_path)
