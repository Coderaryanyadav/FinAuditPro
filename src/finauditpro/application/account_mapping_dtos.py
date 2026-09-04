"""DTOs for Schedule III Account Mapping and Validation."""

from dataclasses import dataclass

from finauditpro.domain.account_mapping_entities import (
    AccountTypeEnum,
)


@dataclass(frozen=True)
class MapAccountDTO:
    engagement_id: str
    account_code: str
    schedule_iii_category: str
    schedule_iii_line_item: str
    lead_schedule_ref: str
    account_type: AccountTypeEnum = AccountTypeEnum.ASSET
    notes: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class BulkMapAccountsDTO:
    engagement_id: str
    account_codes: list[str]
    schedule_iii_category: str
    schedule_iii_line_item: str
    lead_schedule_ref: str
    account_type: AccountTypeEnum = AccountTypeEnum.ASSET
    notes: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class SyncTrialBalanceAccountsDTO:
    engagement_id: str
    dataset_id: str


@dataclass(frozen=True)
class ValidateMappingsDTO:
    engagement_id: str
    materiality_threshold_paise: int = 0
