"""Application service orchestrating Schedule III Account Mapping, Taxonomies, and Re-import Synchronization."""

from uuid import uuid4

from finauditpro.application.account_mapping_dtos import (
    BulkMapAccountsDTO,
    MapAccountDTO,
    SyncTrialBalanceAccountsDTO,
    ValidateMappingsDTO,
)
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.account_mapping_entities import (
    SCHEDULE_III_TAXONOMY,
    AccountMapping,
    AccountMappingHistory,
    AccountTypeEnum,
    MappingStatusEnum,
    MappingValidationReport,
    ScheduleIIIHead,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
    FinancialDataRepository,
)
from finauditpro.infrastructure.persistence.repositories.account_mapping_repository import (
    AccountMappingRepository,
)


class AccountMappingService:
    """Service managing trial balance account groupings and Schedule III mapping validation."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_taxonomy(self) -> list[ScheduleIIIHead]:
        """Return standard Schedule III taxonomy definitions."""
        return SCHEDULE_III_TAXONOMY

    def initialize_mappings_from_trial_balance(
        self, engagement_id: str, dataset_id: str
    ) -> list[AccountMapping]:
        """Sync unique accounts from imported Trial Balance into Account Mappings."""
        return self.sync_trial_balance_accounts(
            SyncTrialBalanceAccountsDTO(engagement_id=engagement_id, dataset_id=dataset_id)
        )

    def sync_trial_balance_accounts(self, dto: SyncTrialBalanceAccountsDTO) -> list[AccountMapping]:
        """Sync unique accounts from imported Trial Balance into Account Mappings table.

        Preserves existing mappings on re-import and clearly flags newly discovered accounts.
        """
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            fin_repo = FinancialDataRepository(session)
            tb_lines = fin_repo.get_trial_balance_lines(dto.dataset_id)
            if not tb_lines:
                raise ValidationError(
                    f"No trial balance lines found for dataset '{dto.dataset_id}'."
                )

            map_repo = AccountMappingRepository(session)
            existing_mappings = {
                m.account_code: m for m in map_repo.list_mappings_for_engagement(dto.engagement_id)
            }

            synced_mappings: list[AccountMapping] = []
            seen_codes: set[str] = set()

            for line in tb_lines:
                code = line.account_code or f"ACC_{line.source_row_no}"
                if code in seen_codes:
                    continue
                seen_codes.add(code)

                # Determine materiality based on closing balance magnitude (> 0) or period movements
                closing_val = max(line.closing_dr_paise, line.closing_cr_paise)
                movement_val = max(line.debit_paise, line.credit_paise)
                is_material = (closing_val > 0) or (movement_val > 0)

                if code in existing_mappings:
                    # Preserve existing mapping, but update account_name if changed
                    existing = existing_mappings[code]
                    if existing.account_name != line.account_name:
                        existing.account_name = line.account_name
                        map_repo.update_mapping(existing)
                    synced_mappings.append(existing)
                else:
                    # New account introduced in trial balance
                    new_mapping = AccountMapping(
                        id=str(uuid4()),
                        engagement_id=dto.engagement_id,
                        account_code=code,
                        account_name=line.account_name,
                        status=MappingStatusEnum.UNMAPPED,
                        is_material=is_material,
                        is_new=True,
                        mapped_by=actor,
                    )
                    created = map_repo.add_mapping(new_mapping)
                    synced_mappings.append(created)


            # Audit event
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AccountMapping",
                    entity_id=dto.dataset_id,
                    action="TB_ACCOUNTS_SYNCED",
                    payload={"synced_count": len(synced_mappings), "dataset_id": dto.dataset_id},
                    user_id=actor,
                )
            )
            return synced_mappings

    def update_mapping(
        self,
        engagement_id: str,
        account_code: str,
        schedule_iii_category: str,
        schedule_iii_line_item: str,
        lead_schedule_ref: str,
        account_type: AccountTypeEnum = AccountTypeEnum.ASSET,
        reason: str | None = None,
    ) -> AccountMapping:
        """Helper to map/update a single account."""
        return self.map_single_account(
            MapAccountDTO(
                engagement_id=engagement_id,
                account_code=account_code,
                schedule_iii_category=schedule_iii_category,
                schedule_iii_line_item=schedule_iii_line_item,
                lead_schedule_ref=lead_schedule_ref,
                account_type=account_type,
                reason=reason,
            )
        )

    def map_single_account(self, dto: MapAccountDTO) -> AccountMapping:
        """Map a single client ledger account to a Schedule III category and line item."""
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            mapping = map_repo.get_mapping_by_account_code(dto.engagement_id, dto.account_code)
            if not mapping:
                # Create on demand if not present
                mapping = AccountMapping(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    account_code=dto.account_code,
                    account_name=dto.account_code,
                    mapped_by=actor,
                )
                mapping = map_repo.add_mapping(mapping)

            if mapping.status == MappingStatusEnum.LOCKED:
                raise ValidationError(
                    f"Cannot edit locked mapping for account '{dto.account_code}'."
                )

            # Capture history
            history = AccountMappingHistory(
                id=str(uuid4()),
                mapping_id=mapping.id,
                changed_by=actor,
                previous_category=mapping.schedule_iii_category or None,
                previous_line_item=mapping.schedule_iii_line_item or None,
                new_category=dto.schedule_iii_category,
                new_line_item=dto.schedule_iii_line_item,
                reason=dto.reason or "Auditor Schedule III classification update",
            )
            map_repo.add_history(history)

            mapping.apply_mapping(
                category=dto.schedule_iii_category,
                line_item=dto.schedule_iii_line_item,
                lead_schedule_ref=dto.lead_schedule_ref,
                account_type=dto.account_type,
                actor=actor,
                notes=dto.notes,
            )
            return map_repo.update_mapping(mapping)

    def bulk_map_accounts(self, dto: BulkMapAccountsDTO) -> list[AccountMapping]:
        """Bulk map multiple client accounts to the same Schedule III head."""
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            updated_list: list[AccountMapping] = []

            for code in dto.account_codes:
                mapping = map_repo.get_mapping_by_account_code(dto.engagement_id, code)
                if not mapping or mapping.status == MappingStatusEnum.LOCKED:
                    continue

                history = AccountMappingHistory(
                    id=str(uuid4()),
                    mapping_id=mapping.id,
                    changed_by=actor,
                    previous_category=mapping.schedule_iii_category or None,
                    previous_line_item=mapping.schedule_iii_line_item or None,
                    new_category=dto.schedule_iii_category,
                    new_line_item=dto.schedule_iii_line_item,
                    reason=dto.reason or "Bulk Schedule III mapping assignment",
                )
                map_repo.add_history(history)

                mapping.apply_mapping(
                    category=dto.schedule_iii_category,
                    line_item=dto.schedule_iii_line_item,
                    lead_schedule_ref=dto.lead_schedule_ref,
                    account_type=dto.account_type,
                    actor=actor,
                    notes=dto.notes,
                )
                updated = map_repo.update_mapping(mapping)
                updated_list.append(updated)

            return updated_list

    def validate_mappings(self, dto: ValidateMappingsDTO) -> MappingValidationReport:
        """Verify that 100% of material accounts are mapped before audit finalization."""
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            mappings = map_repo.list_mappings_for_engagement(dto.engagement_id)

            total = len(mappings)
            mapped_count = sum(
                1
                for m in mappings
                if m.status in (MappingStatusEnum.MAPPED, MappingStatusEnum.LOCKED)
            )
            unmapped_count = sum(1 for m in mappings if m.status == MappingStatusEnum.UNMAPPED)
            material_unmapped = sum(
                1 for m in mappings if m.status == MappingStatusEnum.UNMAPPED and m.is_material
            )
            new_accounts_count = sum(1 for m in mappings if m.is_new)

            messages: list[str] = []
            if total == 0:
                messages.append("No trial balance accounts found. Import a trial balance first.")
                is_valid = False
            elif material_unmapped > 0:
                messages.append(
                    f"Audit Quality Gate Violation: {material_unmapped} material account(s) are unmapped. "
                    "All material trial balance accounts must be classified under Schedule III."
                )
                is_valid = False
            else:
                messages.append(
                    f"All {mapped_count} trial balance accounts are successfully mapped to Schedule III."
                )
                is_valid = True

            if new_accounts_count > 0:
                messages.append(
                    f"Notice: {new_accounts_count} new account(s) were identified from recent trial balance import."
                )

            return MappingValidationReport(
                total_accounts=total,
                mapped_count=mapped_count,
                unmapped_count=unmapped_count,
                material_unmapped_count=material_unmapped,
                new_accounts_count=new_accounts_count,
                is_valid_for_finalization=is_valid,
                validation_messages=messages,
            )

    def list_mappings(self, engagement_id: str) -> list[AccountMapping]:
        with self.db_manager.session_scope() as session:
            return AccountMappingRepository(session).list_mappings_for_engagement(engagement_id)

    def get_mapping_history(self, mapping_id: str) -> list[AccountMappingHistory]:
        with self.db_manager.session_scope() as session:
            return AccountMappingRepository(session).list_history_for_mapping(mapping_id)

    def lock_mapping(self, engagement_id: str, account_code: str) -> AccountMapping:
        """Lock an account mapping to prevent accidental modifications."""
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            mapping = map_repo.get_mapping_by_account_code(engagement_id, account_code)
            if not mapping:
                raise EntityNotFoundError("AccountMapping", f"{engagement_id}:{account_code}")
            if mapping.status == MappingStatusEnum.UNMAPPED:
                raise ValidationError(f"Cannot lock unmapped account '{account_code}'. Map it first.")
            mapping.lock_mapping(actor)
            updated = map_repo.update_mapping(mapping)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=engagement_id,
                    entity_name="AccountMapping",
                    entity_id=mapping.id,
                    action="ACCOUNT_MAPPING_LOCKED",
                    payload={"account_code": account_code},
                    user_id=actor,
                )
            )
            return updated

    def unlock_mapping(self, engagement_id: str, account_code: str) -> AccountMapping:
        """Unlock a previously locked account mapping for editing."""
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            mapping = map_repo.get_mapping_by_account_code(engagement_id, account_code)
            if not mapping:
                raise EntityNotFoundError("AccountMapping", f"{engagement_id}:{account_code}")
            mapping.status = MappingStatusEnum.MAPPED
            mapping.updated_by = actor
            mapping.updated_at = utc_now().isoformat()
            updated = map_repo.update_mapping(mapping)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=engagement_id,
                    entity_name="AccountMapping",
                    entity_id=mapping.id,
                    action="ACCOUNT_MAPPING_UNLOCKED",
                    payload={"account_code": account_code},
                    user_id=actor,
                )
            )
            return updated

    def mark_review_required(
        self, engagement_id: str, account_code: str, reason: str | None = None
    ) -> AccountMapping:
        """Flag an account mapping as requiring review by senior/partner."""
        actor = SecurityContext.get_current_user_id() or "Auditor"
        with self.db_manager.session_scope() as session:
            map_repo = AccountMappingRepository(session)
            mapping = map_repo.get_mapping_by_account_code(engagement_id, account_code)
            if not mapping:
                raise EntityNotFoundError("AccountMapping", f"{engagement_id}:{account_code}")
            mapping.status = MappingStatusEnum.REVIEW_REQUIRED
            mapping.updated_by = actor
            mapping.updated_at = utc_now().isoformat()
            if reason:
                mapping.notes = f"{mapping.notes or ''} | Review required: {reason}".strip(" |")
            updated = map_repo.update_mapping(mapping)
            AuditEventRepository(session).add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=engagement_id,
                    entity_name="AccountMapping",
                    entity_id=mapping.id,
                    action="ACCOUNT_MAPPING_REVIEW_FLAGGED",
                    payload={"account_code": account_code, "reason": reason},
                    user_id=actor,
                )
            )
            return updated

