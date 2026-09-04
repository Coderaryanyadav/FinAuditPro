"""Application service orchestrating Indian Statutory Compliance: CARO 2020 and Form 3CD Tax Audit."""

from typing import Any
from uuid import uuid4

from finauditpro.application.compliance_dtos import (
    ConcludeTaxAuditCheckDTO,
    ExecuteCAROProcedureDTO,
    ReviewCAROClauseDTO,
    RunTaxAuditCheckDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.clock import utc_now
from finauditpro.domain.compliance_entities import (
    CAROApplicabilityEnum,
    CAROClauseEnum,
    CAROClauseWorkpaper,
    CAROReportAnswerEnum,
    TaxAuditCheck,
    TaxAuditCheckResultEnum,
    TaxAuditSummary,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, PermissionDeniedError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import UserModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import (
    ComplianceRepository,
)


class ComplianceService:
    """Service managing CARO 2020 20-clause working papers and Form 3CD Tax Audit checks."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.core_audit_service = CoreAuditService(db_manager)

    def _get_current_user_name(self, session: Any) -> str:
        uid = SecurityContext.get_current_user_id()
        if not uid:
            return "Auditor"
        user = session.get(UserModel, uid)
        return user.username if user else uid

    def initialize_caro_clauses(self, engagement_id: str) -> list[CAROClauseWorkpaper]:
        """Initialize all 20 standard CARO 2020 clause working papers for an engagement."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(engagement_id):
                raise EntityNotFoundError("Engagement", engagement_id)

            repo = ComplianceRepository(session)
            existing = repo.list_caro_workpapers_for_engagement(engagement_id)
            if existing:
                return existing

            clauses = [
                (
                    "3(i)",
                    CAROClauseEnum.CLAUSE_1_PPE_INTANGIBLES.value,
                    "Whether the company is maintaining proper records showing full particulars of PPE and title deeds are held in the name of the company.",
                ),
                (
                    "3(ii)",
                    CAROClauseEnum.CLAUSE_2_INVENTORY_WORKING_CAPITAL.value,
                    "Whether physical verification of inventory has been conducted at reasonable intervals and quarterly returns filed with banks agree with books.",
                ),
                (
                    "3(iii)",
                    CAROClauseEnum.CLAUSE_3_LOANS_INVESTMENTS_GUARANTEES.value,
                    "Whether the company has made investments in, provided guarantee or security or granted any loans or advances in the nature of loans.",
                ),
                (
                    "3(iv)",
                    CAROClauseEnum.CLAUSE_4_SEC_185_186_COMPLIANCE.value,
                    "In respect of loans, investments, guarantees, and security, whether provisions of sections 185 and 186 of Companies Act have been complied with.",
                ),
                (
                    "3(v)",
                    CAROClauseEnum.CLAUSE_5_PUBLIC_DEPOSITS.value,
                    "In respect of deposits accepted, whether directives issued by the RBI and sections 73 to 76 of the Companies Act have been complied with.",
                ),
                (
                    "3(vi)",
                    CAROClauseEnum.CLAUSE_6_COST_RECORDS.value,
                    "Whether maintenance of cost records has been specified by the Central Government under section 148(1) of the Companies Act.",
                ),
                (
                    "3(vii)",
                    CAROClauseEnum.CLAUSE_7_STATUTORY_DUES.value,
                    "Whether the company is regular in depositing undisputed statutory dues (GST, PF, ESI, Income Tax) and disclosure of disputed arrears.",
                ),
                (
                    "3(viii)",
                    CAROClauseEnum.CLAUSE_8_UNDISCLOSED_INCOME.value,
                    "Whether any transactions not recorded in the books of account have been surrendered or disclosed as income during the year in tax assessments.",
                ),
                (
                    "3(ix)",
                    CAROClauseEnum.CLAUSE_9_LOAN_DEFAULTS_UTILIZATION.value,
                    "Whether the company has defaulted in repayment of loans or other borrowings or in the payment of interest thereon to any lender.",
                ),
                (
                    "3(x)",
                    CAROClauseEnum.CLAUSE_10_IPO_FPO_UTILIZATION.value,
                    "Whether moneys raised by way of initial public offer or further public offer or preferential allotment were applied for purposes for which raised.",
                ),
                (
                    "3(xi)",
                    CAROClauseEnum.CLAUSE_11_STATUTORY_DISCLOSURE_REPORTING.value,
                    "Whether any fraud by the company or on the company has been noticed or reported during the year.",  # ignore
                ),
                (
                    "3(xii)",
                    CAROClauseEnum.CLAUSE_12_NIDHI_COMPANY.value,
                    "Whether the Nidhi Company has complied with the Net Owned Funds to Deposits in the ratio of 1:20 to meet liabilities.",
                ),
                (
                    "3(xiii)",
                    CAROClauseEnum.CLAUSE_13_RELATED_PARTY_TRANS.value,
                    "Whether all transactions with the related parties are in compliance with sections 177 and 188 of Companies Act and properly disclosed.",
                ),
                (
                    "3(xiv)",
                    CAROClauseEnum.CLAUSE_14_INTERNAL_AUDIT.value,
                    "Whether the company has an internal audit system commensurate with the size and nature of its business and internal audit reports reviewed.",
                ),
                (
                    "3(xv)",
                    CAROClauseEnum.CLAUSE_15_NON_CASH_TRANSACTIONS.value,
                    "Whether the company has entered into any non-cash transactions with directors or persons connected with him under section 192.",
                ),
                (
                    "3(xvi)",
                    CAROClauseEnum.CLAUSE_16_RBI_ACT_REGISTRATION.value,
                    "Whether the company is required to be registered under section 45-IA of the Reserve Bank of India Act, 1934 and obtained certificate.",
                ),
                (
                    "3(xvii)",
                    CAROClauseEnum.CLAUSE_17_CASH_LOSSES.value,
                    "Whether the company has incurred cash losses in the financial year and in the immediately preceding financial year.",
                ),
                (
                    "3(xviii)",
                    CAROClauseEnum.CLAUSE_18_AUDITOR_RESIGNATION.value,
                    "Whether there has been any resignation of the statutory auditors during the year and whether incoming auditor considered issues raised.",
                ),
                (
                    "3(xix)",
                    CAROClauseEnum.CLAUSE_19_CAPABILITY_MEET_LIABILITIES.value,
                    "Whether on basis of financial ratios and aging of assets/liabilities, material uncertainty exists that company can meet liabilities within 1 year.",
                ),
                (
                    "3(xx)",
                    CAROClauseEnum.CLAUSE_20_CSR_COMPLIANCE.value,
                    "Whether in respect of other than ongoing projects, unspent CSR amount transferred to a Fund specified in Schedule VII within 6 months u/s 135(5).",
                ),
            ]

            created = []
            for code, title, q in clauses:
                wp = CAROClauseWorkpaper(
                    id=str(uuid4()),
                    engagement_id=engagement_id,
                    clause_code=code,
                    clause_title=title,
                    applicability=CAROApplicabilityEnum.APPLICABLE,
                    applicability_reason="Standard applicability assessment",
                    question=q,
                    procedure_text="Review management representations, corroborating register entries, and sample testing results.",
                    report_answer=CAROReportAnswerEnum.UNQUALIFIED,
                    preparer=self._get_current_user_name(session),
                    status="Draft",
                )
                created.append(repo.add_caro_workpaper(wp))
            return created

    def execute_caro_procedure(self, dto: ExecuteCAROProcedureDTO) -> CAROClauseWorkpaper:
        """Execute and document audit work for a specific CARO 2020 clause."""
        with self.db_manager.session_scope() as session:
            repo = ComplianceRepository(session)
            wp = repo.get_caro_workpaper_by_clause(dto.engagement_id, dto.clause_code)
            if not wp:
                wp = CAROClauseWorkpaper(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    clause_code=dto.clause_code,
                    clause_title=dto.clause_title,
                    applicability=dto.applicability,
                    applicability_reason=dto.applicability_reason,
                    question=dto.question,
                    procedure_text=dto.procedure_text,
                    evidence_refs=dto.evidence_refs,
                    finding_refs=dto.finding_refs,
                    management_response=dto.management_response,
                    conclusion_text=dto.conclusion_text,
                    report_answer=dto.report_answer,
                    preparer=self._get_current_user_name(session),
                    status="Completed",
                )
                return repo.add_caro_workpaper(wp)

            wp.applicability = dto.applicability
            wp.applicability_reason = dto.applicability_reason
            wp.procedure_text = dto.procedure_text
            wp.evidence_refs = dto.evidence_refs
            wp.finding_refs = dto.finding_refs
            wp.management_response = dto.management_response
            wp.conclusion_text = dto.conclusion_text
            wp.report_answer = dto.report_answer
            wp.status = "Completed"
            wp.updated_at = utc_now()
            return repo.update_caro_workpaper(wp)

    def review_caro_clause(self, dto: ReviewCAROClauseDTO) -> CAROClauseWorkpaper:
        """Review and approve a CARO clause working paper (Requires Senior, Manager, or Partner)."""
        session_info = SecurityContext.get_current_session()
        if session_info and session_info.role not in (
            RoleEnum.SENIOR,
            RoleEnum.MANAGER,
            RoleEnum.PARTNER,
            RoleEnum.ADMINISTRATOR,
        ):
            raise PermissionDeniedError(
                "Only Senior, Manager, or Partner can review CARO workpapers."
            )

        with self.db_manager.session_scope() as session:
            repo = ComplianceRepository(session)
            wp = repo.get_caro_workpaper_by_clause(dto.engagement_id, dto.clause_code)
            if not wp:
                raise EntityNotFoundError("CAROClauseWorkpaper", dto.clause_code)

            wp.reviewer = self._get_current_user_name(session)
            wp.status = "Reviewed" if dto.decision == "APPROVE" else "Under Review"
            wp.updated_at = utc_now()
            return repo.update_caro_workpaper(wp)

    def list_caro_workpapers(self, engagement_id: str) -> list[CAROClauseWorkpaper]:
        """List all CARO clause workpapers for an engagement."""
        with self.db_manager.session_scope() as session:
            return ComplianceRepository(session).list_caro_workpapers_for_engagement(engagement_id)

    def run_tax_audit_check(self, dto: RunTaxAuditCheckDTO) -> TaxAuditCheck:
        """Execute a discrete Form 3CD statutory rule check and log exception if detected."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            exc_id = None
            if (
                dto.system_result == TaxAuditCheckResultEnum.EXCEPTION_DETECTED
                and dto.exception_amount_paise > 0
            ):
                from finauditpro.domain.audit_execution_entities import (
                    AuditException,
                    ExceptionStatusEnum,
                )
                from finauditpro.domain.audit_matrix_entities import (
                    AssertionEnum,
                    AuditProcedure,
                    ProcedureStatusEnum,
                )
                from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
                    AuditMatrixRepository,
                )
                from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
                    CoreAuditEngineRepository,
                )

                matrix_repo = AuditMatrixRepository(session)
                procs = matrix_repo.list_procedures_for_engagement(dto.engagement_id)
                if procs:
                    proc_id = procs[0].id
                else:
                    default_proc = AuditProcedure(
                        id=str(uuid4()),
                        engagement_id=dto.engagement_id,
                        procedure_code=f"PROC-TAX-{dto.clause_code[:10]}",
                        objective=f"Tax Audit Form 3CD compliance verification for {dto.clause_code}",
                        procedure_type="Statutory Compliance",
                        account_area="Tax Audit",
                        instructions=dto.rule_logic,
                        assertions=[AssertionEnum.COMPLETENESS],
                        status=ProcedureStatusEnum.COMPLETED,
                        preparer=self._get_current_user_name(session),
                    )
                    matrix_repo.add_procedure(default_proc)
                    proc_id = default_proc.id

                exc = AuditException(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    procedure_id=proc_id,
                    sample_item_id=None,
                    exception_code=f"TAX-EXC-{dto.clause_code}",
                    title=f"Form 3CD Exception: {dto.description[:80]}",
                    description=f"Rule: {dto.rule_logic}. Input: {dto.input_source}",
                    amount_paise=dto.exception_amount_paise,
                    status=ExceptionStatusEnum.OPEN,
                )
                saved_exc = CoreAuditEngineRepository(session).add_exception(exc)
                AuditEventRepository(session).add(
                    AuditEvent(
                        engagement_id=dto.engagement_id,
                        entity_name="AuditException",
                        entity_id=saved_exc.id,
                        action="AUDIT_EXCEPTION_LOGGED",
                        payload={"code": saved_exc.exception_code, "amount_paise": saved_exc.amount_paise},
                        user_id=self._get_current_user_name(session),
                    )
                )
                exc_id = saved_exc.id

            check = TaxAuditCheck(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                clause_code=dto.clause_code,
                category=dto.category,
                description=dto.description,
                input_source=dto.input_source,
                rule_logic=dto.rule_logic,
                system_result=dto.system_result,
                auditor_conclusion=dto.system_result,
                exception_amount_paise=dto.exception_amount_paise,
                exception_id=exc_id,
                evidence_ref=dto.evidence_ref,
                reviewer=self._get_current_user_name(session),
                status="Completed",
            )
            saved = ComplianceRepository(session).add_tax_check(check)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="TaxAuditCheck",
                    entity_id=saved.id,
                    action="TAX_AUDIT_CHECK_EXECUTED",
                    payload={"clause": saved.clause_code, "result": saved.system_result.value},
                    user_id=self._get_current_user_name(session),
                )
            )
            return saved

    def conclude_tax_audit_check(self, dto: ConcludeTaxAuditCheckDTO) -> TaxAuditCheck:
        """Record auditor conclusion and notes for a Form 3CD check."""
        with self.db_manager.session_scope() as session:
            repo = ComplianceRepository(session)
            check = repo.session.get(TaxAuditCheck, dto.check_id)
            if not check or check.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("TaxAuditCheck", dto.check_id)

            check.auditor_conclusion = dto.auditor_conclusion
            check.exception_amount_paise = dto.exception_amount_paise
            check.reviewer_notes = dto.reviewer_notes
            check.reviewer = self._get_current_user_name(session)
            check.updated_at = utc_now()
            return repo.update_tax_check(check)

    def get_tax_audit_summary(self, engagement_id: str) -> TaxAuditSummary:
        """Get aggregate summary of Form 3CD Tax Audit checks and exceptions."""
        with self.db_manager.session_scope() as session:
            checks = ComplianceRepository(session).list_tax_checks_for_engagement(engagement_id)
            tot = len(checks)
            comp = len(
                [c for c in checks if c.auditor_conclusion == TaxAuditCheckResultEnum.COMPLIANT]
            )
            exc_checks = [
                c
                for c in checks
                if c.auditor_conclusion == TaxAuditCheckResultEnum.EXCEPTION_DETECTED
            ]
            tot_exc_amt = sum(c.exception_amount_paise for c in exc_checks)
            ready = bool(tot > 0 and len(exc_checks) == 0)

            return TaxAuditSummary(
                engagement_id=engagement_id,
                total_checks=tot,
                compliant_checks=comp,
                exception_checks=len(exc_checks),
                total_exception_amount_paise=tot_exc_amt,
                unresolved_exceptions_count=len(exc_checks),
                is_ready_for_form3cd_signoff=ready,
            )
