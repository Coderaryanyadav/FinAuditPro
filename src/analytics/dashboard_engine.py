"""
Executive Dashboard View Engine for FinAuditPro.
Generates tailored BI data models for CEO, Audit Partner, Senior Auditor, and Junior Auditor dashboards.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from database.database import SessionLocal
from database.models import Client, AuditProject, Document, Finding, WorkingPaper
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
        total_clients, total_audits, hours_saved, doc_count = 0, 0, 0.0, 0
        top_risks = []
        try:
            from database.database import SessionLocal
            from database.models import Client, AuditProject, Document
            session = SessionLocal()
            total_clients = session.query(Client).count()
            total_audits = session.query(AuditProject).count()
            doc_count = session.query(Document).count()
            # Real metrics based strictly on database values
            hours_saved = doc_count * 0.5  # Estimated 30 mins saved per document processed
            
            recent_projects = session.query(AuditProject).order_by(AuditProject.id.desc()).limit(5).all()
            for p in recent_projects:
                client = session.query(Client).filter_by(id=p.client_id).first()
                c_name = client.name if client else f"Client #{p.client_id}"
                c_ind = client.industry if client and hasattr(client, "industry") else "N/A"
                top_risks.append([c_name, c_ind, p.risk_level or "Low"])
                
            session.close()
        except Exception:
            pass

        return DashboardView(
            role_name="CEO Dashboard",
            metrics={
                "total_clients": total_clients,
                "total_audits": total_audits,
                "total_documents": doc_count,
                "hours_saved": round(hours_saved, 1),
            },
            cards=[
                {"title": "Firm Total Clients", "value": str(total_clients), "status": "Active"},
                {"title": "Total Engagements", "value": str(total_audits), "status": "Active"},
                {"title": "Documents Processed", "value": str(doc_count), "status": "Ingested"},
            ],
            tables=[
                {"name": "Top Client Risks", "headers": ["Client Name", "Industry", "Risk Level"], "rows": top_risks if top_risks else [["N/A", "N/A", "N/A"]]}
            ]
        )

    @staticmethod
    def get_partner_dashboard() -> DashboardView:
        active_engagements, critical_findings, high_risk_clients = 0, 0, 0
        review_queue = []
        try:
            from database.database import SessionLocal
            from database.models import Client, AuditProject, Finding
            session = SessionLocal()
            active_engagements = session.query(AuditProject).filter(AuditProject.status != 'Completed').count()
            critical_findings = session.query(Finding).filter(Finding.severity == 'High').count()
            high_risk_clients = session.query(AuditProject).filter(AuditProject.risk_level == 'High').count()
            
            # Fetch pending reviews (e.g. In Progress engagements for demo purposes)
            pending_projects = session.query(AuditProject).filter(AuditProject.status.in_(['In Progress', 'Execution'])).limit(5).all()
            for proj in pending_projects:
                client = session.query(Client).filter_by(id=proj.client_id).first()
                client_name = client.name if client else "Unknown"
                review_queue.append([client_name, proj.status, "CA Partner"])
            
            session.close()
        except Exception:
            pass

        return DashboardView(
            role_name="Audit Partner Dashboard",
            metrics={
                "active_engagements": active_engagements,
                "critical_findings": critical_findings,
                "high_risk_clients": high_risk_clients,
                "review_queue_count": len(review_queue),
                "pending_partner_approvals": len(review_queue),
            },
            cards=[
                {"title": "Active Engagements", "value": str(active_engagements), "status": "In Progress"},
                {"title": "Critical Findings", "value": f"{critical_findings} Flagged", "status": "Requires Review"},
                {"title": "Pending Approvals", "value": f"{len(review_queue)} Reports", "status": "Action Req."},
            ],
            tables=[
                {"name": "Partner Review Queue", "headers": ["Client", "Audit Stage", "Reviewer"], "rows": review_queue or [["None", "N/A", "N/A"]]}
            ]
        )

    @staticmethod
    def get_senior_auditor_dashboard() -> DashboardView:
        session = SessionLocal()
        try:
            projects = session.query(AuditProject).all()
            findings_count = session.query(Finding).count()
            docs_count = session.query(Document).count()
            
            rows = []
            for p in projects:
                client = session.query(Client).filter_by(id=p.client_id).first()
                c_name = client.name if client else f"Client #{p.client_id}"
                rows.append([c_name, p.status, f"{int(p.risk_score or 0)}%"])

            return DashboardView(
                role_name="Senior Auditor Dashboard",
                metrics={
                    "assigned_audits": len(projects),
                    "documents_count": docs_count,
                    "risk_findings_count": findings_count,
                },
                cards=[
                    {"title": "Assigned Audits", "value": f"{len(projects)} Projects", "status": "Active"},
                    {"title": "Documents Ingested", "value": f"{docs_count} Files", "status": "Processed"},
                    {"title": "Risk Findings", "value": f"{findings_count} Items", "status": "Reviewing"},
                ],
                tables=[
                    {"name": "My Assigned Engagements", "headers": ["Client", "Current Stage", "Completion %"], "rows": rows or [["No Active Engagements", "--", "--"]]}
                ]
            )
        finally:
            session.close()

    @staticmethod
    def get_junior_auditor_dashboard() -> DashboardView:
        session = SessionLocal()
        try:
            docs = session.query(Document).all()
            clients_count = session.query(Client).count()
            wp_count = session.query(WorkingPaper).count()
            
            rows = []
            for d in docs:
                client = session.query(Client).filter_by(id=d.client_id).first() if hasattr(d, 'client_id') else None
                c_name = client.name if client else "Unassigned"
                rows.append([d.file_name, c_name, d.doc_type or "Ingested"])

            return DashboardView(
                role_name="Junior Auditor Dashboard",
                metrics={
                    "todays_tasks": len(docs),
                    "recent_uploads": len(docs),
                    "assigned_clients": clients_count,
                    "pending_working_papers": wp_count,
                },
                cards=[
                    {"title": "Recent Uploads", "value": f"{len(docs)} Files", "status": "Completed"},
                    {"title": "Assigned Clients", "value": f"{clients_count} Clients", "status": "Active"},
                    {"title": "Pending Working Papers", "value": f"{wp_count} Papers", "status": "Drafting"},
                ],
                tables=[
                    {"name": "Assigned Document Queue", "headers": ["Document Name", "Client", "OCR Status"], "rows": rows or [["No Documents In Queue", "--", "--"]]}
                ]
            )
        finally:
            session.close()
