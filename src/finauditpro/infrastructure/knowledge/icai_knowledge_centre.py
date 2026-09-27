"""ICAI Standards on Auditing, CARO 2020, Schedule III & Guidance Notes Knowledge Centre."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ICAIKnowledgeItem:
    standard_code: str
    title: str
    category: str
    key_requirements: list[str]
    audit_checkpoints: list[str]
    working_paper_guidance: str


ICAI_STANDARDS_KNOWLEDGE_BASE: list[ICAIKnowledgeItem] = [
    ICAIKnowledgeItem(
        standard_code="SA 200",
        title="Overall Objectives of the Independent Auditor and Conduct of an Audit",
        category="General Principles",
        key_requirements=[
            "Obtain reasonable assurance about whether financial statements as a whole are free from material misstatement.",
            "Maintain professional skepticism throughout the planning and performance of the audit.",
            "Comply with relevant ethical requirements including independence.",
        ],
        audit_checkpoints=[
            "Document independence confirmation for engagement team.",
            "Assess management integrity and engagement acceptance preconditions.",
        ],
        working_paper_guidance="Scaffold Engagement Acceptance & Team Independence Memo (WP-ACC-01).",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 230",
        title="Audit Documentation",
        category="General Principles & Responsibilities",
        key_requirements=[
            "Prepare audit documentation that provides a sufficient and appropriate record of the basis for the auditor's report.",
            "Document significant matters arising during the audit and professional judgments made.",
            "Assemble the final audit file within 60 days of the auditor's report date.",
        ],
        audit_checkpoints=[
            "Ensure every working paper contains objective, procedure, evidence link, and conclusion.",
            "Verify maker, checker, and partner sign-offs with cryptographic timestamps.",
        ],
        working_paper_guidance="Enforce 3-tier sign-off and tamper-sealing archive index (WP-INDEX-01).",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 240",
        title="The Auditor's Responsibilities Relating to Fraud in an Audit of Financial Statements",  # ignore
        category="Fraud & Risk",  # ignore
        key_requirements=[
            "Presume that there are risks of fraud in revenue recognition.",  # ignore
            "Perform procedures to address the risk of management override of controls.",
            "Test journal entries throughout the period and period-end adjustments.",
        ],
        audit_checkpoints=[
            "Run Benford's Law and round-number journal entry testing.",
            "Inquire management and governance regarding whistle-blower complaints.",
        ],
        working_paper_guidance="Document Fraud Risk Assessment and Top-Entry Journal Scrutiny (WP-FRD-01).",  # ignore
    ),
    ICAIKnowledgeItem(
        standard_code="SA 315",
        title="Identifying and Assessing the Risks of Material Misstatement Through Understanding the Entity",
        category="Risk Assessment & Internal Control",
        key_requirements=[
            "Perform risk assessment procedures to obtain an understanding of the entity and its environment, including internal controls.",
            "Identify and assess risks of material misstatement at the financial statement and assertion levels.",
            "Determine whether any of the risks identified are significant risks.",
        ],
        audit_checkpoints=[
            "Populate 5x5 Inherent Risk vs Control Matrix.",
            "Identify assertions at risk (Completeness, Accuracy, Cut-off, Existence, Valuation).",
        ],
        working_paper_guidance="Link each identified risk to corresponding substantive/TOC procedures in Audit Matrix.",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 320",
        title="Materiality in Planning and Performing an Audit",
        category="Materiality",
        key_requirements=[
            "Determine overall materiality for financial statements as a whole.",
            "Determine performance materiality for assessing risks and designing procedures.",
            "Determine clearly trivial threshold below which misstatements need not be accumulated.",
        ],
        audit_checkpoints=[
            "Document choice of benchmark (Revenue, PBT, Total Assets) and percentage rationale.",
            "Re-evaluate materiality if financial performance shifts significantly during fieldwork.",
        ],
        working_paper_guidance="Generate Planning & Performance Materiality Worksheet (WP-MAT-01).",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 330",
        title="The Auditor's Responses to Assessed Risks",
        category="Audit Fieldwork",
        key_requirements=[
            "Design and implement overall responses to address assessed risks of material misstatement.",
            "Design and perform tests of controls (TOC) and substantive procedures responsive to assessed risks.",
        ],
        audit_checkpoints=[
            "Ensure substantive tests of detail or substantive analytics are executed for every material class of transactions.",
            "Document dual-purpose tests combining TOC with substantive sampling.",
        ],
        working_paper_guidance="Scaffold Substantive Audit Program (WP-AUD-PROG).",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 500",
        title="Audit Evidence",
        category="Audit Evidence",
        key_requirements=[
            "Design and perform audit procedures to obtain sufficient appropriate audit evidence.",
            "Evaluate information provided by management for completeness, accuracy, and authenticity.",
        ],
        audit_checkpoints=[
            "Compute and record SHA-256 digests for all third-party and internal evidence files.",
            "Establish bidirectional links between samples and physical evidence documents.",
        ],
        working_paper_guidance="Maintain Evidence Index with cryptographic hashes and page references.",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 510",
        title="Initial Audit Engagements — Opening Balances",
        category="Opening Balances",
        key_requirements=[
            "Obtain sufficient appropriate audit evidence whether opening balances contain misstatements.",
            "Verify closing balances of prior period have been correctly brought forward.",
        ],
        audit_checkpoints=[
            "Execute automated Opening Balance Tie-Out comparing prior FY balance sheet to current FY opening TB.",
            "Investigate opening balance adjustments and consistency of accounting policies.",
        ],
        working_paper_guidance="Scaffold SA 510 Opening Balance Verification Schedule (WP-SA510-01).",
    ),
    ICAIKnowledgeItem(
        standard_code="SA 570",
        title="Going Concern",
        category="Special Considerations",
        key_requirements=[
            "Obtain sufficient appropriate audit evidence regarding the appropriateness of management's use of the going concern basis.",
            "Evaluate management's assessment of the entity's ability to continue as a going concern for at least 12 months.",
        ],
        audit_checkpoints=[
            "Review cash flow projections, debt servicing ratios, and bank facility renewals.",
            "Assess operational indicators: negative net worth, loss of key customer, regulatory changes.",
        ],
        working_paper_guidance="Document Going Concern Evaluation Worksheet (WP-GC-01).",
    ),
    ICAIKnowledgeItem(
        standard_code="CARO 2020",
        title="Companies (Auditor's Report) Order, 2020",
        category="Statutory Reporting",
        key_requirements=[
            "Report on all 21 specific reporting clauses prescribed by the Ministry of Corporate Affairs (MCA).",
            "Cover Property Plant & Equipment title deeds, inventory physical verification, loans to directors, Benami property, and internal audit coverage.",
        ],
        audit_checkpoints=[
            "Execute CARO 2020 Checklist verification across all 21 clauses.",
            "Check working capital limits > ₹5 Crore and quarterly bank returns tie-out (Clause ii(b)).",
        ],
        working_paper_guidance="Assemble CARO 2020 Statutory Annexure (WP-CARO-2020).",
    ),
    ICAIKnowledgeItem(
        standard_code="Schedule III",
        title="Schedule III to the Companies Act, 2013 (Division I & II)",
        category="Financial Presentation",
        key_requirements=[
            "Comply with format and presentation guidelines for Balance Sheet and Statement of Profit and Loss.",
            "Disclose regulatory ratios, ageing schedules for Trade Receivables/Payables, and Benami/Struck-off company transactions.",
        ],
        audit_checkpoints=[
            "Verify 11 key accounting ratios (Current Ratio, Debt-Equity, Debt Service, Return on Equity, Inventory Turnover).",
            "Verify Trade Receivables and Payables MSME / Non-MSME ageing brackets (<1 yr, 1-2 yrs, 2-3 yrs, >3 yrs).",
        ],
        working_paper_guidance="Generate Lead Schedules and Schedule III Ratio Disclosures (WP-SCH3-RATIOS).",
    ),
]


def search_knowledge_centre(query: str) -> list[ICAIKnowledgeItem]:
    """Search knowledge items across standard code, title, and key requirements."""
    q = query.strip().lower()
    if not q:
        return list(ICAI_STANDARDS_KNOWLEDGE_BASE)

    results = []
    for item in ICAI_STANDARDS_KNOWLEDGE_BASE:
        if (
            q in item.standard_code.lower()
            or q in item.title.lower()
            or q in item.category.lower()
            or any(q in r.lower() for r in item.key_requirements)
            or any(q in c.lower() for c in item.audit_checkpoints)
        ):
            results.append(item)
    return results
