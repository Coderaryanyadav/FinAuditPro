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
    """Exports structured audit findings and working papers to Excel/CSV with formula injection defense."""

    @staticmethod
    def sanitize_value(val: Any) -> Any:
        """Sanitize values against CSV/Excel formula injection (=, +, -, @, \\t, \\r)."""
        if isinstance(val, str) and val.startswith(("=", "+", "-", "@", "\t", "\r")):
            return f"'{val}"
        return val

    @classmethod
    def sanitize_records(cls, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize list of dictionary rows."""
        sanitized = []
        for r in records:
            sanitized_row = {k: cls.sanitize_value(v) for k, v in r.items()}
            sanitized.append(sanitized_row)
        return sanitized

    @classmethod
    def export_findings_to_csv(cls, findings: List[Dict[str, Any]], output_path: str) -> str:
        """Export list of finding dictionaries to CSV."""
        if not findings:
            return ""

        sanitized_findings = cls.sanitize_records(findings)
        headers = ["rule_id", "rule_name", "category", "severity", "risk_score", "description", "recommendation"]
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                for row in sanitized_findings:
                    writer.writerow(row)
            return output_path
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"CSV export failed: {e}")
            return ""

    @classmethod
    def export_audit_summary_to_excel(
        cls,
        findings: List[Dict[str, Any]],
        working_papers: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """Export multi-tab audit workbook using pandas/openpyxl if available."""
        sanitized_findings = cls.sanitize_records(findings) if findings else []
        sanitized_wp = cls.sanitize_records(working_papers) if working_papers else []
        try:
            import pandas as pd
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                if sanitized_findings:
                    df_findings = pd.DataFrame(sanitized_findings)
                    df_findings.to_excel(writer, sheet_name="Audit Findings", index=False)

                if sanitized_wp:
                    df_wp = pd.DataFrame(sanitized_wp)
                    df_wp.to_excel(writer, sheet_name="Working Papers", index=False)

            return output_path
        except (ImportError, OSError, ValueError, RuntimeError, Exception) as e:
            logger.warning(f"Pandas/OpenPyXL not available ({e}). Falling back to CSV export.")
            csv_path = output_path.replace(".xlsx", ".csv")
            return cls.export_findings_to_csv(sanitized_findings, csv_path)
