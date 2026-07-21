"""
Analytics Chart Generator Engine for FinAuditPro.
Provides structured chart data series for PySide6 QtCharts and Matplotlib rendering.
"""

from typing import Dict, Any, List

class AnalyticsChartEngine:
    """Generates structured chart series datasets for executive BI views."""

    @staticmethod
    def get_audit_funnel_chart_data() -> Dict[str, Any]:
        """Audit Completion Funnel Series."""
        return {
            "stages": [
                "Document Collection",
                "OCR & Classification",
                "Rule & Risk Analysis",
                "Working Papers Drafted",
                "Partner Signoff & PDF Report"
            ],
            "counts": [150, 142, 130, 115, 95]
        }

    @staticmethod
    def get_ai_ocr_accuracy_chart_data() -> Dict[str, Any]:
        """AI Confidence & OCR Accuracy Series."""
        return {
            "categories": ["PDF Digital", "Scanned PDF", "Invoice Image", "Excel Ledger", "CSV Export"],
            "ocr_accuracy_pct": [99.2, 94.5, 92.1, 100.0, 100.0],
            "ai_confidence_pct": [98.5, 95.0, 91.0, 99.0, 99.5]
        }
