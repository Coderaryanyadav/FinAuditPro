"""Service constructing and traversing the 2-way Audit Traceability Graph."""

from typing import Any

from finauditpro.application.audit_planning_dtos import TraceabilityGraphDTO
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)


class TraceabilityService:
    """Service traversing graph connections across Findings, Procedures, Risks, Assertions, and Evidence."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

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
            evidences = matrix_repo.list_evidence_for_finding(finding.id)
            for ev in evidences:
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
                edges.append({
                    "source": finding_node_id,
                    "target": ev_node_id,
                    "relation": "HAS_EVIDENCE",
                })

            # 3. Linked Procedure
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

                edges.append({
                    "source": finding_node_id,
                    "target": proc_node_id,
                    "relation": "RAISED_BY_PROCEDURE",
                })

                # 4. Procedure Assertions
                for ass in proc.assertions:
                    ass_node_id = f"assertion_{ass.value}"
                    if ass_node_id not in visited_nodes:
                        nodes.append({
                            "id": ass_node_id,
                            "type": "Assertion",
                            "label": ass.value,
                        })
                        visited_nodes.add(ass_node_id)
                    edges.append({
                        "source": proc_node_id,
                        "target": ass_node_id,
                        "relation": "TESTS_ASSERTION",
                    })

                # 5. Linked Risks
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

                        edges.append({
                            "source": proc_node_id,
                            "target": risk_node_id,
                            "relation": "RESPONDS_TO_RISK",
                        })

                        # Risk Assertions
                        for r_ass in risk.assertions:
                            r_ass_id = f"assertion_{r_ass.value}"
                            if r_ass_id not in visited_nodes:
                                nodes.append({
                                    "id": r_ass_id,
                                    "type": "Assertion",
                                    "label": r_ass.value,
                                })
                                visited_nodes.add(r_ass_id)
                            edges.append({
                                "source": risk_node_id,
                                "target": r_ass_id,
                                "relation": "ADDRESSES_ASSERTION",
                            })

            # 6. Linked Working Papers
            from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
                WorkingPaperRepository,
            )
            wp_repo = WorkingPaperRepository(session)
            all_wps = wp_repo.list_for_engagement(engagement_id)
            for wp in all_wps:
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
                    edges.append({
                        "source": wp_node_id,
                        "target": finding_node_id,
                        "relation": "DOCUMENTS_FINDING",
                    })

            # 7. Direct Risk link (if finding linked directly to a risk)
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
                    edges.append({
                        "source": finding_node_id,
                        "target": risk_node_id,
                        "relation": "LINKED_TO_RISK",
                    })

            return TraceabilityGraphDTO(
                engagement_id=engagement_id,
                finding_id=finding_id,
                nodes=nodes,
                edges=edges,
            )
