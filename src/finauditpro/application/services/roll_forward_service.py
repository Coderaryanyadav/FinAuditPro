"""Application service managing multi-year audit roll-forward, SA 510 opening balance tie-out, and carried findings provenance."""

import hashlib
import json

from finauditpro.application.dtos import CreateEngagementDTO
from finauditpro.application.roll_forward_dtos import ConfirmTieOutDTO, ExecuteRollForwardDTO
from finauditpro.application.services.engagement_service import EngagementService
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
    CarriedItemDecisionEnum,
    OpeningBalanceLink,
    RollForwardRecord,
    TieOutSummary,
    calculate_opening_tie_out,
)
from finauditpro.domain.working_paper_entities import (
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    DocumentRepository,
    EngagementRepository,
    FinancialDataRepository,
    RollForwardRepository,
    WorkingPaperRepository,
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

        decisions_map: dict[str, str] = {}
        for cat, default_flag in [
            ("client_information", True),
            ("permanent_file", dto.carry_permanent_documents),
            ("audit_program", dto.carry_procedures),
            ("working_paper_structure", True),
            ("prior_year_findings", dto.carry_findings),
            ("account_mappings", dto.link_opening_balances),
            ("risk_templates", dto.carry_risk_register),
            ("methodology_references", dto.carry_materiality_methodology),
        ]:
            if dto.category_decisions and cat in dto.category_decisions:
                dec = dto.category_decisions[cat]
                decisions_map[cat] = dec.value if hasattr(dec, "value") else str(dec).upper()
            else:
                decisions_map[cat] = CarriedItemDecisionEnum.KEEP.value if default_flag else CarriedItemDecisionEnum.REMOVE.value

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            target_eng = eng_repo.get_by_id(new_eng.id)
            if target_eng:
                target_eng.prior_engagement_id = dto.source_engagement_id
                eng_repo.update(target_eng)

            matrix_repo = AuditMatrixRepository(session)
            rf_repo = RollForwardRepository(session)
            wp_repo = WorkingPaperRepository(session)

            # 1. Client Information
            if decisions_map.get("client_information") in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
                items_carried.append("Client Information & KYC Baseline")

            # 2. Permanent File Documents
            perm_dec = decisions_map.get("permanent_file", CarriedItemDecisionEnum.KEEP.value)
            if perm_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
                doc_repo = DocumentRepository(session)
                docs = doc_repo.list_by_engagement(dto.source_engagement_id)
                perm_docs = [
                    d for d in docs
                    if "PERMANENT" in d.document_category.value.upper() or d.document_category.value == "General"
                ]
                if perm_docs:
                    items_carried.append(f"{len(perm_docs)} Permanent File Document Reference(s)")

            # 3. Risk Templates / Register (Reset to Draft / Medium ROMM)
            risk_dec = decisions_map.get("risk_templates", CarriedItemDecisionEnum.KEEP.value)
            if risk_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
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

            # 4. Materiality & Methodology References
            meth_dec = decisions_map.get("methodology_references", CarriedItemDecisionEnum.KEEP.value)
            if meth_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
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

            # 5. Audit Program / Procedures (Status reset to NOT_STARTED, conclusions empty)
            proc_dec = decisions_map.get("audit_program", CarriedItemDecisionEnum.KEEP.value)
            if proc_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
                source_procs = matrix_repo.list_procedures_for_engagement(dto.source_engagement_id)
                for p in source_procs:
                    draft_proc = AuditProcedure(
                        engagement_id=new_eng.id,
                        procedure_code=p.procedure_code,
                        objective=f"{p.objective} (carried from FY {source_eng.financial_year})" if proc_dec == CarriedItemDecisionEnum.KEEP.value else f"{p.objective} (Updated for FY {dto.target_financial_year})",
                        procedure_type=p.procedure_type,
                        instructions=p.instructions,
                        evidence_requirement=p.evidence_requirement,
                        status=ProcedureStatusEnum.NOT_STARTED,
                        assertions=p.assertions,
                    )
                    matrix_repo.add_procedure(draft_proc)
                if source_procs:
                    items_carried.append(f"{len(source_procs)} Audit Procedure Template(s)")

            # 6. Working Paper Structure (Reset to DRAFT, conclusion cleared, unlocked)
            wp_dec = decisions_map.get("working_paper_structure", CarriedItemDecisionEnum.KEEP.value)
            if wp_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
                source_wps = wp_repo.list_for_engagement(dto.source_engagement_id)
                for wp in source_wps:
                    new_wp = WorkingPaper(
                        engagement_id=new_eng.id,
                        index_reference=wp.index_reference,
                        title=wp.title if wp_dec == CarriedItemDecisionEnum.KEEP.value else f"{wp.title} (FY {dto.target_financial_year})",
                        area=wp.area,
                        file_category=wp.file_category,
                        status=WorkingPaperStatusEnum.DRAFT,
                        conclusion="",
                        preparer_id=dto.performed_by,
                        reviewer_id=None,
                        content_hash=None,
                        version=1,
                        is_locked=False,
                    )
                    saved_wp = wp_repo.add_working_paper(new_wp)
                    sections = wp_repo.get_sections(wp.id)
                    for s in sections:
                        new_sec = WorkingPaperSection(
                            working_paper_id=saved_wp.id,
                            section_order=s.section_order,
                            title=s.title,
                            content_markdown="",
                        )
                        wp_repo.add_section(new_sec)
                if source_wps:
                    items_carried.append(f"{len(source_wps)} Working Paper Structure(s)")

            # 7. Prior-Year Findings (Open/Under-Review Carried Forward)
            find_dec = decisions_map.get("prior_year_findings", CarriedItemDecisionEnum.KEEP.value)
            if find_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
                source_findings = matrix_repo.list_findings_for_engagement(dto.source_engagement_id)
                carried = [
                    f for f in source_findings
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

            # 8. Account Mappings & SA 510 Opening Balances
            map_dec = decisions_map.get("account_mappings", CarriedItemDecisionEnum.KEEP.value)
            if map_dec in (CarriedItemDecisionEnum.KEEP.value, CarriedItemDecisionEnum.UPDATE.value):
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

            # Compute SHA-256 Content Hash for Complete Roll-Forward Audit History
            items_omitted = [
                "Current-Year Evidence",
                "Current-Year Conclusions",
                "Current-Year Testing",
                "Current-Year Management Representations",
            ]
            hash_payload = (
                f"{new_eng.id}:{dto.source_engagement_id}:{source_eng.financial_year}:"
                f"{dto.target_financial_year}:{json.dumps(decisions_map, sort_keys=True)}:"
                f"{','.join(sorted(items_carried))}:{dto.performed_by}"
            )
            rf_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

            # Record RollForwardRecord
            record = RollForwardRecord(
                new_engagement_id=new_eng.id,
                source_engagement_id=dto.source_engagement_id,
                source_fy=source_eng.financial_year,
                target_fy=dto.target_financial_year,
                decisions=decisions_map,
                items_carried=items_carried,
                items_omitted=items_omitted,
                content_hash=rf_hash,
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
                    details=(
                        f"Rolled forward from FY {source_eng.financial_year} into FY {dto.target_financial_year}. "
                        f"Carried: {len(items_carried)} categories. Omitted: {len(items_omitted)} current-year dynamic items. "
                        f"Hash: {rf_hash[:12]}..."
                    ),
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
