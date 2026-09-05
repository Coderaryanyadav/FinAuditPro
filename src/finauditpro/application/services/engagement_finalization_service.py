from typing import Any

from finauditpro.application.completion_dtos import (
    ChecklistItemDTO,
    FinalizationBlockerDTO,
    FinalizationGateResultDTO,
    OpenItemDTO,
    OpenItemsRegisterDTO,
    PartnerSignoffDTO,
    RelatedPartyCompletionDTO,
    SA240CompletionDTO,
    UpdateChecklistItemDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.domain.audit_completion_entities import (
    FinancialMisstatement,
    MisstatementStatusEnum,
    MisstatementTypeEnum,
)
from finauditpro.domain.completion_checklist_entities import (
    ChecklistCategoryEnum,
    CompletionChecklistItem,
    CompletionStatusEnum,
    RelatedPartyCompletionRecord,
    SA240CompletionRecord,
)
from finauditpro.domain.entities import EngagementStatusEnum
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.finalization_gate_engine import FinalizationGateEngine
from finauditpro.domain.financial_statement_entities import PackageStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    EngagementRepository,
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.completion_checklist_repository import (
    CompletionChecklistRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import (
    ComplianceRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)


class EngagementFinalizationService:
    """Orchestrates checklist verification, open-items scanning, finalization gates, and partner approval."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_completion_checklist(self, engagement_id: str) -> list[ChecklistItemDTO]:
        with self.db_manager.session_scope() as session:
            repo = CompletionChecklistRepository(session)
            items = repo.list_checklist_items(engagement_id)
            if not items:
                items = self._initialize_default_checklist(session, engagement_id)
            return [self._to_checklist_dto(i) for i in items]

    def update_checklist_item(self, dto: UpdateChecklistItemDTO) -> ChecklistItemDTO:
        with self.db_manager.session_scope() as session:
            repo = CompletionChecklistRepository(session)
            item = repo.get_checklist_item(dto.item_id)
            if not item or item.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("CompletionChecklistItem", dto.item_id)

            status_enum = next(
                (s for s in CompletionStatusEnum if s.value.lower() == dto.status.lower() or s.name.lower() == dto.status.lower()),
                CompletionStatusEnum.NOT_STARTED,
            )
            updated = CompletionChecklistItem(
                id=item.id,
                engagement_id=item.engagement_id,
                category=item.category,
                title=item.title,
                description=item.description,
                is_applicable=dto.is_applicable if dto.is_applicable is not None else item.is_applicable,
                status=status_enum,
                supporting_ref=dto.supporting_ref or item.supporting_ref,
                reviewer=dto.reviewer or SecurityContext.get_current_username(),
                notes=dto.notes or item.notes,
            )
            saved = repo.save_checklist_item(updated)
            return self._to_checklist_dto(saved)

    def evaluate_finalization_gate(self, engagement_id: str) -> FinalizationGateResultDTO:
        with self.db_manager.session_scope() as session:
            gate_res, _ = self._evaluate_gate_internal(session, engagement_id)
            return FinalizationGateResultDTO(
                engagement_id=engagement_id,
                is_finalizable=gate_res.is_finalizable,
                blockers=[
                    FinalizationBlockerDTO(
                        category=b.category,
                        reason=b.reason,
                        source_ref=b.source_ref,
                        action_required=b.action_required,
                        severity=getattr(b.severity, "value", str(b.severity)),
                    )
                    for b in gate_res.blockers
                ],
                warnings=gate_res.warnings,
                total_open_items=gate_res.total_open_items,
                critical_items_count=gate_res.critical_items_count,
            )

    def get_open_items_register(self, engagement_id: str) -> OpenItemsRegisterDTO:
        with self.db_manager.session_scope() as session:
            _, open_reg = self._evaluate_gate_internal(session, engagement_id)
            return open_reg

    def partner_signoff_and_finalize(self, dto: PartnerSignoffDTO) -> dict[str, Any]:
        session_user = SecurityContext.get_current_session()
        if not session_user:
            raise PermissionDeniedError("Authentication required for partner sign-off.")

        user_role_str = getattr(session_user.role, "value", str(session_user.role))
        if user_role_str not in ("Partner", RoleEnum.PARTNER.value):
            raise PermissionDeniedError(f"Partner Authorization Required: User role '{user_role_str}' cannot perform final engagement sign-off.")

        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            eng = eng_repo.get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)
            if eng.status in (EngagementStatusEnum.COMPLETED, EngagementStatusEnum.ARCHIVED):
                raise ValidationError(f"Engagement '{eng.id}' is already finalized and locked.")

            gate_res, _ = self._evaluate_gate_internal(session, dto.engagement_id)
            if not gate_res.is_finalizable:
                reasons = "; ".join(f"[{b.category}] {b.reason}" for b in gate_res.blockers)
                raise ValidationError(f"CANNOT FINALIZE: Mandatory blocking conditions exist: {reasons}")

            eng.status = EngagementStatusEnum.COMPLETED
            eng_repo.update(eng)

            fs_repo = FinancialStatementRepository(session)
            pkg = fs_repo.get_latest_package(dto.engagement_id)
            if pkg:
                pkg.is_locked, pkg.status, pkg.approved_by = True, PackageStatusEnum.LOCKED, session_user.username
                fs_repo.update_package(pkg)

            wp_repo = WorkingPaperRepository(session)
            for wp in wp_repo.list_for_engagement(dto.engagement_id):
                wp.is_locked = True
                wp_repo.update_working_paper(wp)

            return {
                "engagement_id": eng.id, "status": eng.status.value, "finalized_by": session_user.username,
                "partner_role": user_role_str, "audit_opinion_type": dto.audit_opinion_type, "is_locked": True, "signoff_notes": dto.signoff_notes,
            }

    def record_related_party_completion(self, dto: RelatedPartyCompletionDTO) -> RelatedPartyCompletionDTO:
        with self.db_manager.session_scope() as session:
            repo = CompletionChecklistRepository(session)
            record = RelatedPartyCompletionRecord(
                engagement_id=dto.engagement_id, register_reviewed=dto.register_reviewed,
                undisclosed_transactions_identified=dto.undisclosed_transactions_identified,
                arms_length_verified=dto.arms_length_verified, schedule_iii_disclosed=dto.schedule_iii_disclosed,
                auditor_conclusion=dto.auditor_conclusion, reviewer=dto.reviewer or SecurityContext.get_current_username(), is_completed=True,
            )
            repo.save_related_party_completion(record)
            return dto

    def get_related_party_completion(self, engagement_id: str) -> RelatedPartyCompletionDTO | None:
        with self.db_manager.session_scope() as session:
            r = CompletionChecklistRepository(session).get_related_party_completion(engagement_id)
            if not r:
                return None
            return RelatedPartyCompletionDTO(
                engagement_id=r.engagement_id, register_reviewed=r.register_reviewed,
                undisclosed_transactions_identified=r.undisclosed_transactions_identified,
                arms_length_verified=r.arms_length_verified, schedule_iii_disclosed=r.schedule_iii_disclosed,
                auditor_conclusion=r.auditor_conclusion, reviewer=r.reviewer,
            )

    def record_sa240_completion(self, dto: SA240CompletionDTO) -> SA240CompletionDTO:
        with self.db_manager.session_scope() as session:
            repo = CompletionChecklistRepository(session)
            record = SA240CompletionRecord(
                engagement_id=dto.engagement_id, management_override_tested=dto.management_override_tested,
                journal_entry_testing_completed=dto.journal_entry_testing_completed,
                revenue_recognition_presumption_addressed=dto.revenue_recognition_presumption_addressed,
                risk_indicators_identified=getattr(dto, "risk_indicators_identified", False),
                auditor_conclusion=dto.auditor_conclusion, reviewer=dto.reviewer or SecurityContext.get_current_username(), is_completed=True,
            )
            repo.save_sa240_completion(record)
            return dto

    record_fraud_completion = record_sa240_completion  # ignore

    def get_sa240_completion(self, engagement_id: str) -> SA240CompletionDTO | None:
        with self.db_manager.session_scope() as session:
            f = CompletionChecklistRepository(session).get_sa240_completion(engagement_id)
            if not f:
                return None
            return SA240CompletionDTO(
                engagement_id=f.engagement_id, management_override_tested=f.management_override_tested,
                journal_entry_testing_completed=f.journal_entry_testing_completed,
                revenue_recognition_presumption_addressed=f.revenue_recognition_presumption_addressed,
                risk_indicators_identified=f.risk_indicators_identified,
                auditor_conclusion=f.auditor_conclusion, reviewer=f.reviewer,
            )

    get_fraud_completion = get_sa240_completion  # ignore

    def _evaluate_gate_internal(
        self, session: Any, engagement_id: str
    ) -> tuple[Any, OpenItemsRegisterDTO]:
        wp_repo = WorkingPaperRepository(session)
        wps = wp_repo.list_for_engagement(engagement_id)
        all_review_notes = []
        for wp in wps:
            all_review_notes.extend(wp_repo.list_review_notes(wp.id))

        core_repo = CoreAuditEngineRepository(session)
        exceptions = core_repo.list_exceptions_for_engagement(engagement_id)
        misstatements = core_repo.list_misstatements_for_engagement(engagement_id)

        mat_repo = AuditMatrixRepository(session)
        mat = mat_repo.get_materiality(engagement_id)
        overall_mat = mat.overall_materiality_paise if mat else 0
        perf_mat = mat.performance_materiality_paise if mat else 0
        trivial_mat = mat.clearly_trivial_threshold_paise if mat else 0

        converted_m = [
            FinancialMisstatement(
                id=m.id,
                engagement_id=m.engagement_id,
                misstatement_number=f"MISST-{m.id[:6]}",
                misstatement_type=MisstatementTypeEnum.FACTUAL,
                status=MisstatementStatusEnum.CORRECTED if m.is_corrected else MisstatementStatusEnum.UNCORRECTED,
                title=m.account_name or m.account_code,
                description=m.rationale or "Audit Misstatement",
                affected_fs_area=m.schedule_iii_category or "Financial Statements",
                amount_paise=m.amount_paise,
            )
            for m in misstatements
        ]
        sa450_summary = AuditCompletionEngine.evaluate_sa450_misstatements(
            engagement_id=engagement_id,
            misstatements=converted_m,
            overall_materiality_paise=overall_mat,
            performance_materiality_paise=perf_mat,
            clearly_trivial_threshold_paise=trivial_mat,
        )

        fs_repo = FinancialStatementRepository(session)
        fs_pkg = fs_repo.get_latest_package(engagement_id)

        comp_repo = ComplianceRepository(session)
        caro_workpapers = comp_repo.list_caro_workpapers_for_engagement(engagement_id)

        chk_repo = CompletionChecklistRepository(session)
        checklist_items = chk_repo.list_checklist_items(engagement_id)
        related_parties = chk_repo.get_related_party_completion(engagement_id)
        sa240 = chk_repo.get_sa240_completion(engagement_id)

        compl_repo = AuditCompletionRepository(session)
        gc = compl_repo.get_going_concern_assessment(engagement_id)
        mrl = next(iter(compl_repo.list_mrls(engagement_id)), None)
        subseqs = compl_repo.list_subsequent_events(engagement_id)

        gate_res = FinalizationGateEngine.evaluate(
            engagement_id=engagement_id,
            review_notes=all_review_notes,
            exceptions=exceptions,
            misstatements=misstatements,
            sa450_summary=sa450_summary,
            fs_package=fs_pkg,
            caro_workpapers=caro_workpapers,
            checklist_items=checklist_items,
            going_concern=gc,
            mrl=mrl,
            subsequent_events_count=len(subseqs),
            related_parties=related_parties,
            sa240_override=sa240,
        )

        open_dtos = [
            OpenItemDTO(
                id=b.source_ref,
                engagement_id=engagement_id,
                source_type=b.category,
                source_ref=b.source_ref,
                title=b.reason[:80],
                description=b.reason,
                severity=getattr(b.severity, "value", str(b.severity)),
                action_required=b.action_required,
                is_blocking=True,
                resolved=False,
            )
            for b in gate_res.blockers
        ]

        open_reg = OpenItemsRegisterDTO(
            engagement_id=engagement_id,
            items=open_dtos,
            total_open_count=len(open_dtos),
            critical_count=sum(1 for o in open_dtos if o.severity == "Critical"),
            high_count=sum(1 for o in open_dtos if o.severity == "High"),
            medium_count=sum(1 for o in open_dtos if o.severity == "Medium"),
            low_count=sum(1 for o in open_dtos if o.severity == "Low"),
            informational_count=sum(1 for o in open_dtos if o.severity == "Informational"),
        )

        return gate_res, open_reg

    def _initialize_default_checklist(self, session: Any, engagement_id: str) -> list[CompletionChecklistItem]:
        repo = CompletionChecklistRepository(session)
        default_categories = [
            (ChecklistCategoryEnum.PLANNING, "Engagement Planning & Pre-conditions (SA 210)", "Agree engagement terms, independence verification, and team staffing"),
            (ChecklistCategoryEnum.RISK_ASSESSMENT, "Risk Assessment & Materiality (SA 315 & SA 320)", "Identify significant risks and establish overall and performance materiality"),
            (ChecklistCategoryEnum.AUDIT_PROCEDURES, "Substantive & Control Procedures (SA 330)", "Execute tests of controls and substantive analytical/detailed procedures"),
            (ChecklistCategoryEnum.EVIDENCE, "Sufficient Appropriate Evidence (SA 500)", "Verify all working paper procedures have attached external/substantive evidence"),
            (ChecklistCategoryEnum.SAMPLING, "Audit Sampling Evaluation (SA 530)", "Evaluate representative samples and project misstatements where applicable"),
            (ChecklistCategoryEnum.EXCEPTIONS, "Audit Exception Resolution", "Clear all test exceptions and verify management explanations"),
            (ChecklistCategoryEnum.MISSTATEMENTS, "Misstatement Evaluation (SA 450)", "Aggregate uncorrected misstatements against materiality threshold"),
            (ChecklistCategoryEnum.REVIEW_NOTES, "Review Notes Clearance", "Ensure all Senior, Manager, and Partner review queries are answered and cleared"),
            (ChecklistCategoryEnum.FINANCIAL_STATEMENTS, "Schedule III Balance Sheet & P&L", "Verify presentation under Division I / II of Schedule III and check data drift"),
            (ChecklistCategoryEnum.NOTES_AND_DISCLOSURES, "Statutory Notes & Disclosures", "Verify 5-tier classified notes and accounting policy disclosures"),
            (ChecklistCategoryEnum.CASH_FLOW, "Cash Flow Statement (AS 3 / Ind AS 7)", "Verify indirect cash flow mathematical tie-out to cash balances"),
            (ChecklistCategoryEnum.CARO, "CARO 2020 Working Papers", "Complete clause-level workpapers for all 20 applicable clauses"),
            (ChecklistCategoryEnum.TAX_AUDIT, "Form 3CD Tax Audit Foundation", "Verify Section 40(a)(ia), 43B, and 269SS/269T compliance checks"),
            (ChecklistCategoryEnum.RELATED_PARTIES, "Related Parties (SA 550)", "Review related party register, arm's length testing, and note disclosures"),
            (ChecklistCategoryEnum.GOING_CONCERN, "Going Concern Assessment (SA 570)", "Evaluate 12-month solvency indicators, mitigations, and partner sign-off"),
            (ChecklistCategoryEnum.SUBSEQUENT_EVENTS, "Subsequent Events Review (SA 560)", "Review subsequent events between Balance Sheet and audit report date"),
            (ChecklistCategoryEnum.MANAGEMENT_REPRESENTATION, "Written Representations (SA 580)", "Obtain signed Management Representation Letter before final report"),
            (ChecklistCategoryEnum.FINAL_ANALYTICAL_REVIEW, "Final Analytical Review (SA 520)", "Perform overall financial ratio comparisons and investigate significant variances"),
            (ChecklistCategoryEnum.AUDIT_REPORT, "Audit Report Formulation (SA 700/705/706)", "Formulate statutory audit opinion based on gathered audit evidence"),
            (ChecklistCategoryEnum.PARTNER_REVIEW, "Partner Sign-off & Final Lock", "Final engagement review and cryptographic locking by engagement partner"),
        ]

        return [
            repo.save_checklist_item(
                CompletionChecklistItem(
                    engagement_id=engagement_id,
                    category=cat,
                    title=title,
                    description=desc,
                    is_applicable=True,
                    status=CompletionStatusEnum.NOT_STARTED,
                )
            )
            for cat, title, desc in default_categories
        ]

    def _to_checklist_dto(self, item: CompletionChecklistItem) -> ChecklistItemDTO:
        cat_val = item.category.value if hasattr(item.category, "value") else str(item.category)
        stat_val = item.status.value if hasattr(item.status, "value") else str(item.status)
        dt_val = item.updated_at.isoformat() if hasattr(item.updated_at, "isoformat") else str(item.updated_at)
        return ChecklistItemDTO(
            id=item.id,
            engagement_id=item.engagement_id,
            category=cat_val,
            title=item.title,
            description=item.description,
            is_applicable=item.is_applicable,
            status=stat_val,
            supporting_ref=item.supporting_ref,
            reviewer=item.reviewer,
            notes=item.notes,
            updated_at=dt_val,
        )

