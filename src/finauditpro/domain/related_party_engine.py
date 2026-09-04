"""Pure domain entities and network graph relationship algorithms for SA 550 Related Parties."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class RelatedPartyCategoryEnum(StrEnum):
    HOLDING_SUBSIDIARY = "Holding / Subsidiary / Associate Entity"
    KEY_MANAGEMENT_PERSONNEL = "Key Management Personnel (KMP) & Directors"
    RELATIVE_OF_KMP = "Relative of Director / KMP"
    COMMON_DIRECTORSHIP_ENTITY = "Enterprise with Common Directorship / Control"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class RelatedPartyEntity(DomainBaseModel):
    """Related party entity declared under Section 188 / AS 18 / Ind AS 24."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    party_name: str = Field(..., min_length=1)
    relationship_category: RelatedPartyCategoryEnum = Field(...)
    pan_or_din: str | None = Field(default=None)
    declared_by_management: bool = Field(default=True)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class RelatedPartyTransaction(DomainBaseModel):
    """Transaction with related party evaluated for arm's length pricing & Section 188 approvals."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    related_party_id: str = Field(...)
    party_name: str = Field(...)
    transaction_nature: str = Field(...)  # e.g. Sale of Goods, Loan, Rent
    amount_paise: int = Field(default=0, ge=0)
    is_at_arms_length: bool = Field(default=True)
    has_audit_committee_approval: bool = Field(default=True)
    has_board_resolution: bool = Field(default=True)
    evidence_reference: str = Field(default="")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class RelatedPartyScanResult:
    total_transactions: int
    unapproved_count: int
    non_arms_length_count: int
    undeclared_vendor_matches: list[dict[str, Any]]
    total_volume_paise: int
    rationale: str


class RelatedPartyEngine:
    """Deterministic detection engine for undisclosed related parties & Section 188 compliance."""

    @classmethod
    def scan_ledger_against_kmp_master(
        cls,
        declared_parties: list[RelatedPartyEntity],
        transactions: list[dict[str, Any]],
        directors_kmp_pans: list[str],
    ) -> RelatedPartyScanResult:
        """Scan general ledger entries against declared RPs and PAN/DIN master to detect unrecorded transactions."""
        known_names = {p.party_name.strip().upper() for p in declared_parties}
        kmp_pans = {p.strip().upper() for p in directors_kmp_pans if p}

        unapproved = 0
        non_arms_len = 0
        undeclared = []
        tot_vol = 0

        for t in transactions:
            acc_name = t.get("account_name", "").strip().upper()
            amt = int(t.get("amount_paise", t.get("amount", 0) * 100))
            pan = t.get("pan", "").strip().upper()
            is_arms = t.get("is_at_arms_length", True)
            has_appr = t.get("has_audit_committee_approval", True)
            tot_vol += amt

            if not is_arms:
                non_arms_len += 1
            if not has_appr:
                unapproved += 1

            # Match against undeclared KMP PANs
            if pan and pan in kmp_pans and acc_name not in known_names:
                undeclared.append(
                    {
                        "account_name": acc_name,
                        "pan": pan,
                        "amount_paise": amt,
                        "reason": f"Account PAN '{pan}' matches Director/KMP Master but is NOT declared in Related Party Register.",
                    }
                )

        summary = (
            f"SA 550 Scan: Evaluated {len(transactions)} transactions. "
            f"Identified {len(undeclared)} undisclosed KMP transaction matches and {unapproved} unapproved Section 188 items."
        )

        return RelatedPartyScanResult(
            total_transactions=len(transactions),
            unapproved_count=unapproved,
            non_arms_length_count=non_arms_len,
            undeclared_vendor_matches=undeclared,
            total_volume_paise=tot_vol,
            rationale=summary,
        )
