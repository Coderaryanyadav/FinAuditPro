# FinAuditPro — Electronic Working Papers & Sampling

## 1. Working Paper Lifecycle (SA 230)
Working papers follow a strict state machine:
`DRAFT -> SUBMITTED -> REVIEWED -> APPROVED -> SEALED`

- **Maker-Checker Segregation:** An author cannot approve their own working paper.
- **Review Notes:** Threaded notes (`OPEN -> ADDRESSED -> CLEARED`) attached to workpaper items.
- **Evidence Linking:** Attachments (PDF/Images) hashed with SHA-256 and linked directly to test steps.

## 2. Sampling Algorithms (SA 530)
- **Monetary-Unit Sampling (MUS):** High-risk substantive testing weighted by voucher value.
- **Stratified Sampling:** High, medium, and low value stratification.
- **Benford's Law Analytics:** First-digit and second-digit anomaly detection on journal vouchers.
