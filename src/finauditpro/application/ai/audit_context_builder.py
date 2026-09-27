"""Audit Context Builder assembling Firm, Client, Engagement, Risks, Procedures, WPs, Evidence, and Findings."""

from typing import Any

from finauditpro.domain.ai_entities import AICopilotContext
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditMatrixRepository,
    ClientRepository,
    DocumentRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    WorkingPaperRepository,
)


class AuditContextBuilder:
    """Assembles rich hierarchical audit context for AI Copilot grounding."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def build_context(
        self,
        engagement_id: str,
        audit_area: str | None = None,
        target_wp_id: str | None = None,
    ) -> AICopilotContext:
        """Construct full engagement context graph from persistence layer."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", engagement_id)

            client_name = "Unknown Client"
            if eng.client_id:
                client = ClientRepository(session).get_by_id(eng.client_id)
                if client:
                    client_name = client.name

            firm_name = "Audit Firm"
            if eng.firm_id:
                firm = FirmRepository(session).get_by_id(eng.firm_id)
                if firm:
                    firm_name = firm.name

            matrix_repo = AuditMatrixRepository(session)
            wp_repo = WorkingPaperRepository(session)
            fin_repo = FinancialDataRepository(session)
            doc_repo = DocumentRepository(session)

            # Retrieve active risks
            all_risks = matrix_repo.list_risks_for_engagement(engagement_id)
            if audit_area:
                all_risks = [r for r in all_risks if r.category.lower() == audit_area.lower()]
            risk_dicts = [
                {
                    "risk_id": r.id,
                    "risk_code": r.risk_code,
                    "title": r.title,
                    "category": r.category,
                    "inherent_risk": r.inherent_risk.value if hasattr(r.inherent_risk, "value") else str(r.inherent_risk),
                    "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
                }
                for r in all_risks[:10]
            ]

            # Retrieve active procedures
            all_procs = matrix_repo.list_procedures_for_engagement(engagement_id)
            if audit_area:
                all_procs = [p for p in all_procs if getattr(p, "account_area", "").lower() == audit_area.lower()]
            proc_dicts = [
                {
                    "procedure_id": p.id,
                    "procedure_code": p.procedure_code,
                    "objective": p.objective,
                    "procedure_type": p.procedure_type,
                    "account_area": getattr(p, "account_area", ""),
                    "methodology": getattr(p, "methodology", ""),
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                }
                for p in all_procs[:10]
            ]

            # Retrieve active working papers
            all_wps = wp_repo.list_for_engagement(engagement_id)
            if target_wp_id:
                all_wps = [w for w in all_wps if w.id == target_wp_id or getattr(w, "index_reference", "") == target_wp_id]
            elif audit_area:
                all_wps = [w for w in all_wps if w.area.lower() == audit_area.lower()]
            wp_dicts = [
                {
                    "working_paper_id": w.id,
                    "index_reference": w.index_reference,
                    "title": w.title,
                    "area": w.area,
                    "status": w.status.value if hasattr(w.status, "value") else str(w.status),
                    "preparer_id": w.preparer_id,
                    "reviewer_id": w.reviewer_id,
                }
                for w in all_wps[:10]
            ]

            # Retrieve active evidence
            all_evd = matrix_repo.list_evidence_for_engagement(engagement_id)
            evd_dicts = [
                {
                    "evidence_id": e.id,
                    "title": e.title,
                    "document_id": e.document_id,
                    "page_number": e.page_number,
                    "excerpt": e.excerpt_or_reference,
                }
                for e in all_evd[:10]
            ]

            # Retrieve active findings
            all_findings = matrix_repo.list_findings_for_engagement(engagement_id)
            if audit_area:
                filtered = [f for f in all_findings if audit_area.lower() in getattr(f, "category", "").lower()]
                if filtered:
                    all_findings = filtered
            finding_dicts = [
                {
                    "finding_id": f.id,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                    "status": f.status.value if hasattr(f.status, "value") else str(f.status),
                    "recommendation": f.recommendation,
                }
                for f in all_findings[:10]
            ]

            # Retrieve active exceptions from financial datasets
            datasets = fin_repo.list_datasets_by_engagement(engagement_id)
            exc_dicts = []
            for ds in datasets[:3]:
                excs = fin_repo.list_exceptions_by_dataset(ds.id)
                for exc in excs[:5]:
                    exc_dicts.append({
                        "exception_id": exc.id,
                        "dataset_id": ds.id,
                        "title": exc.title,
                        "severity": exc.severity,
                        "description": exc.description,
                        "evidence": exc.computed_evidence,
                    })

            return AICopilotContext(
                firm_name=firm_name,
                client_name=client_name,
                engagement_id=engagement_id,
                engagement_title=getattr(eng, "title", None) or f"{eng.audit_type.value if hasattr(eng.audit_type, 'value') else str(eng.audit_type)} FY {eng.financial_year}",
                financial_year=eng.financial_year,
                audit_area=audit_area,
                active_risks=risk_dicts,
                active_procedures=proc_dicts,
                active_working_papers=wp_dicts,
                active_evidence=evd_dicts,
                active_findings=finding_dicts,
                active_exceptions=exc_dicts,
            )

    @classmethod
    def format_context_for_prompt(cls, context: AICopilotContext) -> str:
        """Format the structured context into a clear Markdown block for LLM prompt embedding."""
        lines = [
            f"### AUDIT ENGAGEMENT CONTEXT",
            f"• Firm: {context.firm_name} | Client: {context.client_name}",
            f"• Engagement: {context.engagement_title} (FY {context.financial_year}) [ID: {context.engagement_id}]",
        ]
        if context.audit_area:
            lines.append(f"• Focused Audit Area: {context.audit_area}")

        if context.active_risks:
            lines.append("\n**Active Risks Identified:**")
            for r in context.active_risks:
                lines.append(f"  - [{r['risk_code']}] {r['title']} ({r['severity']} Severity)")

        if context.active_procedures:
            lines.append("\n**Active Audit Procedures:**")
            for p in context.active_procedures:
                lines.append(f"  - [{p['procedure_code']}] {p['objective']} (Status: {p['status']})")

        if context.active_working_papers:
            lines.append("\n**Active Working Papers:**")
            for w in context.active_working_papers:
                lines.append(f"  - [{w['index_reference']}] {w['title']} (Area: {w['area']} | Status: {w['status']})")

        if context.active_evidence:
            lines.append("\n**Linked Audit Evidence:**")
            for e in context.active_evidence:
                lines.append(f"  - [{e['evidence_id']}] {e['title']} (Page {e.get('page_number', 1)}): {e['excerpt'][:100]}")

        if context.active_findings:
            lines.append("\n**Open Findings:**")
            for f in context.active_findings:
                lines.append(f"  - [{f['finding_id']}] {f['title']} ({f['severity']}): {f['description'][:100]}")

        if context.active_exceptions:
            lines.append("\n**Deterministic Exceptions / Anomalies:**")
            for exc in context.active_exceptions:
                lines.append(f"  - [{exc['exception_id']}] {exc['title']} ({exc['severity']}): {exc['evidence']}")

        return "\n".join(lines)
