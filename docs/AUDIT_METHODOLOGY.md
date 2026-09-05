# FinAuditPro Audit Methodology & Standards Support

## 1. Overview & Professional Responsibility
FinAuditPro is engineered to support Indian Chartered Accountants in executing statutory audits, tax audits (Form 3CD), internal audits, and CARO 2020 reporting. 

> **Important Statutory Notice**:
> FinAuditPro provides software workflows, mathematical controls, and automated decision-support routines intended to assist the engagement team. It does NOT replace auditor judgment. The Engagement Partner remains solely responsible for audit opinions, evidence sufficiency, and compliance with the Institute of Chartered Accountants of India (ICAI) Standards on Auditing.

---

## 2. Standards on Auditing (SA) Implementation

### SA 320: Materiality in Planning and Performing an Audit
- **Benchmark Selection**: Revenue, Profit Before Tax (PBT), Total Assets, or Gross Margin.
- **Three-Tier Thresholds**:
  - *Overall Materiality (OM)*: Primary benchmark percentage ($0.5\% - 5\%$).
  - *Performance Materiality (PM)*: Typically $50\% - 75\%$ of OM to reduce aggregation risk.
  - *Clearly Trivial Threshold (CTT / SUM)*: Typically $3\% - 5\%$ of OM below which misstatements are not accumulated.

### SA 230: Audit Documentation & Working Papers
- **Maker-Checker Segregation**: Electronic working papers must transition through `Draft` $\rightarrow$ `InReview` $\rightarrow$ `SignedOff`.
- **Self-Review Prevention**: The maker cannot sign off on their own working paper.
- **Review Notes Closure**: An engagement or working paper cannot be signed off with unresolved blocking review notes.
- **Tamper-Evident SHA-256 Digest**: Working paper content and metadata generate an immutable SHA-256 seal.

### SA 510: Initial Audit Engagements — Opening Balances
- **Opening Balance Tie-Out**: Automatic variance reconciliation between prior year audited closing figures and current year opening ledger entries.
- **Discrepancy Highlighting**: Unexplained differences trigger automatic audit findings and review notes.

### SA 450: Evaluation of Misstatements Identified During the Audit
- **Summary of Uncorrected Misstatements (SUM)**: Misstatements classified into Factual, Judgmental, and Projected.
- **Materiality Comparison**: Automatic evaluation against OM and PM with partner sign-off requirements.

### SA 570: Going Concern & SA 560: Subsequent Events
- **Diagnostic Checklists**: Structured statutory questionnaires covering liquidity ratios, operational indicators, and subsequent events prior to report sign-off.

---

## 3. Indian Statutory Reporting (CARO 2020 & Form 3CD)
- **CARO 2020 Checklist**: 21 clauses with structured evidence linking and finding promotion.
- **Form 3CD Tax Audit Engine**: TDS/TCS section compliance, depreciation schedules, and 40A(2)(b) related-party transaction tracking.
- **Schedule III Mapping**: Automated balance sheet and P&L classification conforming to Schedule III of the Companies Act, 2013.
