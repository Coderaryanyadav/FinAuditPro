"""
Analytics Export Engine for FinAuditPro.
Exports executive intelligence metrics to JSON, CSV, and Markdown summaries.
"""

from typing import Dict, Any
import json
import csv
import logging

logger = logging.getLogger(__name__)

class AnalyticsExportEngine:
    """Exports BI dashboard metrics to disk."""

    @staticmethod
    def export_to_json(metrics_dict: Dict[str, Any], output_path: str) -> str:
        """Export analytics dictionary to formatted JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_dict, f, indent=2)
        return output_path

    @staticmethod
    def export_to_csv(flat_metrics: Dict[str, Any], output_path: str) -> str:
        """Export key-value metrics to CSV file."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric Name", "Value"])
            for k, v in flat_metrics.items():
                writer.writerow([k, str(v)])
        return output_path
