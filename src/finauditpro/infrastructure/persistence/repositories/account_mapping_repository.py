"""Repository managing Account Mapping records, bulk mappings, and mapping history."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.account_mapping_entities import (
    AccountMapping,
    AccountMappingHistory,
    AccountTypeEnum,
    MappingStatusEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.mapping_and_adjustment_models import (
    AccountMappingHistoryModel,
    AccountMappingModel,
)


class AccountMappingRepository:
    """Repository managing Schedule III account mappings and audit trail history."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: AccountMappingModel) -> AccountMapping:
        return AccountMapping(
            id=model.id,
            engagement_id=model.engagement_id,
            account_code=model.account_code,
            account_name=model.account_name,
            schedule_iii_category=model.schedule_iii_category,
            schedule_iii_line_item=model.schedule_iii_line_item,
            lead_schedule_ref=model.lead_schedule_ref,
            account_type=AccountTypeEnum(model.account_type)
            if model.account_type in AccountTypeEnum._value2member_map_
            else AccountTypeEnum.ASSET,
            status=MappingStatusEnum(model.status)
            if model.status in MappingStatusEnum._value2member_map_
            else MappingStatusEnum.UNMAPPED,
            is_material=model.is_material,
            is_new=model.is_new,
            mapped_by=model.mapped_by,
            mapped_at=model.mapped_at.isoformat()
            if isinstance(model.mapped_at, datetime)
            else str(model.mapped_at),
            updated_by=model.updated_by,
            updated_at=model.updated_at.isoformat()
            if isinstance(model.updated_at, datetime)
            else (str(model.updated_at) if model.updated_at else None),
            notes=model.notes,
        )

    def _to_history_entity(self, model: AccountMappingHistoryModel) -> AccountMappingHistory:
        return AccountMappingHistory(
            id=model.id,
            mapping_id=model.mapping_id,
            changed_by=model.changed_by,
            changed_at=model.changed_at.isoformat()
            if isinstance(model.changed_at, datetime)
            else str(model.changed_at),
            previous_category=model.previous_category,
            previous_line_item=model.previous_line_item,
            new_category=model.new_category,
            new_line_item=model.new_line_item,
            reason=model.reason,
        )

    def add_mapping(self, mapping: AccountMapping) -> AccountMapping:
        model = AccountMappingModel(
            id=mapping.id,
            engagement_id=mapping.engagement_id,
            account_code=mapping.account_code,
            account_name=mapping.account_name,
            schedule_iii_category=mapping.schedule_iii_category,
            schedule_iii_line_item=mapping.schedule_iii_line_item,
            lead_schedule_ref=mapping.lead_schedule_ref,
            account_type=mapping.account_type.value
            if hasattr(mapping.account_type, "value")
            else str(mapping.account_type),
            status=mapping.status.value
            if hasattr(mapping.status, "value")
            else str(mapping.status),
            is_material=mapping.is_material,
            is_new=mapping.is_new,
            mapped_by=mapping.mapped_by,
            mapped_at=datetime.fromisoformat(mapping.mapped_at)
            if isinstance(mapping.mapped_at, str)
            else utc_now(),
            updated_by=mapping.updated_by,
            updated_at=datetime.fromisoformat(mapping.updated_at)
            if isinstance(mapping.updated_at, str) and mapping.updated_at
            else None,
            notes=mapping.notes,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def update_mapping(self, mapping: AccountMapping) -> AccountMapping:
        model = self.session.get(AccountMappingModel, mapping.id)
        if not model:
            return self.add_mapping(mapping)

        model.account_name = mapping.account_name
        model.schedule_iii_category = mapping.schedule_iii_category
        model.schedule_iii_line_item = mapping.schedule_iii_line_item
        model.lead_schedule_ref = mapping.lead_schedule_ref
        model.account_type = (
            mapping.account_type.value
            if hasattr(mapping.account_type, "value")
            else str(mapping.account_type)
        )
        model.status = (
            mapping.status.value if hasattr(mapping.status, "value") else str(mapping.status)
        )
        model.is_material = mapping.is_material
        model.is_new = mapping.is_new
        model.updated_by = mapping.updated_by
        model.updated_at = utc_now()
        model.notes = mapping.notes
        self.session.flush()
        return self._to_entity(model)

    def get_mapping_by_id(self, mapping_id: str) -> AccountMapping | None:
        model = self.session.get(AccountMappingModel, mapping_id)
        return self._to_entity(model) if model else None

    def get_mapping_by_account_code(
        self, engagement_id: str, account_code: str
    ) -> AccountMapping | None:
        stmt = select(AccountMappingModel).where(
            AccountMappingModel.engagement_id == engagement_id,
            AccountMappingModel.account_code == account_code,
        )
        model = self.session.scalars(stmt).first()
        return self._to_entity(model) if model else None

    def list_mappings_for_engagement(self, engagement_id: str) -> list[AccountMapping]:
        stmt = (
            select(AccountMappingModel)
            .where(AccountMappingModel.engagement_id == engagement_id)
            .order_by(AccountMappingModel.account_code.asc())
        )
        return [self._to_entity(m) for m in self.session.scalars(stmt).all()]

    def list_unmapped_for_engagement(self, engagement_id: str) -> list[AccountMapping]:
        stmt = (
            select(AccountMappingModel)
            .where(
                AccountMappingModel.engagement_id == engagement_id,
                AccountMappingModel.status == MappingStatusEnum.UNMAPPED.value,
            )
            .order_by(AccountMappingModel.account_code.asc())
        )
        return [self._to_entity(m) for m in self.session.scalars(stmt).all()]

    def add_history(self, history: AccountMappingHistory) -> AccountMappingHistory:
        model = AccountMappingHistoryModel(
            id=history.id,
            mapping_id=history.mapping_id,
            changed_by=history.changed_by,
            changed_at=datetime.fromisoformat(history.changed_at)
            if isinstance(history.changed_at, str)
            else utc_now(),
            previous_category=history.previous_category,
            previous_line_item=history.previous_line_item,
            new_category=history.new_category,
            new_line_item=history.new_line_item,
            reason=history.reason,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_history_entity(model)

    def list_history_for_mapping(self, mapping_id: str) -> list[AccountMappingHistory]:
        stmt = (
            select(AccountMappingHistoryModel)
            .where(AccountMappingHistoryModel.mapping_id == mapping_id)
            .order_by(AccountMappingHistoryModel.changed_at.desc())
        )
        return [self._to_history_entity(m) for m in self.session.scalars(stmt).all()]
