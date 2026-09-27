"""Pure domain engine mapping Financial Risks to Relevant Assertions, Recommended Procedures, and Working Paper Templates."""

from dataclasses import dataclass, field
from typing import Any

from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    RiskSeverityEnum,
)


@dataclass(frozen=True)
class ProcedureTemplate:
    code_prefix: str
    title: str
    objective: str
    procedure_type: str
    assertions: list[AssertionEnum]
    instructions: str
    evidence_requirement: str
    population_definition: str
    methodology: str
    working_paper_ref: str
    working_paper_title: str
    wp_sections: list[tuple[int, str, str]] = field(default_factory=list)


AREA_ASSERTIONS_MAP: dict[str, list[AssertionEnum]] = {
    "revenue": [AssertionEnum.OCCURRENCE, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY, AssertionEnum.COMPLETENESS],
    "sales": [AssertionEnum.OCCURRENCE, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY, AssertionEnum.COMPLETENESS],
    "inventory": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.COMPLETENESS, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
    "stock": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.COMPLETENESS, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
    "trade receivables": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
    "debtors": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
    "fixed assets": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.RIGHTS_AND_OBLIGATIONS, AssertionEnum.COMPLETENESS],
    "ppe": [AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.RIGHTS_AND_OBLIGATIONS, AssertionEnum.COMPLETENESS],
    "cash & bank": [AssertionEnum.EXISTENCE, AssertionEnum.COMPLETENESS, AssertionEnum.VALUATION],
    "bank": [AssertionEnum.EXISTENCE, AssertionEnum.COMPLETENESS, AssertionEnum.VALUATION],
    "trade payables": [AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY],
    "creditors": [AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY],
    "purchases": [AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY, AssertionEnum.OCCURRENCE],
    "borrowings": [AssertionEnum.COMPLETENESS, AssertionEnum.RIGHTS_AND_OBLIGATIONS, AssertionEnum.PRESENTATION],
    "loans": [AssertionEnum.COMPLETENESS, AssertionEnum.RIGHTS_AND_OBLIGATIONS, AssertionEnum.PRESENTATION],
    "payroll": [AssertionEnum.OCCURRENCE, AssertionEnum.COMPLETENESS, AssertionEnum.ACCURACY],
    "expenses": [AssertionEnum.OCCURRENCE, AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF, AssertionEnum.ACCURACY],
}

