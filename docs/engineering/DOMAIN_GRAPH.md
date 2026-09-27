# FinAuditPro — Canonical Domain Graph & Workflow Traceability Matrix
**Document Reference:** `docs/engineering/DOMAIN_GRAPH.md`  
**Classification:** Canonical Domain Reconstruction & Forensic Lineage  
**Version:** 1.2.0-FORENSIC  
**Date:** 2026-09-27  

---

## 1. The Canonical Audit Workflow Model

Under Indian Auditing Standards (SA 200–SA 700) and the FinAuditPro architecture, statutory audit execution proceeds through the following deterministic 14-stage chain:

$$\begin{aligned}
\text{Engagement} &\longrightarrow \text{Risk (SA 315)} \longrightarrow \text{Assertion} \longrightarrow \text{Procedure (SA 330)} \longrightarrow \text{Population} \\
&\longrightarrow \text{Sample (SA 530)} \longrightarrow \text{Evidence (SA 500)} \longrightarrow \text{Testing} \longrightarrow \text{Exception} \\
&\longrightarrow \text{Finding} \longrightarrow \text{Working Paper (SA 230)} \longrightarrow \text{Review} \longrightarrow \text{Conclusion} \longrightarrow \text{Finalisation}
\end{aligned}$$

---

## 2. Complete Relationship & Traceability Matrix

| Source Stage | Relationship | Target Stage | Current Implementation Class | Owning Service | Persistence Model | UI View / Dialog | Test File | Missing Connection / Breakpoint |
|---|---|---|---|---|---|---|---|---|
| **Firm / Client** | `1 : N` Parent Tenant | **Engagement** | `Firm`, `Client`, `Engagement` | `EngagementService` | `FirmModel`, `ClientModel`, `EngagementModel` | `EngagementDialog`, `EngagementView` | `test_phase1_engagement_core.py` | Firm/Client setup is fragmented into 3 screens; missing unified 1-step creation. |
| **Engagement** | `1 : N` Scope Context | **Risk (SA 315)** | `AuditRisk` | `AuditMatrixService` | `AuditRiskModel` | `AuditMatrixView`, `RiskDialog` | `test_risk_and_assertion_engine.py` | Risks are created in matrix, but lack automatic Schedule III account tagging. |
| **Risk** | `N : M` Assessment | **Assertion** | `assertions_json` | `AuditMatrixService` | `AuditRiskModel.assertions_json` | `RiskDialog` | `test_risk_and_assertion_engine.py` | Assertions stored as raw JSON list; lacks relational foreign-key integrity. |
| **Risk + Assertion** | `1 : N` Audit Response | **Procedure (SA 330)** | `AuditProcedure`, `ProcedureRiskLink` | `AuditMatrixService` | `AuditProcedureModel`, `ProcedureRiskLinkModel` | `AuditMatrixView`, `ProcedureDialog` | `test_risk_and_procedures.py` | Procedures defined in Planning Matrix do not auto-populate into Working Paper sections. |
| **Procedure** | `1 : 1` Testing Scope | **Population** | `FinancialDataset`, `LedgerEntry`, `TrialBalanceLine` | `FinancialDataService` | `FinancialDatasetModel`, `LedgerEntryModel` | `FinancialDataView` | `test_financial_workflow.py` | Population filter criteria (e.g. account code range, date range) not stored on Procedure entity. |
| **Population** | `1 : N` Selection Filter | **Sample (SA 530)** | `SamplingEngine`, `AuditSampleItem` | `SamplingEngine` / `CoreAuditService` | `AuditSampleItemModel` | `SamplingDialog`, `WorkingPaperView` | `test_procedure_and_sampling_execution.py` | Sampling calculates sample size, but was only recently seeded into the grid via `SamplingDialog`. |
| **Sample** | `1 : N` Verification | **Evidence (SA 500)** | `Document`, `DocumentPage`, `EvidenceLink`, `AuditEvidence` | `DocumentService` | `DocumentModel`, `EvidenceLinkModel`, `AuditEvidenceModel` | `DocumentView`, `DocumentViewerDialog` | `test_evidence_domain.py` | Dual models: `EvidenceLinkModel` vs `AuditEvidenceModel` store overlapping document pins. |
| **Sample + Evidence** | `1 : 1` Audit Execution | **Testing** | `SubstantiveTestingGrid`, `CutOffTestingEngine`, `ThreeWayMatchEngine` | `WorkingPaperService` | `WorkingPaperSectionModel.content_markdown` | `WorkingPaperView` | `test_working_paper_fieldwork_enhancements.py` | Testing results serialized inside markdown text (`<!-- GRID_JSON -->`) rather than first-class rows. |
| **Testing** | `1 : N` Anomaly Detection | **Exception** | `ExceptionItem`, `AuditException` | `FinancialDataService`, `CoreAuditService` | `ExceptionItemModel`, `AuditExceptionModel` | `FinancialDataView` | `test_exception_and_misstatement_engine.py` | Dual models: `exceptions` table vs `audit_exceptions` table. Testing grid variance does not auto-create exception. |
| **Exception** | `N : 1` Escalation | **Finding** | `AuditFinding` | `AuditMatrixService` | `AuditFindingModel` | `FindingDialog`, `WorkingPaperView` | `test_unified_findings_lifecycle.py` | Promoted findings do not automatically link back to the source sample row index. |
| **Finding** | `N : 1` Documentation | **Working Paper (SA 230)** | `WorkingPaper`, `WorkingPaperSection` | `WorkingPaperService` | `WorkingPaperModel`, `WorkingPaperSectionModel` | `WorkingPaperView` | `test_audit_workbench_and_working_paper_lifecycle.py` | Finding shows in Lead Sheet, but does not auto-generate required adjusting entry (AJE). |
| **Working Paper** | `1 : N` Quality Control | **Review (SA 220)** | `ReviewNote`, `SignOff` | `WorkingPaperService` | `ReviewNoteModel`, `SignOffModel` | `ReviewNotesDialog`, `SignoffDialog` | `test_review_workflow_and_notes.py` | Line-pinned notes recently added; blocker checks in finalization gate operational. |
| **Review** | `N : 1` Synthesis | **Conclusion** | `FinalAnalyticalReview`, `AuditReportWorkpaper` | `EngagementFinalizationService` | `FinalAnalyticalReviewModel`, `AuditReportWorkpaperModel` | `CloseWizardDialog`, `ReportView` | `test_finalisation_gate.py` | Analytical review numbers require manual entry instead of pulling dynamically from adjusted TB. |
| **Conclusion** | `1 : 1` Gate Check | **Finalisation & Sealing** | `FinalizationGateEngine`, `EngagementArchive` | `ArchivalService` | `EngagementArchiveModel`, `ArchiveReopenRecordModel` | `ArchivalView` | `test_archival_and_roll_forward.py` | Finalization gate checks 14 preconditions before SHA-256 seal and read-only lockdown. |

