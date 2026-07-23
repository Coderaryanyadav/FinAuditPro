"""
Automated Chart Generator Engine for FinAuditPro Reports.
Generates Matplotlib chart image artifacts (Risk Distribution, Heatmap, Compliance) for embedding into PDFs.
"""

import os
import tempfile
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ReportChartGenerator:
    """Generates high-resolution chart images for PDF reports."""

    @staticmethod
    def generate_risk_distribution_chart(low: int, medium: int, high: int, output_dir: Optional[str] = None) -> str:
        """Generates a doughnut chart image for Risk Distribution."""
        output_path = os.path.join(output_dir or tempfile.gettempdir(), "risk_distribution.png")
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            labels = ["Low Risk", "Medium Risk", "High Risk"]
            sizes = [max(low, 1), max(medium, 0), max(high, 0)]
            colors = ["#10b981", "#f59e0b", "#ef4444"]

            fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct="%1.0f%%",
                startangle=140,
                colors=colors,
                textprops=dict(color="#0f172a", fontsize=8)
            )
            # Make it a doughnut chart
            centre_circle = plt.Circle((0, 0), 0.60, fc="white")
            fig.gca().add_artist(centre_circle)

            plt.tight_layout()
            plt.savefig(output_path, transparent=True)
            plt.close(fig)
            return output_path
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to generate risk distribution chart: {e}")
            return ""

    @staticmethod
    def generate_compliance_chart(score_pct: float, output_dir: Optional[str] = None) -> str:
        """Generates compliance score horizontal gauge bar chart."""
        output_path = os.path.join(output_dir or tempfile.gettempdir(), "compliance_score.png")
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(5, 1), dpi=200)
            ax.barh(["Compliance Score"], [score_pct], color="#0ea5e9", height=0.5)
            ax.set_xlim(0, 100)
            ax.set_xlabel("Percentage (%)", fontsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()
            plt.savefig(output_path, transparent=True)
            plt.close(fig)
            return output_path
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to generate compliance chart: {e}")
            return ""
