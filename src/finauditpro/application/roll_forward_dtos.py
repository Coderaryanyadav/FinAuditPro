"""Data Transfer Objects (DTOs) for Roll Forward and Opening Balance Tie-Out Services."""

from dataclasses import dataclass, field
from finauditpro.domain.roll_forward_entities import OpeningBalanceLink, TieOutSummary


@dataclass
class ExecuteRollForwardDTO:
    source_engagement_id: str
    target_financial_year: str
    performed_by: str
    carry_permanent_documents: bool = True
    carry_risk_register: bool = True
    carry_materiality_methodology: bool = True
    carry_procedures: bool = True
    carry_findings: bool = True
    link_opening_balances: bool = True


@dataclass
class ConfirmTieOutDTO:
    engagement_id: str
    auditor_name: str
