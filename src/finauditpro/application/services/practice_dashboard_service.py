"""Application service for aggregating operational Practice Command Center data."""

from datetime import UTC, datetime

from finauditpro.application.dtos_dashboard import (
    ActiveClientSummaryDTO,
    AttentionItemDTO,
    ClientRequestStatusDTO,
    PracticeDashboardSummaryDTO,
    RecentActivityItemDTO,
    ReconciliationExceptionDTO,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import (
    ClientModel,
    DocumentModel,
    EngagementModel,
    FirmModel,
)


class PracticeDashboardService:
    """Service orchestrating aggregate metrics, attention items, PBC request tracking, and audit activity."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_practice_summary(self, firm_id: str | None = None) -> PracticeDashboardSummaryDTO:
        """Aggregates all operational dashboard statistics and attention items from database records."""
        with self.db_manager.session_scope() as session:
            firm = None
            if firm_id:
                firm = session.query(FirmModel).filter(FirmModel.id == firm_id).first()
            if not firm:
                firm = session.query(FirmModel).order_by(FirmModel.created_at.asc()).first()

            firm_name = firm.name if firm else "CA Practice"
            target_firm_id = firm.id if firm else None

            # Base query for clients
            clients_q = session.query(ClientModel)
            if target_firm_id:
                clients_q = clients_q.filter(ClientModel.firm_id == target_firm_id)
            clients = clients_q.all()
            total_clients = len(clients)

            # Base query for engagements
            engs_q = session.query(EngagementModel)
            if target_firm_id:
                engs_q = engs_q.filter(EngagementModel.firm_id == target_firm_id)
            engagements = engs_q.all()

            active_engagements = [
                e for e in engagements if str(e.status).lower() not in ("completed", "signed off", "archived")
            ]
            completed_audits = [
                e for e in engagements if str(e.status).lower() in ("completed", "signed off", "archived")
            ]

            client_map = {c.id: c for c in clients}

            # 1. Build Attention Items
            attention_items: list[AttentionItemDTO] = []

            # Check unclassified / draft uploaded documents needing review
            docs_q = session.query(DocumentModel)
            if engagements:
                eng_ids = [e.id for e in engagements]
                docs_q = docs_q.filter(DocumentModel.engagement_id.in_(eng_ids))
            else:
                docs_q = docs_q.filter(DocumentModel.id == "")
            unclassified_docs = docs_q.filter(DocumentModel.document_category == "Unclassified").all()

            if unclassified_docs:
                attention_items.append(
                    AttentionItemDTO(
                        id="att_unclassified_docs",
                        category="Documents Needing Review",
                        title=f"{len(unclassified_docs)} unclassified evidence document(s)",
                        description="Uploaded client documents require classification and review.",
                        count=len(unclassified_docs),
                        urgency="warning",
                        target_route="documents",
                    )
                )

            # Check PBC document request status via SQLite direct tables if available
            client_requests: list[ClientRequestStatusDTO] = []
            try:
                from finauditpro.infrastructure.persistence.pbc_and_query_models import (
                    ClientDocumentRequestModel,
                )

                pbc_reqs = session.query(ClientDocumentRequestModel).all()

                pbc_by_eng: dict[str, tuple[int, int]] = {}
                for req in pbc_reqs:
                    tot, rec = pbc_by_eng.get(req.engagement_id, (0, 0))
                    tot += 1
                    if str(req.status).lower() in ("received", "approved", "uploaded", "confirmed"):
                        rec += 1
                    pbc_by_eng[req.engagement_id] = (tot, rec)

                for eng in engagements:
                    if eng.id in pbc_by_eng:
                        tot, rec = pbc_by_eng[eng.id]
                        c = client_map.get(eng.client_id)
                        c_name = c.name if c else "Unknown Client"
                        pending = tot - rec
                        crs = ClientRequestStatusDTO(
                            client_id=eng.client_id,
                            client_name=c_name,
                            engagement_id=eng.id,
                            total_requested=tot,
                            total_received=rec,
                            pending_count=pending,
                        )
                        client_requests.append(crs)

                        if pending > 0:
                            attention_items.append(
                                AttentionItemDTO(
                                    id=f"att_pbc_{eng.id}",
                                    category="Pending Client Requests",
                                    title=f"{c_name}: {pending} PBC document(s) pending",
                                    description=f"{rec}/{tot} requested documents received from client.",
                                    count=pending,
                                    urgency="warning" if pending < 5 else "critical",
                                    target_route="pbc",
                                    target_id=eng.id,
                                )
                            )
            except Exception:
                pass

            # Check open audit findings & risks
            try:
                from finauditpro.infrastructure.persistence.core_audit_engine_models import (
                    FindingModel,
                    RiskModel,
                )

                open_findings = session.query(FindingModel).filter(FindingModel.status != "Closed").all()
                if open_findings:
                    attention_items.append(
                        AttentionItemDTO(
                            id="att_open_findings",
                            category="Open Audit Findings",
                            title=f"{len(open_findings)} un-resolved audit finding(s)",
                            description="Audit findings identified during testing require partner/manager review.",
                            count=len(open_findings),
                            urgency="critical",
                            target_route="audit_matrix",
                        )
                    )

                high_risks = session.query(RiskModel).filter(RiskModel.inherent_risk == "HIGH").all()
                if high_risks:
                    attention_items.append(
                        AttentionItemDTO(
                            id="att_high_risks",
                            category="High-Risk Exposure",
                            title=f"{len(high_risks)} high-risk audit area(s)",
                            description="Key audit matters requiring heightened substantive testing (SA 315).",
                            count=len(high_risks),
                            urgency="critical",
                            target_route="audit_matrix",
                        )
                    )
            except Exception:
                pass

            # Check working paper review notes
            try:
                from finauditpro.infrastructure.persistence.working_paper_models import (
                    ReviewNoteModel,
                )

                open_notes = session.query(ReviewNoteModel).filter(ReviewNoteModel.status == "Open").all()
                if open_notes:
                    attention_items.append(
                        AttentionItemDTO(
                            id="att_review_notes",
                            category="Open Review Notes",
                            title=f"{len(open_notes)} open review note(s)",
                            description="Audit review notes raised during manager/partner working paper review.",
                            count=len(open_notes),
                            urgency="warning",
                            target_route="working_papers",
                        )
                    )
            except Exception:
                pass

            # 2. Build Active Clients List
            active_clients: list[ActiveClientSummaryDTO] = []
            for client in clients:
                c_engs = [e for e in engagements if e.client_id == client.id]
                latest_eng = c_engs[0] if c_engs else None

                audit_t = (
                    latest_eng.audit_type if latest_eng else "Statutory Audit"
                )
                status = latest_eng.status if latest_eng else "No Engagement"
                fy = latest_eng.financial_year if latest_eng else "—"

                # Check PBCs & open findings for client
                pending_pbc = 0
                open_finds = 0
                risk_lvl = "Normal"

                if latest_eng:
                    try:
                        from finauditpro.infrastructure.persistence.core_audit_engine_models import (
                            FindingModel,
                            RiskModel,
                        )

                        open_finds = (
                            session.query(FindingModel)
                            .filter(FindingModel.engagement_id == latest_eng.id)
                            .filter(FindingModel.status != "Closed")
                            .count()
                        )
                        r_high = (
                            session.query(RiskModel)
                            .filter(RiskModel.engagement_id == latest_eng.id)
                            .filter(RiskModel.inherent_risk == "HIGH")
                            .count()
                        )
                        if r_high > 0:
                            risk_lvl = "High"
                    except Exception:
                        pass

                active_clients.append(
                    ActiveClientSummaryDTO(
                        client_id=client.id,
                        client_name=client.name,
                        industry=client.industry,
                        engagement_id=latest_eng.id if latest_eng else None,
                        financial_year=fy,
                        audit_type=str(audit_t),
                        status=str(status),
                        pending_pbc_count=pending_pbc,
                        open_findings_count=open_finds,
                        risk_level=risk_lvl,
                    )
                )

            # 3. Recent Audit Activities (from audit_events table)
            recent_activities: list[RecentActivityItemDTO] = []
            try:
                from finauditpro.infrastructure.persistence.models import AuditEventModel

                events = (
                    session.query(AuditEventModel)
                    .order_by(AuditEventModel.timestamp.desc())
                    .limit(10)
                    .all()
                )
                for ev in events:
                    dt = ev.timestamp if isinstance(ev.timestamp, datetime) else datetime.now(UTC)
                    recent_activities.append(
                        RecentActivityItemDTO(
                            id=ev.id,
                            event_type=ev.event_type,
                            description=ev.details_json or ev.event_type,
                            timestamp=dt,
                            user_name=ev.user_id or "Auditor",
                            entity_type=ev.entity_type,
                            entity_id=ev.entity_id,
                        )
                    )
            except Exception:
                pass

            # 4. Reconciliation Exceptions
            reconciliation_exceptions: list[ReconciliationExceptionDTO] = []
            # Aggregate GST 2B / GL exceptions if present
            try:
                from finauditpro.infrastructure.persistence.models import GSTEntryModel

                mismatches = (
                    session.query(GSTEntryModel)
                    .filter(GSTEntryModel.reconciliation_status == "MISMATCH")
                    .all()
                )
                if mismatches:
                    reconciliation_exceptions.append(
                        ReconciliationExceptionDTO(
                            id="gst_mismatches",
                            title="GSTR-2B vs General Ledger Mismatches",
                            category="GST Reconciliation",
                            mismatch_count=len(mismatches),
                            total_discrepancy_amount=float(
                                sum(abs(m.taxable_value - m.gstr2b_taxable_value) for m in mismatches)
                            ),
                            engagement_id=mismatches[0].engagement_id if mismatches else "",
                            client_name="Practice Clients",
                        )
                    )
            except Exception:
                pass

            return PracticeDashboardSummaryDTO(
                firm_id=target_firm_id,
                firm_name=firm_name,
                total_clients=total_clients,
                active_engagements=len(active_engagements),
                completed_audits=len(completed_audits),
                attention_items=attention_items,
                active_clients=active_clients,
                recent_activities=recent_activities,
                upcoming_deadlines=[],
                client_request_statuses=client_requests,
                reconciliation_exceptions=reconciliation_exceptions,
            )
