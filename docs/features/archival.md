# Engagement Archival, SQC 1 Retention & Multi-Year Roll-Forward

FinAuditPro supports end-of-audit archival sealing and multi-year continuity.

---

## 1. Engagement Archival & SQC 1 Sealing

- **Readiness Checks**: Before sealing, `ArchivalService.check_readiness()` verifies that:
  - All working papers are `SignedOff`
  - Zero open review notes remain
  - All findings are `Reported` or `Closed`
  - The audit report has been approved
- **Cryptographic Archive Packaging**: The engagement's database records, documents, and evidence files are bundled into an encrypted archive with an internal manifest SHA-256 seal.
- **Read-Only SQLite Lock**: Once archived, the active engagement record is locked in `Archived` status and connections are enforced in `PRAGMA query_only = ON` mode.
- **SQC 1 Retention Period**: Retain-until dates are calculated according to SQC 1 rules (typically 7–10 years from the date of the auditor's report).

---

## 2. Multi-Year Engagement Roll-Forward & SA 510 Tie-Out

When rolling forward an engagement to the next financial year (e.g. `FY 2024-25` $\rightarrow$ `FY 2025-26`):
1. **New Engagement Initialized**: Created with `prior_engagement_id` linking back to the sealed prior year engagement.
2. **Carried-Forward Findings**: Unresolved or ongoing control deficiencies are rolled forward with provenance tracking.
3. **SA 510 Opening Balance Tie-Out**: Maps prior year closing trial balance lines to current year opening balances and calculates debit/credit variance in exact integer paise.
