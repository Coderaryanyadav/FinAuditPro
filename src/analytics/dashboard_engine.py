"""
Executive Dashboard View Engine for FinAuditPro.
Generates tailored BI data models for CEO, Audit Partner, Senior Auditor, and Junior Auditor dashboards.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from .kpi_engine import KPIMetrics
from .trend_engine import TrendMetrics
from .forecast_engine import ForecastMetrics

@dataclass
class DashboardView:
    role_name: str
    metrics: Dict[str, Any]
    cards: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_name": self.role_name,
            "metrics": self.metrics,
            "cards": self.cards,
            "tables": self.tables,
        }


class ExecutiveDashboardEngine:
    """Generates tailored role-based executive dashboard datasets."""

    @staticmethod
    def get_ceo_dashboard() -> DashboardView:
        return DashboardView(
            role_name="CEO Dashboard",
            metrics={
                "revenue_ytd": "₹ 2.4 Cr",
                "total_clients": 30,
                "total_audits": 48,
                "growth_rate_pct": 24.5,
                "hours_saved": 340.0,
                "compliance_score_pct": 94.8,
            },
            cards=[
                {"title": "Firm Growth Rate", "value": "+24.5%", "status": "Positive"},
                {"title": "Time Saved via AI", "value": "340 Hours", "status": "Efficiency Boost"},
                {"title": "Firm Compliance", "value": "94.8%", "status": "Excellent"},
            ],
            tables=[
                {"name": "Top Client Risks", "headers": ["Client Name", "Industry", "Risk Level"], "rows": [["TechCorp", "IT", "Low"], ["Global Impex", "Import/Export", "Medium"]]}
            ]
        )

    @staticmethod
    def get_partner_dashboard() -> DashboardView:
        return DashboardView(
            role_name="Audit Partner Dashboard",
            metrics={
                "active_engagements": 12,
                "critical_findings": 3,
                "high_risk_clients": 2,
                "review_queue_count": 5,
                "pending_partner_approvals": 4,
            },
            cards=[
                {"title": "Active Engagements", "value": "12", "status": "In Progress"},
                {"title": "Critical Findings", "value": "3 Flagged", "status": "Requires Review"},
                {"title": "Pending Approvals", "value": "4 Reports", "status": "Action Req."},
            ],
            tables=[
                {"name": "Partner Review Queue", "headers": ["Client", "Audit Stage", "Reviewer"], "rows": [["TechCorp", "FINAL_REPORT", "CA Partner"], ["Global Impex", "PARTNER_REVIEW", "CA Partner"]]}
            ]
        )

    @staticmethod
    def get_senior_auditor_dashboard() -> DashboardView:
        return DashboardView(
            role_name="Senior Auditor Dashboard",
            metrics={
                "assigned_audits": 6,
                "pending_ocr": 2,
                "pending_ai": 3,
                "pending_reviews": 4,
                "risk_findings_count": 14,
            },
            cards=[
                {"title": "Assigned Audits", "value": "6 Projects", "status": "Active"},
                {"title": "Pending AI Runs", "value": "3 Queued", "status": "Processing"},
                {"title": "Risk Findings", "value": "14 Items", "status": "Reviewing"},
            ],
            tables=[
                {"name": "My Assigned Engagements", "headers": ["Client", "Current Stage", "Completion %"], "rows": [["TechCorp", "AI_ANALYSIS", "50%"], ["Mega Mart", "DOCUMENT_COLLECTION", "25%"]]}
            ]
        )

    @staticmethod
    def get_junior_auditor_dashboard() -> DashboardView:
        return DashboardView(
            role_name="Junior Auditor Dashboard",
            metrics={
                "todays_tasks": 8,
                "recent_uploads": 14,
                "assigned_clients": 4,
                "pending_working_papers": 5,
            },
            cards=[
                {"title": "Today's Tasks", "value": "8 Pending", "status": "In Progress"},
                {"title": "Recent Uploads", "value": "14 Files", "status": "Completed"},
                {"title": "Pending Working Papers", "value": "5 Papers", "status": "Drafting"},
            ],
            tables=[
                {"name": "Assigned Document Queue", "headers": ["Document Name", "Client", "OCR Status"], "rows": [["Invoice_402.pdf", "TechCorp", "Ingested"], ["Bank_Feb.xlsx", "Global Impex", "Ingested"]]}
            ]
        )
