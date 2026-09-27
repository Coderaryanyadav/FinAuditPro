# FinAuditPro — Non-Negotiable Domain Invariants & Statutory Constraints
**Document Reference:** `docs/engineering/DOMAIN_INVARIANTS.md`  
**Classification:** Canonical Architecture & Statutory Compliance Invariants  
**Version:** 1.2.0-FORENSIC  
**Date:** 2026-09-27  

---

## Executive Summary

This document establishes the **non-negotiable domain invariants** of FinAuditPro. These invariants are absolute rules derived from Indian Auditing Standards (SA 200–SA 700), the Companies Act 2013, Standard on Quality Control (SQC 1), and ethical requirements of the Institute of Chartered Accountants of India (ICAI).

Any code modification that violates these invariants is deemed an architectural and statutory defect.

---

## 1. Ten Core Domain Invariants

```
+------------------------------------------------------------------------------------------------+
|                                    10 DOMAIN INVARIANTS                                        |
+----+--------------------------------------------+----------------------------------------------+
| #  | Domain Invariant                           | Statutory / Technical Basis                  |
+----+--------------------------------------------+----------------------------------------------+
| 1  | Strict Single-Tenant Engagement Isolation  | SA 220 & Client Confidentiality (Code of Ethics)|
| 2  | Working Paper Engagement Ownership         | SA 230 Audit Documentation                    |
| 3  | Bidirectional Evidence Traceability        | SA 500 Audit Evidence                        |
| 4  | Immutable Locked Working Papers            | SQC 1 Retention & Assembly Integrity         |
| 5  | Cryptographically Sealed Finalisation      | Companies Act 2013 Sec 143 & SQC 1           |
| 6  | Deterministic Integer-Paise Math           | Zero Float Rounding Error Guarantee          |
| 7  | AI is Advisory, Never Authoritative        | SA 200 Overall Objectives of the Auditor     |
| 8  | Maker-Checker Segregation of Duties        | SA 220 Quality Control for an Audit          |
| 9  | Mandatory UDIN on Formal Reports           | ICAI Mandatory UDIN Gazette Notification     |
| 10 | Immutable Append-Only Audit Trail          | NFRA & ICAI Peer Review Board (PRB) Integrity|
+----+--------------------------------------------+----------------------------------------------+
```

---

## 2. Detailed Invariant Specifications

### Invariant 1: Strict Single-Tenant Engagement Isolation
- **Rule:** Every audit risk, procedure, working paper, trial balance line, voucher, finding, evidence link, and review note MUST explicitly contain a non-null `engagement_id` foreign key.
- **Enforcement:** Cross-engagement data leaks or aggregate queries across multiple client engagements without explicit firm-wide permission are strictly blocked at repository level.

### Invariant 2: Working Paper Engagement Ownership
- **Rule:** A working paper cannot exist as a standalone document; it must belong to exactly one engagement and one Schedule III index (A-Series to E-Series).
- **Enforcement:** `working_papers.engagement_id` is a `NOT NULL` foreign key with `ON DELETE CASCADE`.

### Invariant 3: Bidirectional Evidence Traceability (SA 500)
- **Rule:** Every substantive testing exception and audit finding exceeding the clearly trivial threshold MUST link to verifiable source evidence (document page, extracted table row, or GL transaction ID).
- **Enforcement:** Unsubstantiated audit findings cannot be marked as "Under Review" or promoted to the final audit report without linked evidence.

### Invariant 4: Immutable Locked Working Papers (SA 230)
- **Rule:** Once a working paper has received Partner Sign-Off or the engagement has entered the `COMPLETED` / `ARCHIVED` status, its content, testing grid, and attached evidence are permanently frozen.
- **Enforcement:** Any attempt to update a locked working paper raises a `DomainError("Cannot edit locked working paper")`. Reopening requires an explicit administrative override logged in `archive_reopen_records`.

### Invariant 5: Cryptographically Sealed Finalisation (SQC 1)
- **Rule:** Finalisation seals the engagement by computing an SHA-256 Merkle-tree digest across all working papers, lead schedules, trial balance lines, and audit events.
- **Enforcement:** The database-level seal is stored in `engagement_archives` and verified by the PRB inspection tool.

### Invariant 6: Deterministic Integer-Paise Math
- **Rule:** All monetary amounts MUST be stored and computed as integer paise ($1\text{ INR} = 100\text{ paise}$).
- **Enforcement:** Floating-point `float` types are strictly forbidden in financial calculations, balances, materiality assessments, and testing grids.

### Invariant 7: AI Is Advisory, Never Authoritative (SA 200)
- **Rule:** AI copilot outputs, suggestions, draft observations, and anomaly scores are strictly assistive. No AI output can automatically sign off a working paper, modify an audit opinion, or close an audit finding without human auditor review.
- **Enforcement:** Every AI run is logged in `ai_runs` with `is_ai_generated = True` and requires explicit practitioner confirmation.

### Invariant 8: Maker-Checker Segregation of Duties (SA 220)
- **Rule:** The preparer of a working paper cannot approve their own work. Review and sign-off require an auditor with Manager or Partner role credentials.
- **Enforcement:** `SignOffDialog` validates that `preparer_user_id != approver_user_id`.

### Invariant 9: Mandatory ICAI UDIN Validation
- **Rule:** Generating a final Independent Auditor's Report (SA 700) requires a valid 18-digit Unique Document Identification Number (UDIN) issued by the ICAI portal matching format `YY[MemberNo]AAAA[XXXX]`.
- **Enforcement:** `AuditReportService` rejects report issuance if the UDIN checksum fails or is missing.

### Invariant 10: Immutable Append-Only Audit Trail
- **Rule:** The `audit_events` table is append-only. No user, administrator, or database operation can modify or delete existing audit events.
- **Enforcement:** SQLite triggers `prevent_audit_events_update` and `prevent_audit_events_delete` raise database-level exceptions on any `UPDATE` or `DELETE` statement.

---
*Domain Invariants formalized and committed.*
