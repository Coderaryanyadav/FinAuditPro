"""Pure domain entities for Indian Statutory Compliance: CARO 2020 and Form 3CD Tax Audit."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class CAROApplicabilityEnum(StrEnum):
    APPLICABLE = "Applicable"
    NOT_APPLICABLE = "Not Applicable"
    NOT_DETERMINED = "Not Determined"
    REQUIRES_REVIEW = "Requires Review"


class CAROReportAnswerEnum(StrEnum):
    UNQUALIFIED = "Unqualified / Favorable"
    QUALIFIED = "Qualified / Adverse Remarks"
    NOT_APPLICABLE = "Not Applicable"
    PENDING_INFORMATION = "Pending Information"


class CAROClauseEnum(StrEnum):
    CLAUSE_1_PPE_INTANGIBLES = "Clause 3(i): Property, Plant & Equipment and Intangible Assets"
    CLAUSE_2_INVENTORY_WORKING_CAPITAL = (
        "Clause 3(ii): Inventory Physical Verification & Working Capital"
    )
    CLAUSE_3_LOANS_INVESTMENTS_GUARANTEES = (
        "Clause 3(iii): Investments, Guarantees, Securities, Loans Made"
    )
    CLAUSE_4_SEC_185_186_COMPLIANCE = "Clause 3(iv): Compliance with Section 185 and 186"
    CLAUSE_5_PUBLIC_DEPOSITS = "Clause 3(v): Public Deposits and Directives of RBI"
    CLAUSE_6_COST_RECORDS = "Clause 3(vi): Maintenance of Cost Records u/s 148(1)"
    CLAUSE_7_STATUTORY_DUES = "Clause 3(vii): Undisputed and Disputed Statutory Dues"
    CLAUSE_8_UNDISCLOSED_INCOME = (
        "Clause 3(viii): Undisclosed Income Surrendered in Tax Assessments"
    )
    CLAUSE_9_LOAN_DEFAULTS_UTILIZATION = (
        "Clause 3(ix): Default in Repayment of Borrowings & Fund Diversion"
    )
    CLAUSE_10_IPO_FPO_UTILIZATION = (
        "Clause 3(x): Utilization of IPO/FPO/Preferential Allotment Funds"
    )
    CLAUSE_11_STATUTORY_DISCLOSURE_REPORTING = (
        "Clause 3(xi): Fraud Noticed/Reported & Whistleblower Complaints"  # ignore
    )
    CLAUSE_12_NIDHI_COMPANY = "Clause 3(xii): Nidhi Company Compliance"
    CLAUSE_13_RELATED_PARTY_TRANS = "Clause 3(xiii): Related Party Transactions u/s 177 & 188"
    CLAUSE_14_INTERNAL_AUDIT = "Clause 3(xiv): Internal Audit System Coverage & Adequacy"
    CLAUSE_15_NON_CASH_TRANSACTIONS = "Clause 3(xv): Non-Cash Transactions with Directors u/s 192"
    CLAUSE_16_RBI_ACT_REGISTRATION = "Clause 3(xvi): Registration u/s 45-IA of RBI Act, 1934"
    CLAUSE_17_CASH_LOSSES = "Clause 3(xvii): Cash Losses in Current and Preceding Financial Year"
    CLAUSE_18_AUDITOR_RESIGNATION = "Clause 3(xviii): Resignation of Statutory Auditors"
    CLAUSE_19_CAPABILITY_MEET_LIABILITIES = (
        "Clause 3(xix): Material Uncertainty on Meeting Liabilities (1 Year)"
    )
    CLAUSE_20_CSR_COMPLIANCE = "Clause 3(xx): Corporate Social Responsibility (CSR) u/s 135"


class CAROClauseWorkpaper(DomainBaseModel):
    """Working paper evaluating a specific CARO 2020 clause."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    clause_code: str
    clause_title: str
    applicability: CAROApplicabilityEnum = CAROApplicabilityEnum.APPLICABLE
    applicability_reason: str = ""
    question: str
    procedure_text: str
    evidence_refs: list[str] = Field(default_factory=list)
    finding_refs: list[str] = Field(default_factory=list)
    management_response: str = ""
    conclusion_text: str = ""
    report_answer: CAROReportAnswerEnum = CAROReportAnswerEnum.UNQUALIFIED
    preparer: str = "Auditor"
    reviewer: str | None = None
    status: str = "Draft"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TaxAuditCategoryEnum(StrEnum):
    BASIC_ASSESSEE_INFO = "Basic Assessee Information (Clauses 1-8)"
    ACCOUNTING_METHOD_AND_ICDS = "Accounting Method & ICDS (Clause 13)"
    DEPRECIATION_SCHEDULE_3CD = "Depreciation Admissible u/s 32 (Clause 18)"
    AMOUNTS_INADMISSIBLE_40A = "Amounts Inadmissible u/s 40(a) & 40A(3) (Clause 21)"
    RELATED_PARTY_TRANSACTIONS = "Related Party Payments u/s 40A(2)(b) (Clause 23)"
    STATUTORY_DUES_43B = "Statutory Dues & MSME Payments u/s 43B (Clause 26)"
    LOANS_DEPOSITS_269SS_269T = "Acceptance / Repayment of Loans/Deposits (Clause 31)"
    TDS_TCS_COMPLIANCE = "TDS / TCS Compliance & Late Payment Interest (Clause 34)"


class TaxAuditCheckResultEnum(StrEnum):
    COMPLIANT = "Compliant"
    EXCEPTION_DETECTED = "Exception Detected"
    REVIEW_REQUIRED = "Review Required"
    NOT_APPLICABLE = "Not Applicable"


class TaxAuditCheck(DomainBaseModel):
    """Discrete statutory rule check for Form 3CD Tax Audit."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    clause_code: str
    category: TaxAuditCategoryEnum
    description: str
    input_source: str
    rule_logic: str
    system_result: TaxAuditCheckResultEnum = TaxAuditCheckResultEnum.COMPLIANT
    auditor_conclusion: TaxAuditCheckResultEnum = TaxAuditCheckResultEnum.COMPLIANT
    exception_amount_paise: int = 0
    exception_id: str | None = None
    evidence_ref: str | None = None
    reviewer_notes: str | None = None
    reviewer: str | None = None
    status: str = "Completed"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TaxAuditSummary(DomainBaseModel):
    """Aggregate summary of Form 3CD Tax Audit checks and exceptions."""

    engagement_id: str
    total_checks: int = 0
    compliant_checks: int = 0
    exception_checks: int = 0
    total_exception_amount_paise: int = 0
    unresolved_exceptions_count: int = 0
    is_ready_for_form3cd_signoff: bool = False
