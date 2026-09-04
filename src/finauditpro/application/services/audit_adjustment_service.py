"""Application service orchestrating Audit Adjustments (AJE), Adjusted Trial Balance, and Lead Schedule Rollups."""

from collections import defaultdict
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from finauditpro.application.audit_adjustment_dtos import (
    AccountTraceDTO,
    ApplyAJEDTO,
    CreateAJEDTO,
    LeadScheduleTraceDTO,
    ReverseAJEDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
    UpdateAJEDTO,
)
from finauditpro.application.security.engagement_lock_guard import assert_engagement_not_locked
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_adjustment_entities import (
    AdjustedTrialBalanceLine,
    AdjustedTrialBalanceSummary,
    AJEStatusEnum,
    AuditJournalEntry,
    AuditJournalLine,
    LeadScheduleAccountLine,
    LeadScheduleSummary,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import FinancialDatasetModel, UserModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
    FinancialDataRepository,
)
from finauditpro.infrastructure.persistence.repositories.account_mapping_repository import (
    AccountMappingRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_adjustment_repository import (
    AuditAdjustmentRepository,
)


class AuditAdjustmentService:
    """Service managing Audit Adjusting Journal Entries, Double-Entry Invariants, and Lead Schedules."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def _get_trusted_user(self, session: Any) -> tuple[str, str]:
        user_session = SecurityContext.get_current_session()
        if not user_session or not user_session.user_id:
            return "Auditor", "Associate"
        user = session.get(UserModel, user_session.user_id)
        role_val = (
            user.role
            if user
            else (
                user_session.role.value
                if hasattr(user_session.role, "value")
                else str(user_session.role)
            )
        )
        return (user.id if user else user_session.user_id, role_val)

    def _assert_not_locked(self, session: Any, engagement_id: str) -> None:
        eng = EngagementRepository(session).get_by_id(engagement_id)
        if not eng:
            raise EntityNotFoundError("Engagement", engagement_id)
        assert_engagement_not_locked(eng)

    def create_adjustment(self, dto: CreateAJEDTO) -> AuditJournalEntry:
        """Create a new Draft Audit Adjusting Journal Entry with strict double-entry validation."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)

            actor_id, _ = self._get_trusted_user(session)
            aje_repo = AuditAdjustmentRepository(session)
            if aje_repo.get_entry_by_number(dto.engagement_id, dto.aje_number):
                raise ValidationError(
                    f"AJE number '{dto.aje_number}' already exists in this engagement."
                )

            lines = [
                AuditJournalLine(
                    id=str(uuid4()),
                    entry_id="",
                    line_no=idx,
                    account_code=l.account_code,
                    account_name=l.account_name,
                    debit_paise=l.debit_paise,
                    credit_paise=l.credit_paise,
                    lead_schedule_ref=l.lead_schedule_ref,
                    narration=l.narration,
                )
                for idx, l in enumerate(dto.lines, start=1)
            ]
            entry = AuditJournalEntry(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                aje_number=dto.aje_number,
                entry_date=dto.entry_date,
                aje_type=dto.aje_type,
                status=AJEStatusEnum.DRAFT,
                title=dto.title,
                narration=dto.narration,
                reason=dto.reason,
                working_paper_ref=dto.working_paper_ref,
                prepared_by=actor_id,
                lines=lines,
            )
            entry.validate_double_entry()
            created = aje_repo.add_entry(entry)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditJournalEntry",
                    entity_id=created.id,
                    action="AJE_CREATED",
                    payload={
                        "aje_number": created.aje_number,
                        "total_paise": created.total_debit_paise,
                    },
                    user_id=actor_id,
                )
            )
            return created

    def update_draft_adjustment(self, dto: UpdateAJEDTO) -> AuditJournalEntry:
        """Update an existing draft or rejected AJE with strict double-entry validation."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            entry = aje_repo.get_entry_by_id(dto.entry_id)
            if not entry or entry.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", dto.entry_id)

            if entry.status not in (AJEStatusEnum.DRAFT, AJEStatusEnum.REJECTED):
                raise ValidationError(
                    f"Cannot edit AJE '{entry.aje_number}' in status '{entry.status}'. "
                    "Only Draft or Rejected adjustments may be edited. Use reversal for applied/approved adjustments."
                )

            actor_id, _ = self._get_trusted_user(session)
            lines = [
                AuditJournalLine(
                    id=str(uuid4()),
                    entry_id=entry.id,
                    line_no=idx,
                    account_code=l.account_code,
                    account_name=l.account_name,
                    debit_paise=l.debit_paise,
                    credit_paise=l.credit_paise,
                    lead_schedule_ref=l.lead_schedule_ref,
                    narration=l.narration,
                )
                for idx, l in enumerate(dto.lines, start=1)
            ]
            entry.title = dto.title
            entry.narration = dto.narration
            entry.reason = dto.reason
            entry.working_paper_ref = dto.working_paper_ref
            entry.aje_type = dto.aje_type
            entry.lines = lines
            entry.validate_double_entry()

            updated = aje_repo.update_entry(entry)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditJournalEntry",
                    entity_id=updated.id,
                    action="AJE_UPDATED",
                    payload={
                        "aje_number": updated.aje_number,
                        "total_paise": updated.total_debit_paise,
                    },
                    user_id=actor_id,
                )
            )
            return updated

    def delete_draft_adjustment(self, engagement_id: str, entry_id: str) -> bool:
        """Delete a draft AJE permanently."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            entry = aje_repo.get_entry_by_id(entry_id)
            if not entry or entry.engagement_id != engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", entry_id)
            if entry.status != AJEStatusEnum.DRAFT:
                raise ValidationError(
                    f"Cannot delete AJE '{entry.aje_number}' with status '{entry.status}'. "
                    "Only Draft adjustments can be deleted."
                )
            actor_id, _ = self._get_trusted_user(session)
            success = aje_repo.delete_draft_entry(entry_id)
            if success:
                AuditEventRepository(session).add(
                    AuditEvent(
                        id=str(uuid4()),
                        engagement_id=engagement_id,
                        entity_name="AuditJournalEntry",
                        entity_id=entry_id,
                        action="AJE_DELETED",
                        payload={"aje_number": entry.aje_number},
                        user_id=actor_id,
                    )
                )
            return success

    def submit_adjustment(self, dto: SubmitAJEDTO) -> AuditJournalEntry:
        """Submit a draft AJE for review."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            entry = aje_repo.get_entry_by_id(dto.entry_id)
            if not entry or entry.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", dto.entry_id)
            actor_id, _ = self._get_trusted_user(session)
            entry.submit_for_review(actor_id)
            return aje_repo.update_entry(entry)

    def review_adjustment(self, dto: ReviewAJEDTO) -> AuditJournalEntry:
        """Review an AJE (Approve or Reject) enforcing Maker-Checker segregation of duties."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            entry = aje_repo.get_entry_by_id(dto.entry_id)
            if not entry or entry.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", dto.entry_id)

            reviewer_id, role = self._get_trusted_user(session)
            if entry.prepared_by == reviewer_id:
                raise PermissionDeniedError(
                    f"Maker-Checker Violation: User '{reviewer_id}' prepared AJE '{entry.aje_number}' and cannot approve it."
                )
            role_clean = role.strip().title()
            if not any(r in role_clean for r in ("Senior", "Manager", "Partner", "Admin")):
                raise PermissionDeniedError(
                    f"User role '{role}' is not authorized to review audit adjustments."
                )

            if dto.decision.upper() == "APPROVE":
                entry.approve(reviewer_id)
            else:
                entry.reject(reviewer_id, dto.rejection_reason or "Reviewer rejected adjustment.")

            updated = aje_repo.update_entry(entry)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditJournalEntry",
                    entity_id=updated.id,
                    action=f"AJE_{dto.decision.upper()}D",
                    payload={"aje_number": updated.aje_number, "status": updated.status.value},
                    user_id=reviewer_id,
                )
            )
            return updated

    def apply_adjustment(self, dto: ApplyAJEDTO) -> AuditJournalEntry:
        """Apply an approved AJE to the engagement's financial figures."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            entry = aje_repo.get_entry_by_id(dto.entry_id)
            if not entry or entry.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", dto.entry_id)
            actor_id, _ = self._get_trusted_user(session)
            entry.apply(actor_id)
            return aje_repo.update_entry(entry)

    def reverse_adjustment(self, dto: ReverseAJEDTO) -> AuditJournalEntry:
        """Create a mirrored reversing AJE to reverse an approved/applied adjustment while preserving audit history."""
        with self.db_manager.session_scope() as session:
            self._assert_not_locked(session, dto.engagement_id)
            aje_repo = AuditAdjustmentRepository(session)
            orig = aje_repo.get_entry_by_id(dto.entry_id)
            if not orig or orig.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditJournalEntry", dto.entry_id)
            if orig.status not in (AJEStatusEnum.APPROVED, AJEStatusEnum.APPLIED):
                raise ValidationError(
                    f"Cannot reverse AJE '{orig.aje_number}' with status '{orig.status}'."
                )

            actor_id, _ = self._get_trusted_user(session)
            reversal_lines = [
                AuditJournalLine(
                    id=str(uuid4()),
                    entry_id="",
                    line_no=idx,
                    account_code=l.account_code,
                    account_name=l.account_name,
                    debit_paise=l.credit_paise,
                    credit_paise=l.debit_paise,
                    lead_schedule_ref=l.lead_schedule_ref,
                    narration=f"Reversal of {orig.aje_number}: {l.narration or ''}".strip(),
                )
                for idx, l in enumerate(orig.lines, start=1)
            ]
            reversal_entry = AuditJournalEntry(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                aje_number=dto.reversal_aje_number,
                entry_date=orig.entry_date,
                aje_type=orig.aje_type,
                status=AJEStatusEnum.APPLIED,
                title=f"Reversal of {orig.aje_number}: {orig.title}",
                narration=f"Reversing entry for {orig.aje_number}. Reason: {dto.reason}",
                reason=dto.reason,
                working_paper_ref=orig.working_paper_ref,
                prepared_by=actor_id,
                reviewed_by=actor_id,
                reversal_of_entry_id=orig.id,
                lines=reversal_lines,
            )
            reversal_entry.validate_double_entry()
            orig.mark_reversed(reversal_entry.id)
            aje_repo.update_entry(orig)
            return aje_repo.add_entry(reversal_entry)

    def calculate_adjusted_trial_balance(
        self, engagement_id: str, dataset_id: str | None = None
    ) -> AdjustedTrialBalanceSummary:
        """Calculate the complete Adjusted Trial Balance by combining unadjusted TB rows with approved/applied AJEs."""
        with self.db_manager.session_scope() as session:
            fin_repo, map_repo, aje_repo = (
                FinancialDataRepository(session),
                AccountMappingRepository(session),
                AuditAdjustmentRepository(session),
            )

            if not dataset_id:
                stmt = (
                    select(FinancialDatasetModel.id)
                    .where(FinancialDatasetModel.engagement_id == engagement_id)
                    .order_by(FinancialDatasetModel.created_at.desc())
                )
                dataset_id = session.scalars(stmt).first()

            tb_lines = fin_repo.get_trial_balance_lines(dataset_id) if dataset_id else []
            mappings = {
                m.account_code: m for m in map_repo.list_mappings_for_engagement(engagement_id)
            }
            applied_ajes = aje_repo.list_applied_and_approved_entries(engagement_id)

            aje_dr: dict[str, int] = defaultdict(int)
            aje_cr: dict[str, int] = defaultdict(int)
            aje_nums: dict[str, list[str]] = defaultdict(list)

            for aje in applied_ajes:
                for line in aje.lines:
                    aje_dr[line.account_code] += line.debit_paise
                    aje_cr[line.account_code] += line.credit_paise
                    if aje.aje_number not in aje_nums[line.account_code]:
                        aje_nums[line.account_code].append(aje.aje_number)

            adj_lines: list[AdjustedTrialBalanceLine] = []
            processed: set[str] = set()
            t_u_dr, t_u_cr, t_a_dr, t_a_cr, t_f_dr, t_f_cr = 0, 0, 0, 0, 0, 0

            for tb in tb_lines:
                code = tb.account_code or f"ACC_{tb.source_row_no}"
                processed.add(code)
                mapping = mappings.get(code)
                u_dr = tb.closing_dr_paise or tb.debit_paise
                u_cr = tb.closing_cr_paise or tb.credit_paise
                u_net = u_dr - u_cr
                d_adj, c_adj = aje_dr.get(code, 0), aje_cr.get(code, 0)
                n_adj = d_adj - c_adj
                c_net = u_net + n_adj
                f_dr, f_cr = max(0, c_net), max(0, -c_net)

                t_u_dr += u_dr
                t_u_cr += u_cr
                t_a_dr += d_adj
                t_a_cr += c_adj
                t_f_dr += f_dr
                t_f_cr += f_cr
                adj_lines.append(
                    AdjustedTrialBalanceLine(
                        account_code=code,
                        account_name=tb.account_name,
                        schedule_iii_category=mapping.schedule_iii_category if mapping else "",
                        schedule_iii_line_item=mapping.schedule_iii_line_item if mapping else "",
                        lead_schedule_ref=mapping.lead_schedule_ref if mapping else "WP-MISC",
                        account_type=mapping.account_type if mapping else AccountTypeEnum.ASSET,
                        unadjusted_dr_paise=u_dr,
                        unadjusted_cr_paise=u_cr,
                        unadjusted_net_paise=u_net,
                        adjustment_dr_paise=d_adj,
                        adjustment_cr_paise=c_adj,
                        net_adjustment_paise=n_adj,
                        adjusted_dr_paise=f_dr,
                        adjusted_cr_paise=f_cr,
                        adjusted_net_paise=c_net,
                        linked_aje_numbers=aje_nums.get(code, []),
                    )
                )

            extra_codes = (set(aje_dr.keys()) | set(aje_cr.keys())) - processed
            for code in sorted(extra_codes):
                d_adj = aje_dr.get(code, 0)
                c_adj = aje_cr.get(code, 0)
                n_adj = d_adj - c_adj
                f_dr, f_cr = max(0, n_adj), max(0, -n_adj)
                mapping = mappings.get(code)
                t_a_dr += d_adj
                t_a_cr += c_adj
                t_f_dr += f_dr
                t_f_cr += f_cr
                acct_name = (
                    mapping.account_name
                    if mapping
                    else next(
                        (l.account_name for a in applied_ajes for l in a.lines if l.account_code == code),
                        code,
                    )
                )
                adj_lines.append(
                    AdjustedTrialBalanceLine(
                        account_code=code,
                        account_name=acct_name,
                        schedule_iii_category=mapping.schedule_iii_category if mapping else "",
                        schedule_iii_line_item=mapping.schedule_iii_line_item if mapping else "",
                        lead_schedule_ref=mapping.lead_schedule_ref if mapping else "WP-MISC",
                        account_type=mapping.account_type if mapping else AccountTypeEnum.ASSET,
                        unadjusted_dr_paise=0,
                        unadjusted_cr_paise=0,
                        unadjusted_net_paise=0,
                        adjustment_dr_paise=d_adj,
                        adjustment_cr_paise=c_adj,
                        net_adjustment_paise=n_adj,
                        adjusted_dr_paise=f_dr,
                        adjusted_cr_paise=f_cr,
                        adjusted_net_paise=n_adj,
                        linked_aje_numbers=aje_nums.get(code, []),
                    )
                )

            return AdjustedTrialBalanceSummary(
                total_unadjusted_dr_paise=t_u_dr,
                total_unadjusted_cr_paise=t_u_cr,
                total_adjustment_dr_paise=t_a_dr,
                total_adjustment_cr_paise=t_a_cr,
                total_adjusted_dr_paise=t_f_dr,
                total_adjusted_cr_paise=t_f_cr,
                line_count=len(adj_lines),
                applied_aje_count=len(applied_ajes),
                lines=adj_lines,
            )

    def calculate_lead_schedules(
        self, engagement_id: str, dataset_id: str | None = None
    ) -> list[LeadScheduleSummary]:
        """Roll up adjusted trial balance accounts into standard Schedule III Lead Schedules."""
        adj_tb = self.calculate_adjusted_trial_balance(engagement_id, dataset_id)
        grouped: dict[str, list[AdjustedTrialBalanceLine]] = defaultdict(list)
        for line in adj_tb.lines:
            grouped[line.lead_schedule_ref or "WP-MISC"].append(line)

        lead_schedules: list[LeadScheduleSummary] = []
        for ref, lines in grouped.items():
            category = lines[0].schedule_iii_category or "Unclassified Category"
            acct_type = lines[0].account_type
            is_dr = acct_type in (AccountTypeEnum.ASSET, AccountTypeEnum.EXPENSE)

            tot_unadj = sum(
                l.unadjusted_net_paise if is_dr else -l.unadjusted_net_paise for l in lines
            )
            tot_dr_adj = sum(l.adjustment_dr_paise for l in lines)
            tot_cr_adj = sum(l.adjustment_cr_paise for l in lines)
            tot_net_adj = sum(
                l.net_adjustment_paise if is_dr else -l.net_adjustment_paise for l in lines
            )
            tot_adjusted = sum(
                l.adjusted_net_paise if is_dr else -l.adjusted_net_paise for l in lines
            )

            acc_lines = [
                LeadScheduleAccountLine(
                    account_code=l.account_code,
                    account_name=l.account_name,
                    schedule_iii_line_item=l.schedule_iii_line_item or l.account_name,
                    unadjusted_balance_paise=l.unadjusted_net_paise
                    if is_dr
                    else -l.unadjusted_net_paise,
                    adjustment_dr_paise=l.adjustment_dr_paise,
                    adjustment_cr_paise=l.adjustment_cr_paise,
                    net_adjustment_paise=l.net_adjustment_paise
                    if is_dr
                    else -l.net_adjustment_paise,
                    adjusted_balance_paise=l.adjusted_net_paise if is_dr else -l.adjusted_net_paise,
                    linked_aje_numbers=l.linked_aje_numbers,
                )
                for l in lines
            ]
            lead_schedules.append(
                LeadScheduleSummary(
                    lead_schedule_ref=ref,
                    lead_schedule_name=category,
                    category=category,
                    account_type=acct_type,
                    unadjusted_balance_paise=tot_unadj,
                    adjustment_dr_paise=tot_dr_adj,
                    adjustment_cr_paise=tot_cr_adj,
                    net_adjustment_paise=tot_net_adj,
                    adjusted_balance_paise=tot_adjusted,
                    account_count=len(acc_lines),
                    accounts=acc_lines,
                )
            )

        lead_schedules.sort(key=lambda s: s.lead_schedule_ref)
        return lead_schedules

    def list_adjustments(self, engagement_id: str) -> list[AuditJournalEntry]:
        with self.db_manager.session_scope() as session:
            return AuditAdjustmentRepository(session).list_entries_for_engagement(engagement_id)

    def get_lead_schedule_traceability(
        self, engagement_id: str, lead_schedule_ref: str, dataset_id: str | None = None
    ) -> LeadScheduleTraceDTO:
        """Trace a Lead Schedule down to constituent TB accounts and specific linked AJEs."""
        lead_schedules = self.calculate_lead_schedules(engagement_id, dataset_id)
        matching_ls = next(
            (s for s in lead_schedules if s.lead_schedule_ref == lead_schedule_ref), None
        )
        if not matching_ls:
            raise EntityNotFoundError("LeadSchedule", f"{engagement_id}:{lead_schedule_ref}")

        with self.db_manager.session_scope() as session:
            aje_repo = AuditAdjustmentRepository(session)
            applied_ajes = aje_repo.list_applied_and_approved_entries(engagement_id)

            account_traces: list[AccountTraceDTO] = []
            adj_tb = self.calculate_adjusted_trial_balance(engagement_id, dataset_id)
            tb_line_map = {l.account_code: l for l in adj_tb.lines}

            for acc in matching_ls.accounts:
                line = tb_line_map.get(acc.account_code)
                linked_details: list[dict[str, object]] = []
                for aje in applied_ajes:
                    for l in aje.lines:
                        if l.account_code == acc.account_code:
                            linked_details.append(
                                {
                                    "aje_id": aje.id,
                                    "aje_number": aje.aje_number,
                                    "title": aje.title,
                                    "entry_date": aje.entry_date,
                                    "status": (
                                        aje.status.value
                                        if hasattr(aje.status, "value")
                                        else str(aje.status)
                                    ),
                                    "debit_paise": l.debit_paise,
                                    "credit_paise": l.credit_paise,
                                    "narration": l.narration or aje.narration,
                                }
                            )

                account_traces.append(
                    AccountTraceDTO(
                        account_code=acc.account_code,
                        account_name=acc.account_name,
                        schedule_iii_category=matching_ls.category,
                        schedule_iii_line_item=acc.schedule_iii_line_item,
                        lead_schedule_ref=matching_ls.lead_schedule_ref,
                        unadjusted_dr_paise=line.unadjusted_dr_paise if line else 0,
                        unadjusted_cr_paise=line.unadjusted_cr_paise if line else 0,
                        unadjusted_net_paise=line.unadjusted_net_paise if line else 0,
                        adjustment_dr_paise=line.adjustment_dr_paise if line else 0,
                        adjustment_cr_paise=line.adjustment_cr_paise if line else 0,
                        net_adjustment_paise=line.net_adjustment_paise if line else 0,
                        adjusted_dr_paise=line.adjusted_dr_paise if line else 0,
                        adjusted_cr_paise=line.adjusted_cr_paise if line else 0,
                        adjusted_net_paise=line.adjusted_net_paise if line else 0,
                        linked_ajes=linked_details,
                    )
                )

            return LeadScheduleTraceDTO(
                lead_schedule_ref=matching_ls.lead_schedule_ref,
                lead_schedule_name=matching_ls.lead_schedule_name,
                category=matching_ls.category,
                account_type=(
                    matching_ls.account_type.value
                    if hasattr(matching_ls.account_type, "value")
                    else str(matching_ls.account_type)
                ),
                total_unadjusted_paise=matching_ls.unadjusted_balance_paise,
                total_adjustment_paise=matching_ls.net_adjustment_paise,
                total_adjusted_paise=matching_ls.adjusted_balance_paise,
                accounts=account_traces,
            )

    def get_account_traceability(
        self, engagement_id: str, account_code: str, dataset_id: str | None = None
    ) -> AccountTraceDTO:
        """Trace a specific account code to its TB balance, Schedule III classification, and linked AJEs."""
        adj_tb = self.calculate_adjusted_trial_balance(engagement_id, dataset_id)
        line = next((l for l in adj_tb.lines if l.account_code == account_code), None)
        if not line:
            raise EntityNotFoundError("Account", f"{engagement_id}:{account_code}")

        with self.db_manager.session_scope() as session:
            aje_repo = AuditAdjustmentRepository(session)
            applied_ajes = aje_repo.list_applied_and_approved_entries(engagement_id)
            linked_details: list[dict[str, object]] = []
            for aje in applied_ajes:
                for l in aje.lines:
                    if l.account_code == account_code:
                        linked_details.append(
                            {
                                "aje_id": aje.id,
                                "aje_number": aje.aje_number,
                                "title": aje.title,
                                "entry_date": aje.entry_date,
                                "status": (
                                    aje.status.value
                                    if hasattr(aje.status, "value")
                                    else str(aje.status)
                                ),
                                "debit_paise": l.debit_paise,
                                "credit_paise": l.credit_paise,
                                "narration": l.narration or aje.narration,
                            }
                        )

            return AccountTraceDTO(
                account_code=line.account_code,
                account_name=line.account_name,
                schedule_iii_category=line.schedule_iii_category,
                schedule_iii_line_item=line.schedule_iii_line_item,
                lead_schedule_ref=line.lead_schedule_ref,
                unadjusted_dr_paise=line.unadjusted_dr_paise,
                unadjusted_cr_paise=line.unadjusted_cr_paise,
                unadjusted_net_paise=line.unadjusted_net_paise,
                adjustment_dr_paise=line.adjustment_dr_paise,
                adjustment_cr_paise=line.adjustment_cr_paise,
                net_adjustment_paise=line.net_adjustment_paise,
                adjusted_dr_paise=line.adjusted_dr_paise,
                adjusted_cr_paise=line.adjusted_cr_paise,
                adjusted_net_paise=line.adjusted_net_paise,
                linked_ajes=linked_details,
            )

