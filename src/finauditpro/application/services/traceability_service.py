"""Service constructing and traversing the 2-way Audit Traceability Graph."""

from typing import Any

from finauditpro.application.audit_planning_dtos import TraceabilityGraphDTO
from finauditpro.domain.audit_matrix_entities import AuditEvidence, AuditFinding, AuditProcedure, AuditRisk
from finauditpro.domain.working_paper_entities import WorkingPaper
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import AuditMatrixRepository
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import CoreAuditEngineRepository
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import WorkingPaperRepository


class TraceabilityService:
    """Service traversing graph connections across Findings, Procedures, Risks, Assertions, Evidence, and Working Papers."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_evidence_for_finding(self, engagement_id: str, finding_id: str) -> list[AuditEvidence]:
        """Navigate Finding -> Evidence."""
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_evidence_for_finding(finding_id)

    def get_findings_for_evidence(self, engagement_id: str, evidence_id: str) -> list[AuditFinding]:
        """Navigate Evidence -> Finding."""
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            ev = repo.get_evidence_by_id(evidence_id)
            if not ev or not ev.finding_id:
                return []
            f = repo.get_finding_by_id(ev.finding_id)
            return [f] if f and f.engagement_id == engagement_id else []

    def get_procedures_for_working_paper(self, engagement_id: str, working_paper_id: str) -> list[AuditProcedure]:
        """Navigate Working Paper -> Procedure."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            matrix_repo = AuditMatrixRepository(session)
            wp = wp_repo.get_by_id(working_paper_id)
            if not wp or wp.engagement_id != engagement_id:
                return []
            links = wp_repo.get_links(working_paper_id)
            target_ids = {l["target_id"] for l in links if l.get("target_type") in ("Procedure", "procedure")}
            all_procs = matrix_repo.list_procedures_for_engagement(engagement_id)
            # Match by explicit link or area matching
            result = []
            for p in all_procs:
                if p.id in target_ids or (wp.area and wp.area.lower() in p.account_area.lower()):
                    result.append(p)
            return result

    def get_working_papers_for_procedure(self, engagement_id: str, procedure_id: str) -> list[WorkingPaper]:
        """Navigate Procedure -> Working Paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            matrix_repo = AuditMatrixRepository(session)
            proc = matrix_repo.get_procedure_by_id(procedure_id)
            if not proc or proc.engagement_id != engagement_id:
                return []
            all_wps = wp_repo.list_for_engagement(engagement_id)
            matched = []
            for wp in all_wps:
                links = wp_repo.get_links(wp.id)
                target_ids = {l["target_id"] for l in links}
                if proc.id in target_ids or (wp.area and wp.area.lower() in proc.account_area.lower()):
                    matched.append(wp)
            return matched

    def get_risks_for_procedure(self, engagement_id: str, procedure_id: str) -> list[AuditRisk]:
        """Navigate Procedure -> Risk."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            proc = matrix_repo.get_procedure_by_id(procedure_id)
            if not proc or proc.engagement_id != engagement_id:
                return []
            risks = []
            for r_id in proc.linked_risk_ids:
                r = matrix_repo.get_risk_by_id(r_id)
                if r and r.engagement_id == engagement_id:
                    risks.append(r)
            return risks

    def get_procedures_for_risk(self, engagement_id: str, risk_id: str) -> list[AuditProcedure]:
        """Navigate Risk -> Procedure."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            all_procs = matrix_repo.list_procedures_for_engagement(engagement_id)
            return [p for p in all_procs if risk_id in p.linked_risk_ids]

    def get_working_papers_for_risk(self, engagement_id: str, risk_id: str) -> list[WorkingPaper]:
        """Navigate Risk -> Working Paper (via addressing procedures)."""
        procs = self.get_procedures_for_risk(engagement_id, risk_id)
        wps_dict = {}
        for p in procs:
            for wp in self.get_working_papers_for_procedure(engagement_id, p.id):
                wps_dict[wp.id] = wp
        return list(wps_dict.values())

    def get_risks_for_working_paper(self, engagement_id: str, working_paper_id: str) -> list[AuditRisk]:
        """Navigate Working Paper -> Risk (via addressing procedures)."""
        procs = self.get_procedures_for_working_paper(engagement_id, working_paper_id)
        risks_dict = {}
        for p in procs:
            for r in self.get_risks_for_procedure(engagement_id, p.id):
                risks_dict[r.id] = r
        return list(risks_dict.values())

    def get_evidence_for_procedure(self, engagement_id: str, procedure_id: str) -> list[AuditEvidence]:
        """Navigate Procedure -> Evidence."""
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_evidence_for_procedure(procedure_id)

    def get_evidence_for_working_paper(self, engagement_id: str, working_paper_id: str) -> list[AuditEvidence]:
        """Navigate Working Paper -> Evidence."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            matrix_repo = AuditMatrixRepository(session)
            links = wp_repo.get_links(working_paper_id)
            ev_ids = {l["target_id"] for l in links if l.get("target_type") in ("Evidence", "EVIDENCE", "evidence")}
            all_ev = matrix_repo.list_evidence_for_engagement(engagement_id)
            return [e for e in all_ev if e.id in ev_ids or e.working_paper_id == working_paper_id]

    def get_evidence_for_sample(self, engagement_id: str, sample_ref: str) -> list[AuditEvidence]:
        """Navigate Sample -> Evidence."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            all_ev = matrix_repo.list_evidence_for_engagement(engagement_id)
            return [e for e in all_ev if e.sample_ref == sample_ref]

    def get_working_papers_for_evidence(self, engagement_id: str, evidence_id: str) -> list[WorkingPaper]:
        """Navigate Evidence -> Working Paper."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            wp_repo = WorkingPaperRepository(session)
            ev = matrix_repo.get_evidence_by_id(evidence_id)
            if not ev or not ev.working_paper_id:
                return []
            wp = wp_repo.get_by_id(ev.working_paper_id)
            return [wp] if wp and wp.engagement_id == engagement_id else []

    def get_procedures_for_evidence(self, engagement_id: str, evidence_id: str) -> list[AuditProcedure]:
        """Navigate Evidence -> Procedure."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            ev = matrix_repo.get_evidence_by_id(evidence_id)
            if not ev or not ev.procedure_id:
                return []
            proc = matrix_repo.get_procedure_by_id(ev.procedure_id)
            return [proc] if proc and proc.engagement_id == engagement_id else []

    def build_finding_traceability(self, engagement_id: str, finding_id: str) -> TraceabilityGraphDTO:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            finding = matrix_repo.get_finding_by_id(finding_id)
            if not finding or finding.engagement_id != engagement_id:
                return TraceabilityGraphDTO(engagement_id=engagement_id, finding_id=finding_id)

            nodes: list[dict[str, Any]] = []
            edges: list[dict[str, Any]] = []
            visited_nodes: set[str] = set()

            # 1. Finding Node
            finding_node_id = f"finding_{finding.id}"
            nodes.append({
                "id": finding_node_id,
                "type": "Finding",
                "label": finding.title,
                "status": finding.status.value,
                "severity": finding.severity.value,
                "source": finding.source.value if hasattr(finding.source, "value") else str(finding.source),
            })
            visited_nodes.add(finding_node_id)

            # 2. Linked Evidence
            for ev in matrix_repo.list_evidence_for_finding(finding.id):
                ev_type = "DocumentPage" if (ev.document_id or ev.page_number is not None) else "FinancialRow"
                ev_node_id = f"evidence_{ev.id}"
                nodes.append({
                    "id": ev_node_id,
                    "type": ev_type,
                    "label": ev.title,
                    "document_id": ev.document_id,
                    "page_number": ev.page_number,
                    "dataset_id": ev.dataset_id,
                    "row_index": ev.row_index,
                })
                edges.append({"source": finding_node_id, "target": ev_node_id, "relation": "HAS_EVIDENCE"})

            # 3. Linked Procedure & Assertions & Risks
            proc = matrix_repo.get_procedure_by_id(finding.procedure_id) if finding.procedure_id else None
            if proc:
                proc_node_id = f"procedure_{proc.id}"
                if proc_node_id not in visited_nodes:
                    nodes.append({
                        "id": proc_node_id,
                        "type": "Procedure",
                        "label": f"[{proc.procedure_code}] {proc.objective}",
                        "status": proc.status.value,
                    })
                    visited_nodes.add(proc_node_id)
                edges.append({"source": finding_node_id, "target": proc_node_id, "relation": "RAISED_BY_PROCEDURE"})

                for ass in proc.assertions:
                    ass_node_id = f"assertion_{ass.value}"
                    if ass_node_id not in visited_nodes:
                        nodes.append({"id": ass_node_id, "type": "Assertion", "label": ass.value})
                        visited_nodes.add(ass_node_id)
                    edges.append({"source": proc_node_id, "target": ass_node_id, "relation": "TESTS_ASSERTION"})

                for risk_id in proc.linked_risk_ids:
                    risk = matrix_repo.get_risk_by_id(risk_id)
                    if risk:
                        risk_node_id = f"risk_{risk.id}"
                        if risk_node_id not in visited_nodes:
                            nodes.append({
                                "id": risk_node_id,
                                "type": "Risk",
                                "label": f"[{risk.risk_code}] {risk.title}",
                                "romm": risk.derived_romm.value,
                            })
                            visited_nodes.add(risk_node_id)
                        edges.append({"source": proc_node_id, "target": risk_node_id, "relation": "RESPONDS_TO_RISK"})

            # 4. Linked Working Papers
            wp_repo = WorkingPaperRepository(session)
            for wp in wp_repo.list_for_engagement(engagement_id):
                links = wp_repo.get_links(wp.id)
                target_ids = {l["target_id"] for l in links}
                if (finding.id in target_ids) or (proc and proc.id in target_ids):
                    wp_node_id = f"working_paper_{wp.id}"
                    if wp_node_id not in visited_nodes:
                        nodes.append({
                            "id": wp_node_id,
                            "type": "WorkingPaper",
                            "label": f"[{wp.index_reference}] {wp.title}",
                            "status": wp.status.value,
                        })
                        visited_nodes.add(wp_node_id)
                    edges.append({"source": wp_node_id, "target": finding_node_id, "relation": "DOCUMENTS_FINDING"})

            # 5. Direct Risk link
            if finding.risk_id:
                risk = matrix_repo.get_risk_by_id(finding.risk_id)
                if risk:
                    risk_node_id = f"risk_{risk.id}"
                    if risk_node_id not in visited_nodes:
                        nodes.append({
                            "id": risk_node_id,
                            "type": "Risk",
                            "label": f"[{risk.risk_code}] {risk.title}",
                            "romm": risk.derived_romm.value,
                        })
                        visited_nodes.add(risk_node_id)
                    edges.append({"source": finding_node_id, "target": risk_node_id, "relation": "LINKED_TO_RISK"})

            # 6. Misstatements & AJE
            core_repo = CoreAuditEngineRepository(session)
            for misst in core_repo.list_misstatements_for_engagement(engagement_id):
                if misst.exception_id == finding.id or misst.procedure_id == (proc.id if proc else None):
                    m_node_id = f"misstatement_{misst.id}"
                    if m_node_id not in visited_nodes:
                        nodes.append({
                            "id": m_node_id,
                            "type": "Misstatement",
                            "label": f"[{misst.account_code}] ₹{misst.amount_paise / 100:,.2f} ({misst.status.value})",
                            "amount_paise": misst.amount_paise,
                        })
                        visited_nodes.add(m_node_id)
                    edges.append({"source": finding_node_id, "target": m_node_id, "relation": "QUANTIFIED_AS_MISSTATEMENT"})

                    if misst.linked_aje_number:
                        aje_node_id = f"aje_{misst.linked_aje_id or misst.linked_aje_number}"
                        if aje_node_id not in visited_nodes:
                            nodes.append({
                                "id": aje_node_id,
                                "type": "AJE",
                                "label": f"Adjustment [{misst.linked_aje_number}]",
                            })
                            visited_nodes.add(aje_node_id)
                        edges.append({"source": m_node_id, "target": aje_node_id, "relation": "CORRECTED_BY_AJE"})

            return TraceabilityGraphDTO(
                engagement_id=engagement_id,
                finding_id=finding_id,
                nodes=nodes,
                edges=edges,
            )