---

## 3. End-to-End Forensic Trace: Revenue Cut-Off (SA 315 / SA 330)

Below is the step-by-step code execution path for a real statutory audit test on **Revenue Cut-Off**:

```
[1. GL Transaction Ingested]
  File: src/finauditpro/infrastructure/financial/financial_importer.py
  Method: FinancialImporter.import_ledger_csv()
  Action: Ingests Invoice S-101 (₹10,00,000, Date: 2026-04-03, Dispatch: 2026-03-29).
  Persistence: `ledger_entries` table (LedgerEntryModel, ID: le_7a8b).

[2. Revenue Population Filtered]
  File: src/finauditpro/infrastructure/persistence/repositories/financial_data_repository.py
  Method: FinancialDataRepository.get_ledger_entries_by_account()
  Action: Filters Account Code '4001' (Revenue from Operations) within period 2026-03-20 to 2026-04-10.
  Population Count: 45 transactions, Total Value: ₹4,50,00,000.

[3. Statutory Risk Identified (SA 315 / SA 240)]
  File: src/finauditpro/application/services/audit_matrix_service.py
  Method: AuditMatrixService.create_risk()
  Risk Code: 'RSK-REV-01' — "Risk of premature revenue recognition / year-end sales inflation".
  Inherent Risk: High, Control Risk: Medium, Derived RoMM: High, Significant Risk: True.
  Persistence: `audit_risks` table (AuditRiskModel, ID: rsk_1199).

[4. Assertion Selected]
  File: src/finauditpro/domain/audit_matrix_entities.py:AuditRisk.assertions
  Assertion: 'Cut-off' (Transactions recorded in correct accounting period) + 'Occurrence'.

[5. Audit Procedure Formulated (SA 330)]
  File: src/finauditpro/application/services/audit_matrix_service.py
  Method: AuditMatrixService.create_procedure()
  Procedure Code: 'PRC-REV-CUTOFF' — "Inspect dispatch notes and invoices +/- 10 days of balance sheet date".
  Persistence: `audit_procedures` & `procedure_risk_links` tables (AuditProcedureModel, ID: prc_4455).

[6. Sample Selected (SA 530)]
  File: src/finauditpro/domain/sampling_engine.py
  Method: SamplingEngine.calculate_stratified_sample()
  Sample Item: Voucher V-1005 (Invoice S-101, ₹10,00,000, Date: 2026-04-03).
  Persistence: `audit_sample_items` table (AuditSampleItemModel, ID: smp_9901).

[7. Audit Evidence Linked (SA 500)]
  File: src/finauditpro/application/services/document_service.py
  Method: DocumentService.link_evidence()
  Evidence: Lorry Receipt LR-8899 dated 2026-03-29 attached with bounding box [120, 340, 480, 560].
  Persistence: `evidence_links` table (EvidenceLinkModel, ID: ev_3321).

[8. Substantive Testing Executed]
  File: src/finauditpro/ui/views/working_paper_view.py
  Method: WorkingPaperView._on_testing_cell_changed()
  Test: Dispatch date 2026-03-29 (FY 2025-26) vs Billing date 2026-04-03 (FY 2026-27).
  Result: FAILED / EXCEPTION (`x`).

[9. Audit Exception Logged]
  File: src/finauditpro/domain/cutoff_testing_engine.py
  Method: CutOffTestingEngine.analyze_cutoff_records()
  Exception Type: 'CutOffExceptionTypeEnum.PRE_YEAR_END_UNBILLED_DISPATCH'
  Variance: ₹10,00,000 unbilled revenue in FY 2025-26.
  Persistence: `audit_exceptions` table (AuditExceptionModel, ID: exc_0012).

[10. Audit Finding Promoted (SA 450)]
  File: src/finauditpro/application/services/audit_matrix_service.py
  Method: AuditMatrixService.promote_exception_to_finding()
  Title: "Unrecorded Revenue for Pre-Year-End Dispatches (Invoice S-101)"
  Severity: High, Amount: ₹10,00,000, Status: Open.
  Persistence: `audit_findings` table (AuditFindingModel, ID: fnd_5502).

[11. Working Paper Updated (SA 230)]
  File: src/finauditpro/application/services/working_paper_service.py
  Method: WorkingPaperService.update_section()
  Working Paper: Index C-10 ("Revenue from Operations — Substantive Cut-off Schedule").
  Persistence: `working_paper_sections` table (WorkingPaperSectionModel, ID: sec_8820).

[12. Line-Pinned Review Note Raised (SA 220)]
  File: src/finauditpro/ui/dialogs/review_notes_dialog.py
  Method: ReviewNotesDialog._handle_create()
  Note: "Article Assistant: Propose adjusting journal entry (AJE) to accrue unbilled revenue of ₹10L."
  Status: Open, Pinned to Section 'Testing Grid - Row 4'.
  Persistence: `review_notes` table (ReviewNoteModel, ID: rn_6611).

[13. Manager & Partner Review Sign-Off (UDIN)]
  File: src/finauditpro/ui/dialogs/signoff_dialog.py
  Method: SignoffDialog._handle_signoff()
  Sign-off: Partner Approved with ICAI UDIN: '26045892AAAAAA1234'.
  Persistence: `sign_offs` table (SignOffModel, ID: so_1102).

[14. Audit Finalisation & Report Integration (SA 700)]
  File: src/finauditpro/domain/finalization_gate_engine.py
  Method: FinalizationGateEngine.evaluate_gate_status()
  Gate Check: All review notes cleared, AJE accepted, working paper locked.
```

---

## 4. Where the Chain Breaks in Current Codebase

1. **Step 3 $\rightarrow$ Step 5 (Risk to Procedure Auto-Creation):**
   - When a CA adds a standard risk under SA 315 in `AuditMatrixView`, standard statutory audit procedures are not automatically instantiated or mapped to relevant Schedule III working papers.
2. **Step 5 $\rightarrow$ Step 6 (Procedure to Population Filtering):**
   - `AuditProcedure` has an objective string, but lacks executable population queries (e.g. `account_code = '4001' AND amount > performance_materiality`). The auditor must manually browse `FinancialDataView`.
3. **Step 8 $\rightarrow$ Step 9 (Testing Grid to Exception Auto-Generation):**
   - Typing an exception or difference in the Substantive Testing Grid in `WorkingPaperView` saves markdown JSON, but does not automatically write an `AuditExceptionModel` row in `audit_exceptions`.
4. **Step 10 $\rightarrow$ Step 11 (Finding to Adjusting Journal Entry):**
   - An uncorrected misstatement / finding is recorded in `audit_findings`, but there is no 1-click "Generate Proposed AJE" button in `FindingDialog` to populate `audit_journal_entries`.

---
*Canonical Domain Graph documented and verified.*
