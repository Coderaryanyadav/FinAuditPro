"""Application service for generating Schedule III Statements, Notes, Cash Flow, and Packaging."""

import hashlib
from typing import Any
from uuid import uuid4

from finauditpro.application.financial_statement_dtos import (
    CreateOrUpdateNoteDTO,
    CreateOrUpdatePolicyDTO,
    GenerateFinancialStatementsDTO,
    GetDataLineageDTO,
    LockFinancialStatementPackageDTO,
    ReviewFinancialStatementPackageDTO,
    SaveFinancialStatementPackageDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.domain.cash_flow_evaluation_engine import (
    build_indirect_cash_flow_statement,
    build_statement_of_changes_in_equity,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.financial_statement_entities import (
    AccountingPolicy,
    BalanceSheet,
    CashFlowStatement,
    DataLineageNode,
    FinancialStatementNote,
    FinancialStatementPackage,
    FinancialStatementVersionEnum,
    PackageStatusEnum,
    ProfitAndLossStatement,
    StatementOfChangesInEquity,
)
from finauditpro.domain.financial_statement_evaluation_engine import (
    build_schedule_iii_balance_sheet,
    build_schedule_iii_profit_and_loss,
)
from finauditpro.domain.financial_statement_lineage_engine import extract_data_lineage_trace
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import UserModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)


class FinancialStatementService:
    """Service managing Schedule III presentation, Notes, Cash Flow, and Statement Packaging."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.adj_service = AuditAdjustmentService(db_manager)

    def _get_current_user_name(self, session: Any) -> str:
        uid = SecurityContext.get_current_user_id()
        if not uid:
            return "Auditor"
        user = session.get(UserModel, uid)
        return user.username if user else uid

    def _compute_data_hash(self, adj_tb_lines: list[Any]) -> str:
        data_str = "|".join(
            f"{l.account_code}:{l.adjusted_net_paise}"
            for l in sorted(adj_tb_lines, key=lambda x: x.account_code)
        )
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def generate_balance_sheet(self, dto: GenerateFinancialStatementsDTO) -> BalanceSheet:
        """Generate Schedule III Balance Sheet from Adjusted Trial Balance lines."""
        adj_tb = self.adj_service.calculate_adjusted_trial_balance(
            dto.engagement_id, dto.dataset_id
        )
        return build_schedule_iii_balance_sheet(
            dto.engagement_id, dto.as_at_date, adj_tb.lines, dto.division
        )

    def generate_profit_and_loss(
        self, dto: GenerateFinancialStatementsDTO
    ) -> ProfitAndLossStatement:
        """Generate Schedule III Statement of Profit & Loss from Adjusted Trial Balance lines."""
        adj_tb = self.adj_service.calculate_adjusted_trial_balance(
            dto.engagement_id, dto.dataset_id
        )
        return build_schedule_iii_profit_and_loss(
            dto.engagement_id, dto.for_period_ended, adj_tb.lines
        )

    def generate_cash_flow_statement(
        self, dto: GenerateFinancialStatementsDTO
    ) -> CashFlowStatement:
        """Generate Indirect Cash Flow Statement and verify cash reconciliation invariants."""
        bs = self.generate_balance_sheet(dto)
        pnl = self.generate_profit_and_loss(dto)
        return build_indirect_cash_flow_statement(dto.engagement_id, dto.for_period_ended, bs, pnl)

    def generate_statement_of_changes_in_equity(
        self, dto: GenerateFinancialStatementsDTO
    ) -> StatementOfChangesInEquity:
        """Generate Statement of Changes in Equity / Reserves Reconciliation."""
        bs = self.generate_balance_sheet(dto)
        pnl = self.generate_profit_and_loss(dto)
        return build_statement_of_changes_in_equity(dto.engagement_id, bs, pnl)

    def save_package(self, dto: SaveFinancialStatementPackageDTO) -> FinancialStatementPackage:
        """Generate and persist a complete versioned Financial Statement package."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            repo = FinancialStatementRepository(session)
            latest = repo.get_latest_package(dto.engagement_id)
            if latest and latest.is_locked:
                raise ValidationError(
                    "Cannot modify locked financial statement package. Re-opening required."
                )

            adj_tb = self.adj_service.calculate_adjusted_trial_balance(
                dto.engagement_id, dto.dataset_id
            )
            bs = build_schedule_iii_balance_sheet(dto.engagement_id, dto.as_at_date, adj_tb.lines)
            pnl = build_schedule_iii_profit_and_loss(
                dto.engagement_id, dto.for_period_ended, adj_tb.lines
            )
            cf = build_indirect_cash_flow_statement(
                dto.engagement_id, dto.for_period_ended, bs, pnl
            )
            eq = build_statement_of_changes_in_equity(dto.engagement_id, bs, pnl)
            notes = repo.list_notes_for_engagement(dto.engagement_id)
            policies = repo.list_policies_for_engagement(dto.engagement_id)

            pkg = FinancialStatementPackage(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                version=dto.version,
                status=PackageStatusEnum.DRAFT,
                balance_sheet=bs,
                profit_and_loss=pnl,
                cash_flow=cf,
                changes_in_equity=eq,
                notes=notes,
                policies=policies,
                data_hash=self._compute_data_hash(adj_tb.lines),
                is_locked=False,
                is_stale=False,
                created_by=self._get_current_user_name(session),
            )
            saved = repo.add_package(pkg)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="FinancialStatementPackage",
                    entity_id=saved.id,
                    action="FS_PACKAGE_SAVED",
                    payload={"version": saved.version.value, "balanced": bs.is_balanced},
                    user_id=saved.created_by,
                )
            )
            return saved

    def review_package(self, dto: ReviewFinancialStatementPackageDTO) -> FinancialStatementPackage:
        """Review and approve financial statement package (Requires Manager or Partner role)."""
        session_info = SecurityContext.get_current_session()
        if session_info and session_info.role not in (
            RoleEnum.MANAGER,
            RoleEnum.PARTNER,
            RoleEnum.ADMINISTRATOR,
        ):
            raise PermissionDeniedError(
                "Only Manager, Partner, or Admin can review/approve financial statement packages."
            )

        with self.db_manager.session_scope() as session:
            repo = FinancialStatementRepository(session)
            pkg = repo.get_package_by_id(dto.package_id)
            if not pkg or pkg.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("FinancialStatementPackage", dto.package_id)
            if pkg.is_locked:
                raise ValidationError(
                    "Package is locked and cannot be re-reviewed without unsealing."
                )

            pkg.status = (
                PackageStatusEnum.APPROVED
                if dto.decision == "APPROVE"
                else PackageStatusEnum.UNDER_REVIEW
            )
            pkg.approved_by = (
                self._get_current_user_name(session) if dto.decision == "APPROVE" else None
            )
            pkg.version = FinancialStatementVersionEnum.REVIEWED_V3
            pkg.updated_at = utc_now()
            saved = repo.update_package(pkg)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="FinancialStatementPackage",
                    entity_id=saved.id,
                    action=f"FS_PACKAGE_{dto.decision}",
                    payload={"notes": dto.reviewer_notes},
                    user_id=self._get_current_user_name(session),
                )
            )
            return saved

    def lock_package(self, dto: LockFinancialStatementPackageDTO) -> FinancialStatementPackage:
        """Lock financial statement package for final archival (Requires Partner role)."""
        session_info = SecurityContext.get_current_session()
        if session_info and session_info.role not in (
            RoleEnum.PARTNER,
            RoleEnum.ADMINISTRATOR,
        ):
            raise PermissionDeniedError(
                "Only Partner or Admin can lock financial statement packages."
            )

        with self.db_manager.session_scope() as session:
            repo = FinancialStatementRepository(session)
            pkg = repo.get_package_by_id(dto.package_id)
            if not pkg or pkg.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("FinancialStatementPackage", dto.package_id)
            if not pkg.balance_sheet.is_balanced:
                raise ValidationError(
                    "Cannot lock unbalanced financial statements (Assets != Liabilities + Equity)."
                )

            pkg.is_locked = True
            pkg.status = PackageStatusEnum.LOCKED
            pkg.version = FinancialStatementVersionEnum.FINAL_LOCKED_V4
            pkg.updated_at = utc_now()
            saved = repo.update_package(pkg)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="FinancialStatementPackage",
                    entity_id=saved.id,
                    action="FS_PACKAGE_LOCKED",
                    payload={"version": saved.version.value},
                    user_id=self._get_current_user_name(session),
                )
            )
            return saved

    def check_data_drift_and_invalidate(self, engagement_id: str) -> bool:
        """Detect if underlying trial balance or AJEs have changed and mark packages as stale."""
        with self.db_manager.session_scope() as session:
            repo = FinancialStatementRepository(session)
            latest = repo.get_latest_package(engagement_id)
            if not latest:
                return False

            adj_tb = self.adj_service.calculate_adjusted_trial_balance(engagement_id)
            current_hash = self._compute_data_hash(adj_tb.lines)

            if latest.data_hash and latest.data_hash != current_hash:
                latest.is_stale = True
                latest.status = PackageStatusEnum.UNDER_REVIEW
                repo.update_package(latest)
                AuditEventRepository(session).add(
                    AuditEvent(
                        engagement_id=engagement_id,
                        entity_name="FinancialStatementPackage",
                        entity_id=latest.id,
                        action="FS_PACKAGE_DATA_DRIFT_DETECTED",
                        payload={"message": "Underlying data changed. Marked stale."},
                        user_id=self._get_current_user_name(session),
                    )
                )
                return True
            return False

    def create_or_update_note(self, dto: CreateOrUpdateNoteDTO) -> FinancialStatementNote:
        """Create or update a structured Note to Accounts."""
        with self.db_manager.session_scope() as session:
            repo = FinancialStatementRepository(session)
            note = FinancialStatementNote(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                package_id=dto.package_id,
                note_number=dto.note_number,
                title=dto.title,
                fs_reference=dto.fs_reference,
                source_type=dto.source_type,
                disclosure_classification=dto.disclosure_classification,
                amount_paise=dto.amount_paise,
                details=dto.details,
                narrative=dto.narrative,
                prepared_by=self._get_current_user_name(session),
            )
            return repo.add_note(note)

    def create_or_update_policy(self, dto: CreateOrUpdatePolicyDTO) -> AccountingPolicy:
        """Create or update a significant accounting policy disclosure."""
        with self.db_manager.session_scope() as session:
            repo = FinancialStatementRepository(session)
            pol = AccountingPolicy(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                policy_code=dto.policy_code,
                title=dto.title,
                category=dto.category,
                applicable_standard=dto.applicable_standard,
                policy_text=dto.policy_text,
                changes_text=dto.changes_text,
                reviewed_by=self._get_current_user_name(session),
            )
            return repo.add_policy(pol)

    def get_data_lineage(self, dto: GetDataLineageDTO) -> DataLineageNode:
        """Extract complete deterministic lineage: FS Line -> Note -> Mapped Accounts -> Adjusted TB -> AJE -> Original TB."""
        bs = self.generate_balance_sheet(
            GenerateFinancialStatementsDTO(
                engagement_id=dto.engagement_id, dataset_id=dto.dataset_id
            )
        )
        pnl = self.generate_profit_and_loss(
            GenerateFinancialStatementsDTO(
                engagement_id=dto.engagement_id, dataset_id=dto.dataset_id
            )
        )
        with self.db_manager.session_scope() as session:
            notes = FinancialStatementRepository(session).list_notes_for_engagement(
                dto.engagement_id
            )
        adj_tb = self.adj_service.calculate_adjusted_trial_balance(
            dto.engagement_id, dto.dataset_id
        )
        return extract_data_lineage_trace(dto.line_code, bs, pnl, notes, adj_tb.lines)
