"""Standard Internal Financial Controls (IFC / ICFR) Catalogue for ICAI-compliant audits.

Pre-configures 12 foundational internal controls spanning 5 key business cycles:
1. Revenue & Receivables (IFC-REV-001 to 003)
2. Procurement & Payables (IFC-PRO-001 to 003)
3. Treasury & Cash Management (IFC-TRE-001 to 002)
4. Payroll & HR Operations (IFC-PAY-001 to 002)
5. Fixed Assets & Depreciation (IFC-FAR-001 to 002)
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ControlFrequencyEnum(StrEnum):
    DAILY = "Daily"
    TRANSACTIONAL = "Transactional"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUAL = "Annual"


class ControlTypeEnum(StrEnum):
    PREVENTIVE = "Preventive"
    DETECTIVE = "Detective"


class ControlTestingResultStatusEnum(StrEnum):
    EFFECTIVE = "Effective"
    DEFICIENCY = "Deficiency"
    SIGNIFICANT_DEFICIENCY = "Significant Deficiency"
    MATERIAL_WEAKNESS = "Material Weakness"


@dataclass
class StandardIFCControl:
    control_id: str
    cycle: str
    title: str
    objective: str
    risk_addressed: str
    control_type: ControlTypeEnum
    frequency: ControlFrequencyEnum
    assertion: str
    testing_procedure: str
    sample_criteria: str
    statutory_ref: str


STANDARD_12_IFC_CONTROLS: list[StandardIFCControl] = [
    # ── 1. REVENUE CYCLE ──────────────────────────────────────────────────────
    StandardIFCControl(
        control_id="IFC-REV-001",
        cycle="Revenue",
        title="Sales Order Authorization & Credit Limit Verification",
        objective="Ensure all sales dispatches are made only against approved sales orders within customer credit limits.",
        risk_addressed="Unauthorized dispatches leading to uncollectible debts or disputed billings.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.TRANSACTIONAL,
        assertion="Occurrence / Rights & Obligations",
        testing_procedure="Sample sales invoices and verify corresponding approved sales order and credit approval timestamp prior to dispatch.",
        sample_criteria="Transactions exceeding credit limits or manual overrides.",
        statutory_ref="SA 315 / Guidance Note on IFC / CARO 2020",
    ),
    StandardIFCControl(
        control_id="IFC-REV-002",
        cycle="Revenue",
        title="3-Way Invoice vs. Proof of Delivery (POD) vs. Customer PO Matching",
        objective="Verify billed quantities and prices agree with customer purchase order and signed acknowledgement.",
        risk_addressed="Premature revenue recognition, billing discrepancies, and fictitious revenue.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.DAILY,
        assertion="Accuracy / Completeness / Occurrence",
        testing_procedure="Perform 3-way match on sales invoice sample against signed POD/e-way bill and customer purchase order.",
        sample_criteria="Top 20 customers by revenue + random statistical sample.",
        statutory_ref="SA 500 / SA 505 External Confirmations",
    ),
    StandardIFCControl(
        control_id="IFC-REV-003",
        cycle="Revenue",
        title="Period-End Revenue Cut-off Verification",
        objective="Ensure revenue is recorded in the correct accounting period around balance sheet date.",
        risk_addressed="Cut-off errors inflating current period turnover.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.QUARTERLY,
        assertion="Cut-Off",
        testing_procedure="Inspect sales invoices and credit notes issued 5 days before and 5 days after March 31st against shipping/gate pass dates.",
        sample_criteria="100% of sales transactions within 5 days of year-end.",
        statutory_ref="SA 240 Intentional Misstatement / SA 560",
    ),

    # ── 2. PROCUREMENT CYCLE ──────────────────────────────────────────────────
    StandardIFCControl(
        control_id="IFC-PRO-001",
        cycle="Procurement",
        title="Purchase Order Authorization & Delegation of Financial Powers (DoFP)",
        objective="Ensure all goods/services purchases are approved per company financial approval hierarchy.",
        risk_addressed="Unauthorized commitments, rogue purchasing, and overspending.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.TRANSACTIONAL,
        assertion="Occurrence / Authorization",
        testing_procedure="Test PO sample against DoFP matrix to verify authorized signatory approval before vendor issuance.",
        sample_criteria="Sample size based on DoFP thresholds (> ₹1,00,000).",
        statutory_ref="Section 134(5)(e) Internal Financial Controls",
    ),
    StandardIFCControl(
        control_id="IFC-PRO-002",
        cycle="Procurement",
        title="Goods Receipt Note (GRN) & Quality Inspection Clearance",
        objective="Ensure raw materials/capital goods are inspected and recorded only upon physical delivery.",
        risk_addressed="Payment for undelivered or substandard goods; inventory misstatements.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.DAILY,
        assertion="Existence / Valuation",
        testing_procedure="Inspect GRN sample and verify physical security gate entry, QC sign-off, and warehouse receipt stamp.",
        sample_criteria="Major supplier deliveries and high-value materials.",
        statutory_ref="CARO 2020 Clause (ii) Physical Verification of Inventory",
    ),
    StandardIFCControl(
        control_id="IFC-PRO-003",
        cycle="Procurement",
        title="Vendor Master Due Diligence & Bank Detail Change Controls",
        objective="Ensure vendor onboarding undergoes KYC/GSTIN verification and bank changes require dual authorization.",
        risk_addressed="Vendor bank diversion, payment redirection, and unauthorized master changes.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.TRANSACTIONAL,
        assertion="Validity / Rights & Obligations",
        testing_procedure="Inspect audit log for all vendor bank account modifications; check independent confirmation calls.",
        sample_criteria="100% of vendor bank modification requests during FY.",
        statutory_ref="SA 240 / Section 143(12) Reporting on Irregularities",
    ),

    # ── 3. TREASURY CYCLE ─────────────────────────────────────────────────────
    StandardIFCControl(
        control_id="IFC-TRE-001",
        cycle="Treasury",
        title="Monthly Bank Reconciliation Timing & Unreconciled Clearance Monitoring",
        objective="Ensure monthly BRS is prepared for all bank accounts within 7 days of month-end with timely clearance of reconciling items.",
        risk_addressed="Misappropriation of funds, unrecorded bank charges, and delayed cheque clearing.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.MONTHLY,
        assertion="Completeness / Accuracy / Existence",
        testing_procedure="Inspect monthly BRS for all bank accounts; verify reconciling items older than 30 days are investigated.",
        sample_criteria="100% of all active bank accounts for 12 months.",
        statutory_ref="SA 505 / SA 500 Audit Evidence",
    ),
    StandardIFCControl(
        control_id="IFC-TRE-002",
        cycle="Treasury",
        title="Dual-Signatory Mandate & Payment Threshold Verification (> ₹5,00,000)",
        objective="Ensure all banking disbursements exceeding designated thresholds require dual authorization.",
        risk_addressed="Single-person embezzlement and unauthorized bank transfers.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.DAILY,
        assertion="Authorization / Occurrence",
        testing_procedure="Inspect bank payment batch approval audit trails and RTGS/NEFT authorizations against bank mandate.",
        sample_criteria="Sample of high-value disbursements > ₹5,00,000.",
        statutory_ref="Section 143(3)(i) IFC / Board Resolution Controls",
    ),

    # ── 4. PAYROLL CYCLE ──────────────────────────────────────────────────────
    StandardIFCControl(
        control_id="IFC-PAY-001",
        cycle="Payroll",
        title="Ghost Employee & Biometric Attendance Cross-Verification",
        objective="Ensure monthly payroll disbursements are made only to active, physically verified employees.",
        risk_addressed="Fictitious personnel, unadjusted leave deductions, and payroll irregularities.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.MONTHLY,
        assertion="Occurrence / Completeness",
        testing_procedure="Cross-match monthly payroll register against biometric access records, active employee master, and bank payout report.",
        sample_criteria="Random sample across departments + all employee exits during FY.",
        statutory_ref="SA 315 / SA 240 Irregularity Detection",
    ),
    StandardIFCControl(
        control_id="IFC-PAY-002",
        cycle="Payroll",
        title="Overtime, Bonus & Variable Compensation Authorization",
        objective="Ensure all variable pay, overtime, and incentive disbursements are approved by Department Head & HR.",
        risk_addressed="Unauthorized compensation increments and budget overruns.",
        control_type=ControlTypeEnum.PREVENTIVE,
        frequency=ControlFrequencyEnum.MONTHLY,
        assertion="Accuracy / Authorization",
        testing_procedure="Verify approval vouchers and HR calculation sheets for all bonus/overtime disbursements.",
        sample_criteria="Top 15% variable pay recipients and overtime samples.",
        statutory_ref="ICAI Framework on Internal Financial Controls",
    ),

    # ── 5. FIXED ASSETS CYCLE ─────────────────────────────────────────────────
    StandardIFCControl(
        control_id="IFC-FAR-001",
        cycle="Fixed Assets",
        title="Physical Fixed Asset Verification & Barcode Tagging Register",
        objective="Ensure physical existence of Property, Plant and Equipment (PPE) reconciles with Fixed Asset Register (FAR).",
        risk_addressed="Unrecorded retirements, scrap pilferage, and obsolete asset carrying value.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.ANNUAL,
        assertion="Existence / Completeness",
        testing_procedure="Inspect annual physical verification report conducted by management; tie out sample tags to FAR.",
        sample_criteria="Physical inspection of top 25 high-value assets + additions.",
        statutory_ref="CARO 2020 Clause (i)(a) & (b) Fixed Asset Maintenance",
    ),
    StandardIFCControl(
        control_id="IFC-FAR-002",
        cycle="Fixed Assets",
        title="Schedule II Depreciation Rate & Useful Life Compliance",
        objective="Ensure depreciation is computed strictly per useful lives specified in Schedule II of Companies Act, 2013.",
        risk_addressed="Depreciation under/overcharge distorting carrying values and P&L.",
        control_type=ControlTypeEnum.DETECTIVE,
        frequency=ControlFrequencyEnum.ANNUAL,
        assertion="Valuation & Allocation / Accuracy",
        testing_procedure="Recalculate depreciation on entire FAR using straight-line / WDV methods based on Schedule II useful lives.",
        sample_criteria="100% recalculation across all PPE categories.",
        statutory_ref="Schedule II Companies Act, 2013 / AS 10 / Ind AS 16",
    ),
]


def get_all_standard_controls() -> list[StandardIFCControl]:
    """Return immutable copy of the standard 12 ICAI IFC controls."""
    return list(STANDARD_12_IFC_CONTROLS)


def get_control_by_id(control_id: str) -> StandardIFCControl | None:
    """Find a standard control by its unique code (e.g. 'IFC-REV-001')."""
    for c in STANDARD_12_IFC_CONTROLS:
        if c.control_id.upper() == control_id.strip().upper():
            return c
    return None
