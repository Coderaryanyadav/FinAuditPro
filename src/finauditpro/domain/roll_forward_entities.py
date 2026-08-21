"""Pure domain entities and SA 510 tie-out math for multi-year audit roll-forward."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class OpeningBalanceLink(DomainBaseModel):
    """Entity representing SA 510 opening balance link to prior audited closing balances."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    source_engagement_id: str = Field(...)
    account_code: str = Field(...)
    account_name: str = Field(...)
    opening_dr_paise: int = Field(default=0, ge=0)
    opening_cr_paise: int = Field(default=0, ge=0)
    prior_closing_dr_paise: int = Field(default=0, ge=0)
    prior_closing_cr_paise: int = Field(default=0, ge=0)
    is_tied_out: bool = Field(default=False)
    is_verified_by_auditor: bool = Field(default=False)
    verified_at: str | None = Field(default=None)
    verified_by: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class RollForwardRecord(DomainBaseModel):
    """Entity documenting multi-year audit roll-forward execution and carried items."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    new_engagement_id: str = Field(...)
    source_engagement_id: str = Field(...)
    source_fy: str = Field(...)
    items_carried: list[str] = Field(default_factory=list)
    performed_by: str = Field(...)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class TieOutSummary(DomainBaseModel):
    """Summary entity of SA 510 opening balance tie-out calculations across all accounts."""

    total_accounts: int = Field(default=0)
    tied_out_accounts: int = Field(default=0)
    mismatched_accounts: int = Field(default=0)
    total_opening_dr_paise: int = Field(default=0)
    total_opening_cr_paise: int = Field(default=0)
    total_prior_closing_dr_paise: int = Field(default=0)
    total_prior_closing_cr_paise: int = Field(default=0)
    is_fully_tied_out: bool = Field(default=False)
    is_confirmed_by_auditor: bool = Field(default=False)
    verified_statutory: bool = Field(default=False)


def calculate_opening_tie_out(links: list[OpeningBalanceLink]) -> TieOutSummary:
    """Calculate SA 510 opening balance tie-out summary in paise."""
    total_accounts = len(links)
    tied_out = 0
    mismatched = 0

    tot_op_dr = 0
    tot_op_cr = 0
    tot_cl_dr = 0
    tot_cl_cr = 0
    all_confirmed = True if links else False

    for link in links:
        tot_op_dr += link.opening_dr_paise
        tot_op_cr += link.opening_cr_paise
        tot_cl_dr += link.prior_closing_dr_paise
        tot_cl_cr += link.prior_closing_cr_paise

        is_tied = (
            link.opening_dr_paise == link.prior_closing_dr_paise
            and link.opening_cr_paise == link.prior_closing_cr_paise
        )

        if is_tied:
            tied_out += 1
        else:
            mismatched += 1

        if not link.is_verified_by_auditor:
            all_confirmed = False

    is_fully_tied = (mismatched == 0) and (total_accounts > 0)

    return TieOutSummary(
        total_accounts=total_accounts,
        tied_out_accounts=tied_out,
        mismatched_accounts=mismatched,
        total_opening_dr_paise=tot_op_dr,
        total_opening_cr_paise=tot_op_cr,
        total_prior_closing_dr_paise=tot_cl_dr,
        total_prior_closing_cr_paise=tot_cl_cr,
        is_fully_tied_out=is_fully_tied,
        is_confirmed_by_auditor=all_confirmed,
        verified_statutory=False,  # SA 510 requires auditor confirmation
    )
