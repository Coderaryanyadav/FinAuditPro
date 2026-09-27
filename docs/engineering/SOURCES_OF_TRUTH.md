# FinAuditPro — Canonical Sources of Truth & Multi-Writer Analysis
**Document Reference:** `docs/engineering/SOURCES_OF_TRUTH.md`  
**Classification:** Canonical Architectural Governance & State Integrity  
**Version:** 1.2.0-FORENSIC  
**Date:** 2026-09-27  

---

## Executive Summary

A critical requirement of professional statutory audit software is **unambiguous state ownership**: exactly ONE authoritative source of truth for every business concept. 

This audit identifies all domain entities, financial values, and lifecycle statuses that currently have **multiple competing writers or divergent representations**, and specifies the single canonical authority for each.

---

## 1. Domain State & Writer Integrity Matrix

| Business Concept | Canonical Source of Truth | Competing / Divergent Writers | Inconsistency Risk | Architectural Remediation |
|---|---|---|---|---|
| **SA 320 Materiality (Overall, PM, Trivial)** | `MaterialityAssessmentModel` (via `AuditMatrixService.calculate_materiality()`) | 1. `MaterialityService.calculate()`<br>2. Local UI state in `WorkingPaperView`<br>3. `InspectionView` calculation | Desynchronization between Planning matrix and Workpaper header visibility. | Remove `MaterialityService`. Consolidate all calculations in `AuditMatrixService` using pure `MaterialityEngine`. |
| **Engagement Lifecycle Status** | `EngagementModel.status` managed strictly by `EngagementStateMachine` | 1. `EngagementService.update_engagement()` (direct attribute overwrite)<br>2. Direct SQL in test fixtures<br>3. `CloseWizardDialog` | Illegal state skips (e.g. jumping from *Planning* directly to *Completed* without Fieldwork). | Enforce that `EngagementModel.status` can ONLY be modified via `EngagementService.transition_engagement_status()`. |
| **Audit Findings & Misstatements (SA 450)** | `AuditFindingModel` (`audit_findings` table) | 1. `AuditExceptionModel` (`audit_exceptions` table)<br>2. `AuditMisstatementModel` (`audit_misstatements` table)<br>3. `ExceptionItemModel` (`exceptions` table) | Quadruple representation of audit exceptions with different status lifecycles. | Deprecate `exceptions` and `audit_misstatements` tables; unify into `audit_findings` with clear lifecycle stages (`Exception` $\rightarrow$ `Uncorrected Misstatement` $\rightarrow$ `Corrected via AJE` $\rightarrow$ `Closed`). |
| **Trial Balance Balances & Mapping** | `TrialBalanceLineModel` linked to `AccountMappingModel` | 1. `raw_values_json` in `financial_datasets`<br>2. Ad-hoc Lead Sheet calculations in `WorkingPaperView` | Inconsistent closing balances displayed between `FinancialDataView` and Lead Sheet working papers. | Make `AccountMappingService.get_adjusted_trial_balance()` the sole provider of account closing balances. |
| **Audit Evidence Links** | `EvidenceLinkModel` (`evidence_links` table) | 1. `AuditEvidenceModel` (`audit_evidence` table)<br>2. Markdown embed strings in `working_paper_sections` | Evidence attached to a finding is invisible in the document repository. | Unify all document references into `evidence_links` table with relational foreign keys. |
| **Working Paper Sign-Off State** | `SignOffModel` (`sign_offs` table) | 1. `WorkingPaperModel.status`<br>2. Markdown status badges in `content_markdown` | A working paper marked as "Approved" in the tree without a valid cryptographic partner signature. | Compute `WorkingPaperModel.status` strictly from the latest approved record in `sign_offs`. |
| **Report Generation & Opinions** | `AuditReportWorkpaperModel` (`audit_report_workpapers` table) | 1. `ReportModel` (`reports` table)<br>2. `ReportArtifactModel` | Competing report versioning pipelines. | Consolidate on `AuditReportWorkpaperModel` with SA 700 / 705 / 706 compliance. |

---

## 2. In-Memory Context vs Database State

FinAuditPro maintains an in-memory application singleton: `finauditpro.application.engagement_context.current_context`.

### Governance Rules:
1. **Read Direction:** `current_context` is a read-only mirror of the active `Firm`, `Client`, and `Engagement` entities in SQLite.
2. **Write Rule:** UI components MUST NOT mutate `current_context` directly; all state changes must be committed to the database via Application Services, which then notify `current_context.set_context()`.
3. **Cross-Tenant Safety:** Any switch in `MainWindow`'s active engagement selector must atomically flush `current_context` and notify all 18 subscribed UI views.

---

## 3. Mandatory Single-Writer Enforcement Policies

1. **No Direct SQL Updates:** All database mutations must go through Application Services and Domain State Machines.
2. **Deterministic Monetary Math:** All currency calculations must use pure integer-paise math via domain engines; no floating-point arithmetic allowed in persistence or presentation layers.
3. **Trigger Enforced Append-Only:** Immutability of `audit_events` is physically guaranteed by SQLite database triggers.

---
*Canonical Sources of Truth documented and governed.*
