"""Application service managing multi-year audit roll-forward, SA 510 opening balance tie-out, and carried findings provenance."""

from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO, ExecuteRollForwardDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.domain.audit_matrix_entities import (
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    FindingStatusEnum,
    MaterialityAssessment,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent, Engagement
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.domain.roll_forward_entities import (
    OpeningBalanceLink,
    RollForwardRecord,
    TieOutSummary,
    calculate_opening_tie_out,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    DocumentRepository,
    EngagementRepository,
    FinancialDataRepository,
    RollForwardRepository,
)


class RollForwardService:
    """Service orchestrating multi-year engagement roll-forwards, SA 510 balance tie-outs, and carried finding provenance."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.engagement_service = EngagementService(db_manager)

    def roll_forward_engagement(self, dto: ExecuteRollForwardDTO) -> Engagement:
        """Create new engagement for next FY for same client, rolling forward re-usable planning drafts & carried findings."""
        items_carried: list[str] = []

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            source_eng = eng_repo.get_by_id(dto.source_engagement_id)
            if not source_eng:
                raise EntityNotFoundError("Source Engagement", dto.source_engagement_id)

            if source_eng.status.value not in ("Archived", "Completed"):
                raise ValidationError(
                    "Roll-forward can only be executed from a closed or archived prior-year engagement."
                )

        # Create New Engagement for Next FY for SAME CLIENT
        new_eng = self.engagement_service.create_engagement(
            CreateEngagementDTO(
                firm_id=source_eng.firm_id,
                client_id=source_eng.client_id,
                financial_year=dto.target_financial_year,
            )
        )

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            target_eng = eng_repo.get_by_id(new_eng.id)
            if target_eng:
                target_eng.prior_engagement_id = dto.source_engagement_id
                eng_repo.update(target_eng)

            matrix_repo = AuditMatrixRepository(session)
            rf_repo = RollForwardRepository(session)

            # 1. Carry Permanent File Documents
            if dto.carry_permanent_documents:
                doc_repo = DocumentRepository(session)
                docs = doc_repo.list_by_engagement(dto.source_engagement_id)
                perm_docs = [
                    d
                    for d in docs
                    if "PERMANENT" in d.document_category.value.upper()
                    or d.document_category.value == "General"
                ]
                if perm_docs:
                    items_carried.append(f"{len(perm_docs)} Permanent File Document Reference(s)")

            # 2. Carry Risk Register as Drafts (Ratings Reset to UNASSESSED)
            if dto.carry_risk_register:
                source_risks = matrix_repo.list_risks_for_engagement(dto.source_engagement_id)
                for r in source_risks:
                    draft_risk = AuditRisk(
                        engagement_id=new_eng.id,
                        risk_code=r.risk_code,
                        title=f"{r.title} (carried from FY {source_eng.financial_year} — review)",
                        category=r.category,
                        description=f"Carried from FY {source_eng.financial_year}. Original description: {r.description}",
                        assertions=r.assertions,
                        inherent_risk=RiskSeverityEnum.MEDIUM,
                        control_risk=RiskSeverityEnum.MEDIUM,
                        derived_romm=RiskSeverityEnum.MEDIUM,
                        is_significant_risk=r.is_significant_risk,
                        risk_response=r.risk_response,
                    )
                    matrix_repo.add_risk(draft_risk)
                if source_risks:
                    items_carried.append(f"{len(source_risks)} Draft Risk Register Entry(ies)")

            # 3. Carry Materiality Methodology (Method only, amounts zeroed for re-computation)
            if dto.carry_materiality_methodology:
                source_mat = matrix_repo.get_latest_materiality(dto.source_engagement_id)
                if source_mat:
                    draft_mat = MaterialityAssessment(
                        engagement_id=new_eng.id,
                        benchmark_type=source_mat.benchmark_type,
                        benchmark_amount_paise=0,
                        benchmark_source=f"Carried methodology from FY {source_eng.financial_year} — pending current-year financial import",
                        overall_percentage=source_mat.overall_percentage,
                        overall_materiality_paise=0,
                        performance_percentage=source_mat.performance_percentage,
                        performance_materiality_paise=0,
                        trivial_percentage=source_mat.trivial_percentage,
                        clearly_trivial_threshold_paise=0,
                        methodology_notes=f"Methodology carried from FY {source_eng.financial_year}: {source_mat.methodology_notes}",
                        created_by=dto.performed_by,
                        is_verified_statutory=False,
                    )
                    matrix_repo.add_materiality(draft_mat)
                    items_carried.append("Materiality Benchmark Methodology")

            # 4. Carry Audit Procedures
            if dto.carry_procedures:
                source_procs = matrix_repo.list_procedures_for_engagement(dto.source_engagement_id)
                for p in source_procs:
                    draft_proc = AuditProcedure(
                        engagement_id=new_eng.id,
                        procedure_code=p.procedure_code,
                        objective=f"{p.objective} (carried from FY {source_eng.financial_year})",
                        procedure_type=p.procedure_type,
                        instructions=p.instructions,
                        evidence_requirement=p.evidence_requirement,
                        status=ProcedureStatusEnum.PLANNED,
                        assertions=p.assertions,
                    )
                    matrix_repo.add_procedure(draft_proc)
                if source_procs:
                    items_carried.append(f"{len(source_procs)} Audit Procedure Template(s)")

            # 5. Carry Open / Carried Findings (Preserving M5 AI Badges & Citations)
            if dto.carry_findings:
                source_findings = matrix_repo.list_findings_for_engagement(dto.source_engagement_id)
                carried = [
                    f
                    for f in source_findings
                    if f.status in (FindingStatusEnum.OPEN, FindingStatusEnum.UNDER_REVIEW)
                ]
                for f in carried:
                    carried_finding = AuditFinding(
                        engagement_id=new_eng.id,
                        procedure_id=None,
                        risk_id=None,
                        title=f"{f.title} (carried from FY {source_eng.financial_year})",
                        description=f"Carried-forward finding from FY {source_eng.financial_year}. {f.description}",
                        severity=f.severity,
                        status=FindingStatusEnum.OPEN,
                        amount_paise=f.amount_paise,
                        source=f.source,
                        is_ai_generated=f.is_ai_generated,
                        prior_engagement_finding_id=f.id,
                    )
                    matrix_repo.add_finding(carried_finding)
                if carried:
                    items_carried.append(f"{len(carried)} Carried-Forward Audit Finding(s)")

            # 6. Link SA 510 Opening Balances to Prior Audited Closing Balances
            if dto.link_opening_balances:
                fin_repo = FinancialDataRepository(session)
                datasets = fin_repo.get_datasets_by_engagement(dto.source_engagement_id)
                links: list[OpeningBalanceLink] = []
                for ds in datasets:
                    lines = fin_repo.get_trial_balance_lines(ds.id)
                    for line in lines:
                        links.append(
                            OpeningBalanceLink(
                                engagement_id=new_eng.id,
                                source_engagement_id=dto.source_engagement_id,
                                account_code=line.account_code or "ACC-UNK",
                                account_name=line.account_name or "Account",
                                opening_dr_paise=line.closing_dr_paise,
                                opening_cr_paise=line.closing_cr_paise,
                                prior_closing_dr_paise=line.closing_dr_paise,
                                prior_closing_cr_paise=line.closing_cr_paise,
                                is_tied_out=True,
                                is_verified_by_auditor=False,
                            )
                        )

                if links:
                    rf_repo.add_opening_balance_links(links)
                    items_carried.append(f"{len(links)} SA 510 Opening Balance Link(s)")

            # Record RollForwardRecord
            record = RollForwardRecord(
                new_engagement_id=new_eng.id,
                source_engagement_id=dto.source_engagement_id,
                source_fy=source_eng.financial_year,
                items_carried=items_carried,
                performed_by=dto.performed_by,
            )
            rf_repo.add_roll_forward_record(record)

            # Record Audit Event
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=new_eng.id,
                    actor=dto.performed_by,
                    action="Engagement Rolled Forward",
                    details=f"Rolled forward from FY {source_eng.financial_year} into FY {dto.target_financial_year}. Items carried: {', '.join(items_carried)}",
                )
            )

        return new_eng

    def get_opening_balance_tie_out(
        self, engagement_id: str
    ) -> tuple[TieOutSummary, list[OpeningBalanceLink]]:
        """Fetch opening balance links and compute SA 510 tie-out summary."""
        with self.db_manager.session_scope() as session:
            repo = RollForwardRepository(session)
            links = repo.list_opening_balance_links(engagement_id)
            summary = calculate_opening_tie_out(links)
            return summary, links

    def confirm_opening_balance_tie_out(self, dto: ConfirmTieOutDTO) -> TieOutSummary:
        """Auditor confirmation of SA 510 opening balance tie-out."""
        with self.db_manager.session_scope() as session:
            repo = RollForwardRepository(session)
            now_str = utc_now().isoformat()
            repo.confirm_opening_balance_tie_out(dto.engagement_id, dto.auditor_name, now_str)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.auditor_name,
                    action="SA 510 Opening Balances Confirmed",
                    details=f"Auditor '{dto.auditor_name}' confirmed SA 510 opening balance tie-out.",
                )
            )

            links = repo.list_opening_balance_links(dto.engagement_id)
            return calculate_opening_tie_out(links)
