"""Pure domain entities, deterministic statutory rule engine, and status workflow transitions for Compliance."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ComplianceItemStatusEnum(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CLIENT = "WAITING_FOR_CLIENT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMPLETED = "COMPLETED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class ComplianceItemDTO(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    requirement: str = Field(..., min_length=1)
    statutory_head: str = Field(default="Statutory Compliance")
    rule_code: str = Field(..., min_length=1)
    applicable: bool = Field(default=True)
    applicability_reason: str = Field(default="")
    due_date: str = Field(..., min_length=1)
    status: ComplianceItemStatusEnum = Field(default=ComplianceItemStatusEnum.NOT_STARTED)
    evidence: list[str] = Field(default_factory=list)
    owner: str = Field(default="Auditor")
    reviewer: str = Field(default="Senior Reviewer")
    notes: str = Field(default="")


class ComplianceWorkflowEngine:
    """Deterministic statutory rule engine determining applicability, due dates, and status transition invariants."""

    VALID_TRANSITIONS: dict[ComplianceItemStatusEnum, set[ComplianceItemStatusEnum]] = {
        ComplianceItemStatusEnum.NOT_STARTED: {
            ComplianceItemStatusEnum.IN_PROGRESS,
            ComplianceItemStatusEnum.WAITING_FOR_CLIENT,
            ComplianceItemStatusEnum.NOT_APPLICABLE,
        },
        ComplianceItemStatusEnum.IN_PROGRESS: {
            ComplianceItemStatusEnum.WAITING_FOR_CLIENT,
            ComplianceItemStatusEnum.READY_FOR_REVIEW,
            ComplianceItemStatusEnum.COMPLETED,
            ComplianceItemStatusEnum.NOT_APPLICABLE,
        },
        ComplianceItemStatusEnum.WAITING_FOR_CLIENT: {
            ComplianceItemStatusEnum.IN_PROGRESS,
            ComplianceItemStatusEnum.READY_FOR_REVIEW,
        },
        ComplianceItemStatusEnum.READY_FOR_REVIEW: {
            ComplianceItemStatusEnum.COMPLETED,
            ComplianceItemStatusEnum.IN_PROGRESS,  # Sent back for rework
        },
        ComplianceItemStatusEnum.COMPLETED: {
            ComplianceItemStatusEnum.IN_PROGRESS,  # Reopened
        },
        ComplianceItemStatusEnum.NOT_APPLICABLE: {
            ComplianceItemStatusEnum.NOT_STARTED,
            ComplianceItemStatusEnum.IN_PROGRESS,
        },
    }

    @classmethod
    def validate_status_transition(
        cls, current_status: ComplianceItemStatusEnum, new_status: ComplianceItemStatusEnum
    ) -> bool:
        """Enforce statutory compliance status transition rules."""
        if current_status == new_status:
            return True
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @classmethod
    def determine_compliance_items(
        cls,
        engagement_id: str,
        client_name: str,
        entity_type: str = "PRIVATE_LIMITED",
        turnover_rupees: float = 120000000.0,
        is_listed: bool = False,
        borrowings_rupees: float = 0.0,
        net_worth_rupees: float = 50000000.0,
        net_profit_rupees: float = 10000000.0,
        financial_year: str = "2025-26",
    ) -> list[ComplianceItemDTO]:
        """Deterministically derive statutory compliance requirements and deadlines based on client characteristics."""
        items: list[ComplianceItemDTO] = []
        ent_upper = entity_type.upper()

        # 1. CARO 2020 Compliance
        is_company = "COMPANY" in ent_upper or "LIMITED" in ent_upper
        caro_app = is_listed or (
            is_company
            and not ("PRIVATE" in ent_upper and turnover_rupees <= 100000000.0 and borrowings_rupees <= 10000000.0)
        )
        caro_reason = (
            "Applicable u/s 143(11) for Companies meeting turnover (>₹10 Cr) or borrowing thresholds."
            if caro_app
            else "Exempt: Private company under turnover (≤₹10 Cr) and borrowing (≤₹1 Cr) limits."
        )
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement="CARO 2020 Statutory Audit Reporting (21 Clauses)",
                statutory_head="Companies Act 2013",
                rule_code="CARO_2020",
                applicable=caro_app,
                applicability_reason=caro_reason,
                due_date="2026-09-30",
                status=ComplianceItemStatusEnum.NOT_STARTED if caro_app else ComplianceItemStatusEnum.NOT_APPLICABLE,
            )
        )

        # 2. Form 3CD Tax Audit (u/s 44AB)
        tax_audit_app = turnover_rupees > 10000000.0
        tax_audit_reason = (
            "Applicable u/s 44AB as annual turnover exceeds ₹1 Cr."
            if tax_audit_app
            else "Not applicable: Turnover within presumptive tax limits."
        )
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement="Form 3CD Tax Audit Report & Clause Verification",
                statutory_head="Income Tax Act 1961",
                rule_code="FORM_3CD",
                applicable=tax_audit_app,
                applicability_reason=tax_audit_reason,
                due_date="2026-09-30",
                status=ComplianceItemStatusEnum.NOT_STARTED if tax_audit_app else ComplianceItemStatusEnum.NOT_APPLICABLE,
            )
        )

        # 3. Income Tax Return (ITR-6 / ITR-5)
        itr_due = "2026-10-31" if tax_audit_app else "2026-07-31"
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement=f"Income Tax Return Filing for {financial_year}",
                statutory_head="Income Tax Act 1961",
                rule_code="ITR_FILING",
                applicable=True,
                applicability_reason="Mandatory annual tax return for entity.",
                due_date=itr_due,
                status=ComplianceItemStatusEnum.NOT_STARTED,
            )
        )

        # 4. ROC Financial Statements (Form AOC-4)
        roc_app = is_company
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement="ROC Form AOC-4 (Filing Financial Statements & Notes)",
                statutory_head="Companies Act 2013",
                rule_code="ROC_AOC4",
                applicable=roc_app,
                applicability_reason="Mandatory u/s 137 for all incorporated companies.",
                due_date="2026-10-30",
                status=ComplianceItemStatusEnum.NOT_STARTED if roc_app else ComplianceItemStatusEnum.NOT_APPLICABLE,
            )
        )

        # 5. ROC Annual Return (Form MGT-7)
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement="ROC Form MGT-7 / MGT-7A (Annual Return)",
                statutory_head="Companies Act 2013",
                rule_code="ROC_MGT7",
                applicable=roc_app,
                applicability_reason="Mandatory u/s 92 for all incorporated companies.",
                due_date="2026-11-29",
                status=ComplianceItemStatusEnum.NOT_STARTED if roc_app else ComplianceItemStatusEnum.NOT_APPLICABLE,
            )
        )

        # 6. Section 135 CSR Compliance
        csr_app = is_company and (net_worth_rupees >= 5000000000.0 or turnover_rupees >= 10000000000.0 or net_profit_rupees >= 50000000.0)
        csr_reason = (
            "Applicable u/s 135 as Net Profit >= ₹5 Cr or Net Worth >= ₹500 Cr."
            if csr_app
            else "Exempt: Financial parameters below Section 135 thresholds."
        )
        items.append(
            ComplianceItemDTO(
                engagement_id=engagement_id,
                requirement="Corporate Social Responsibility (Section 135 & Annexure)",
                statutory_head="Companies Act 2013",
                rule_code="SEC_135_CSR",
                applicable=csr_app,
                applicability_reason=csr_reason,
                due_date="2026-03-31",
                status=ComplianceItemStatusEnum.NOT_STARTED if csr_app else ComplianceItemStatusEnum.NOT_APPLICABLE,
            )
        )

        return items