STANDARD_PROCEDURE_CATALOGUE: list[ProcedureTemplate] = [
    # --- REVENUE ---
    ProcedureTemplate(
        code_prefix="PROC-REV-CUTOFF",
        title="Revenue Cut-off Testing",
        objective="Verify that sales invoices and credit notes recorded around year-end belong to the correct accounting period (SA 500 / Ind AS 115).",
        procedure_type="Substantive Cut-off Testing",
        assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
        instructions="Select 100% of sales transactions 15 days before and 15 days after balance sheet date. Inspect dispatch notes (e-Way bills, bilty, goods dispatch notes) and ensure billing dates match delivery/risk transfer dates.",
        evidence_requirement="Sales Invoices, Goods Dispatch Notes (GDN), Transporter Bilty / e-Way Bills, Sales Return Register.",
        population_definition="General Ledger Sales Register transactions from 15 days prior to 15 days post financial year end.",
        methodology="SA 530 Targeted Sample + 100% Threshold Testing around year-end cutoff window.",
        working_paper_ref="WP-REV-CUTOFF",
        working_paper_title="Revenue Cut-off Testing & Dispatch Verification Schedule",
        wp_sections=[
            (1, "1. Cut-off Sample Selection", "Record the threshold and selected transactions 15 days prior and post year-end."),
            (2, "2. Dispatch & Invoicing Matching", "Verify date of invoice vs date of e-Way bill / LR / Proof of Delivery."),
            (3, "3. Exceptions & Unrecorded Returns", "Note any misstated periods and required cutoff adjustments."),
        ],
    ),
    ProcedureTemplate(
        code_prefix="PROC-REV-OCCUR",
        title="Substantive Testing of Revenue Occurrence and Pricing",
        objective="Ensure recorded revenue transactions represent genuine sales of goods/services rendered at authorized contract prices.",
        procedure_type="Substantive Test of Details",
        assertions=[AssertionEnum.OCCURRENCE, AssertionEnum.ACCURACY],
        instructions="Sample sales entries exceeding performance materiality. Agree to customer purchase order, delivery proof, tax invoice, and GST GSTR-1 filings.",
        evidence_requirement="Customer Purchase Orders, GST Invoices, Proof of Delivery, Bank Inward Remittance Advices.",
        population_definition="Full Year General Ledger Sales Register.",
        methodology="Monetary Unit Sampling (MUS) based on SA 320 Performance Materiality.",
        working_paper_ref="WP-REV-OCCUR",
        working_paper_title="Revenue Substantive Voucher Audit Schedule",
        wp_sections=[
            (1, "1. Sampling Methodology", "Document sampling parameters, high-value threshold, and random sample selection."),
            (2, "2. Vouching & 3-Way Match", "Cross-verify PO, Invoice, Delivery Chalan, and GSTR-1."),
            (3, "3. Pricing & Tax Calculations", "Verify GST rate compliance and arithmetic accuracy."),
        ],
    ),
    # --- TRADE RECEIVABLES ---
    ProcedureTemplate(
        code_prefix="PROC-REC-CONF",
        title="Trade Receivables SA 505 External Balance Confirmation",
        objective="Obtain direct third-party balance confirmations from significant debtors (SA 505) to verify existence and valuation.",
        procedure_type="Substantive External Confirmation",
        assertions=[AssertionEnum.EXISTENCE, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
        instructions="Send positive confirmation requests to all debtors > 5% of total receivables and a random sample of other accounts. Reconcile differences.",
        evidence_requirement="Signed Confirmation Letters, Postal/Email tracking logs, Debtor Ledger extracts.",
        population_definition="Debtors Sub-ledger as at balance sheet date.",
        methodology="Stratified Sampling (> Top 70% value + random selection).",
        working_paper_ref="WP-REC-CONF",
        working_paper_title="Trade Receivables Confirmation Control & Reconciliation Schedule",
        wp_sections=[
            (1, "1. Confirmation Dispatch Control", "Log of confirmation requests sent, dispatch method, and dates."),
            (2, "2. Responses & Reconciliations", "Direct replies received, confirmations agreed, and disputed balances."),
            (3, "3. Alternative Audit Procedures", "Subsequent receipts testing for non-responses."),
        ],
    ),
    # --- INVENTORY ---
    ProcedureTemplate(
        code_prefix="PROC-INV-COUNT",
        title="Physical Inventory Observation and Valuation (SA 501)",
        objective="Observe physical stock taking, test count accuracy, and evaluate inventory valuation at lower of cost or NRV (AS 2 / Ind AS 2).",
        procedure_type="Physical Inspection & Test of Details",
        assertions=[AssertionEnum.EXISTENCE, AssertionEnum.VALUATION],
        instructions="Attend physical verification on or near year-end. Perform test counts, inspect slow-moving/damaged stock, and test cost vs NRV valuation.",
        evidence_requirement="Physical Verification Count Sheets, Stock Summary Report, Cost Calculation Sheets, Recent Selling Price Invoices.",
        population_definition="Perpetual Stock Register & Warehouse Inventory Summary.",
        methodology="SA 501 Observation + ABC Stratification Sample.",
        working_paper_ref="WP-INV-COUNT",
        working_paper_title="Physical Stock Verification & NRV Testing Working Paper",
        wp_sections=[
            (1, "1. Physical Count Observation", "Observations on client's count procedures, controls, and test counts."),
            (2, "2. Cost vs NRV Valuation Test", "Comparison of carrying unit cost with post-period selling prices."),
            (3, "3. Slow-Moving & Obsolete Provisions", "Assessment of provisioning requirements."),
        ],
    ),
    # --- CASH & BANK ---
    ProcedureTemplate(
        code_prefix="PROC-BNK-RECON",
        title="Bank Reconciliation & Direct Confirmation Verification",
        objective="Verify 100% bank reconciliations and agree balances with direct bank confirmation certificates.",
        procedure_type="Substantive Test of Details & Confirmation",
        assertions=[AssertionEnum.EXISTENCE, AssertionEnum.COMPLETENESS, AssertionEnum.VALUATION],
        instructions="Obtain bank statements, bank confirmation letters, and BRS for all accounts. Trace uncredited deposits and unpresented cheques to subsequent clearance.",
        evidence_requirement="Bank Statements, Bank Confirmation Certificates, BRS Statements, Subsequent Month Statements.",
        population_definition="All active and dormant bank accounts maintained during the financial year.",
        methodology="100% Substantive Verification across all bank accounts.",
        working_paper_ref="WP-BNK-RECON",
        working_paper_title="Bank Reconciliations & SA 505 Confirmation Schedule",
        wp_sections=[
            (1, "1. Bank Account Summary", "List of all accounts, GL balance, statement balance, and confirmation balance."),
            (2, "2. BRS Item Verification", "Detailed testing of old uncleared items > 30 days."),
            (3, "3. Subsequent Clearance Testing", "Trace clearance of unpresented cheques in April/May."),
        ],
    ),
    # --- TRADE PAYABLES & PURCHASES ---
    ProcedureTemplate(
        code_prefix="PROC-PAY-UNREC",
        title="Search for Unrecorded Liabilities and Purchase Cut-off",
        objective="Identify unrecorded trade payables and expenses (Completeness & Cut-off) around year-end.",
        procedure_type="Substantive Search for Unrecorded Liabilities",
        assertions=[AssertionEnum.COMPLETENESS, AssertionEnum.CUT_OFF],
        instructions="Inspect subsequent bank payments and vendor invoices received post year-end. Cross-check against goods inward notes dated on or before balance sheet date.",
        evidence_requirement="Subsequent Cash/Bank Disbursals, April/May Vendor Invoices, GRN (Goods Received Notes) Register, GSTR-2B.",
        population_definition="Post-balance sheet payment vouchers and April/May vendor invoices.",
        methodology="100% test of payments > threshold in subsequent 45 days.",
        working_paper_ref="WP-PAY-UNREC",
        working_paper_title="Search for Unrecorded Liabilities & Purchase Cut-off Schedule",
        wp_sections=[
            (1, "1. Subsequent Payments Log", "Sample of payments made post balance sheet date."),
            (2, "2. GRN & Period Matching", "Verification of corresponding GRN dates vs liability booking."),
            (3, "3. Identified Unrecorded Liabilities", "Summary of unrecorded accruals requiring adjustment."),
        ],
    ),
    # --- FIXED ASSETS ---
    ProcedureTemplate(
        code_prefix="PROC-FA-ADD",
        title="Fixed Assets Additions, Physical Existence & Depreciation Audit",
        objective="Verify additions to Property, Plant & Equipment, evaluate capitalisation criteria (AS 10 / Ind AS 16), and recalculate depreciation.",
        procedure_type="Substantive Test of Details & Recalculation",
        assertions=[AssertionEnum.EXISTENCE, AssertionEnum.VALUATION, AssertionEnum.RIGHTS_AND_OBLIGATIONS],
        instructions="Vouch additions > materiality threshold to vendor invoices, title deeds, installation certificates. Recalculate depreciation per Companies Act Schedule II.",
        evidence_requirement="Fixed Asset Register (FAR), Purchase Invoices, Title Deeds/RTO Registration, Depreciation Calculation Sheet.",
        population_definition="Fixed Asset Register additions and depreciation schedule for the year.",
        methodology="100% vouching of additions above threshold + Depreciation model recalculation.",
        working_paper_ref="WP-FA-ADD",
        working_paper_title="Fixed Assets Vouching, Title Deeds & Depreciation Schedule",
        wp_sections=[
            (1, "1. Additions Vouching Schedule", "Review of capitalisation invoices and installation certificates."),
            (2, "2. Depreciation Recalculation", "Audit recalculation of useful lives and depreciation rates under Schedule II."),
            (3, "3. Physical Verification & Impairment", "Review of management's physical verification report."),
        ],
    ),
]


class RiskProcedureEngine:
    """Pure domain engine connecting financial areas & risks to assertions, procedures, and working papers."""

    @staticmethod
    def get_relevant_assertions(area: str, category: str = "") -> list[AssertionEnum]:
        """Determine relevant audit assertions based on financial statement area."""
        normalized_area = area.strip().lower()
        for key, assertions in AREA_ASSERTIONS_MAP.items():
            if key in normalized_area or normalized_area in key:
                return assertions
        norm_cat = category.strip().lower()
        for key, assertions in AREA_ASSERTIONS_MAP.items():
            if key in norm_cat or norm_cat in key:
                return assertions
        return [
            AssertionEnum.COMPLETENESS,
            AssertionEnum.ACCURACY,
            AssertionEnum.EXISTENCE,
            AssertionEnum.VALUATION,
        ]

    @staticmethod
    def get_recommended_procedures(
        area: str,
        risk_category: str = "",
        assertions: list[AssertionEnum] | None = None,
        romm: RiskSeverityEnum = RiskSeverityEnum.MEDIUM,
    ) -> list[ProcedureTemplate]:
        """Recommend specific substantive audit procedures tailored to the area, risk, and assertions."""
        search_keys = [area.strip().lower(), risk_category.strip().lower()]
        matched: list[ProcedureTemplate] = []

        for proc in STANDARD_PROCEDURE_CATALOGUE:
            # Match by area or keyword in title/objective
            is_area_match = any(
                (k in proc.title.lower() or k in proc.objective.lower() or k in proc.working_paper_title.lower())
                for k in search_keys
                if k
            )
            # Match by assertions overlap
            is_assertion_match = False
            if assertions:
                is_assertion_match = any(a in proc.assertions for a in assertions)

            if is_area_match or (is_assertion_match and not any(k in ("revenue", "inventory", "bank", "fixed asset") for k in search_keys)):
                matched.append(proc)

        # If no direct match, return standard general procedures
        if not matched:
            for proc in STANDARD_PROCEDURE_CATALOGUE:
                if assertions and any(a in proc.assertions for a in assertions):
                    matched.append(proc)
            if not matched:
                matched = STANDARD_PROCEDURE_CATALOGUE[:2]

        return matched
