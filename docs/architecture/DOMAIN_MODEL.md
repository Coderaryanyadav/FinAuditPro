# FinAuditPro — Domain Model & Value Objects

## 1. Core Domain Entities & Aggregates

### 1.1 Engagement Aggregate Root
- **Entities:** `Engagement`, `EngagementMember`, `EngagementSetting`, `AuditStage`.
- **Invariants:**
  - An engagement cannot be sealed until all mandatory completion checklist gates and partner sign-offs are valid.
  - A sealed engagement rejects all update, insert, and delete mutations.

### 1.2 Trial Balance & Lead Schedule Aggregate
- **Entities:** `TrialBalance`, `AccountMapping`, `LeadSchedule`, `AdjustmentEntry`.
- **Invariants:**
  - Trial balance net sum of debits minus credits must strictly equal zero paise.
  - Adjustment entries must be double-entry balanced before being posted to the adjusted trial balance.

### 1.3 Working Paper & Procedure Aggregate
- **Entities:** `WorkingPaper`, `AuditProcedure`, `ReviewNote`, `EvidenceAttachment`.
- **Invariants:**
  - A working paper requires two distinct users for Maker and Checker sign-offs.
  - Once signed off by Checker, content fields become immutable unless explicitly reopened by Partner.

### 1.4 Currency Value Object (`Money`)
- Expressed exclusively as integer paise (`1 INR = 100 paise`).
- Arithmetic operations (`+`, `-`, `*`) maintain exact integer precision, preventing rounding anomalies in statutory lead schedules.
