# FinAuditPro — Product Rebuild & Quality Implementation Tasks

This task tracker lists implementation tasks grouped by priority level. Each
task is checked `[x]` only after complete verification.

---

## Phase A: P0 Critical Architectural & Data Fixes

- [x] `TASK-001`: **Unify Active Engagement Context System**
  - Fix `DashboardWindow.on_active_engagement_changed` to map `AuditProject` to
    real `Engagement.id`.
  - Pass `active_engagement_id` consistently across all 12 sub-page modules
    (`documents.py`, `financial_statements.py`, `gst_verification.py`,
    `compliance.py`, `risk_analysis.py`, `ai_analysis.py`, `working_papers.py`,
    `reports.py`, `history.py`).

- [x] `TASK-002`: **Fix AI Findings to Working Papers DB Linkage**
  - Update `AIAnalysisPage` to invoke `FindingService.create_finding()` with
    explicit `working_paper_id` assignment.
  - Wire AI finding cards directly to active working paper indices.

- [x] `TASK-003`: **Implement Trial Balance Account Mapping Persistence**
  - Update `FinancialStatementsPage` to auto-save trial balance account mapping
    choices to persistence layer.
  - Validate debit/credit balancing before enabling financial statement
    compilation.

- [x] `TASK-004`: **Persist GST Reconciliation State**
  - Implement GST reconciliation run persistence in `GSTVerificationPage`.
  - Save mismatch summary and tax variance counts to active engagement context.

- [x] `TASK-005`: **Auto-Save Materiality Calculations**
  - Connect `RiskAnalysisPage` materiality benchmark inputs to
    `RiskService.calculate_materiality()`.
  - Reload saved ISA 320 materiality parameters on engagement switch.

- [x] `TASK-006`: **Dynamic Audit Report Generation Integration**
  - Update `ReportService.generate_report` to aggregate real engagement
    findings, compliance exceptions, and materiality limits into draft report
    text and PDF.

- [x] `TASK-007`: **Fix Document OCR State & Handling**
  - Add graceful missing OCR state handling in `DocumentsPage`.
  - Provide inline "Trigger OCR Processing" action button when document text is
    empty.

- [x] `TASK-008`: **Auto-Seed Standard Working Paper Indices (A to Z)**
  - Update `EngagementService.create_engagement` to automatically seed standard
    ISA working paper index sections (A: Legal/General, B: Financial Statements,
    C: Fixed Assets, D: Inventory, E: Cash & Bank, F: Revenue, G: Expenses, H:
    Tax & Statutory).

- [x] `TASK-009`: **Create Engagement Duplicate Constraint Validation**
  - Add pre-submission validation check in `CreateEngagementDialog` to prevent
    duplicate `(client_id, financial_year_id)` constraint violations.

- [x] `TASK-010`: **Propagate Authenticated User Roles to Workflow Engine**
  - Pass authenticated `User` object and role permissions from `LoginWindow` to
    `WorkflowManager`.

- [x] `TASK-011`: **Persist Compliance Checklist Status**
  - Bind `CompliancePage` checkbox toggles directly to `ComplianceTask`
    repository records.

- [x] `TASK-012`: **Connect Dashboard Analytics to DB Queries**
  - Replace hardcoded trend line arrays and stat metrics with real database
    aggregate queries in `DashboardService`.

- [x] `TASK-013`: **Add Encryption Fallback Check in Settings**
  - Gracefully handle SQLCipher availability check in `db_encryptor.py` and
    `SettingsPage`.

- [x] `TASK-014`: **Link Audit Logs to Active Engagement ID**
  - Update `AuditTrailService.log_action` invocations to record
    `active_engagement_id`.

- [x] `TASK-015`: **Validate Uploaded Document Integrity**
  - Add 0-byte file check and header validation before persisting `Document` DB
    entries.

---

## Phase B: P1 High Priority UX & Component Enhancements

- [x] `TASK-016`: **Dynamic Stepper Progress in Workspace Panel**
  - Highlight current audit lifecycle stage in `AuditWorkspacePanel` stepper
    based on real completion stats.

- [x] `TASK-017`: **Enhance Client Management Search & Filters**
  - Implement case-insensitive search and industry filter dropdown choice.

- [x] `TASK-018`: **Drag & Drop File Upload Visual Feedback**
  - Add active border highlight and hover tint to document upload drop area.

- [x] `TASK-019`: **Refactor Design System Color Tokens**
  - Replace ad-hoc hex colors across UI views with `Colors` design system
    tokens.

- [x] `TASK-020`: **Enable Table Sorting Across Views**
  - Enable sorting by column on Trial Balance, Working Papers, Compliance, and
    Audit History tables.

- [x] `TASK-021`: **Add GST Reconciliation Excel/CSV Export**
  - Add export button to download GST variance breakdown report to CSV.

- [x] `TASK-022`: **Add Statutory Clause Tooltips on Compliance Items**
  - Attach tooltips with statutory clause references (CARO 2020, Companies Act
    2013).

- [x] `TASK-023`: **Persist User Role Reviewer Sign-Offs**
  - Update `WorkingPapersPage` to record user ID and timestamp on procedure
    signoff.

- [x] `TASK-024`: **Auto-Insert Standard Opinion Drafts in Reports**
  - Populate SA 700 / SA 705 draft text when opinion type changes in
    `ReportsPage`.

- [x] `TASK-025`: **Collapsible Navigation Sidebar**
  - Add compact icon-only mode toggle button on left navigation sidebar.

---

## Phase C: P2 Medium Priority Quality & Polish

- [x] `TASK-026`: **Standardize Form Controls & Input Fields**
  - Add uppercase input validator on GSTIN / PAN inputs.
  - Add red asterisk (`*`) for required form fields.

- [x] `TASK-027`: **Custom Empty States Across All Views**
  - Implement explicit empty state illustrations and CTA buttons for empty
    clients, documents, financial statements, and GST lists.

- [x] `TASK-028`: **Format File Sizes and Currency Display**
  - Add human-readable file size formatter (KB, MB) and Indian Rupee currency
    formatter (`₹ #,##,###.00`).

- [x] `TASK-029`: **Table Column Auto-Resizing & Padding**
  - Set explicit column stretch factors and 38px row height in `GLOBAL_QSS`.

- [x] `TASK-030`: **Keyboard Accessibility & Shortcuts**
  - Ensure focus rings on interactive widgets and verify Ctrl+K global search
    popup navigation.

---

## Phase D: Final Verification & End-to-End Test Pass

- [x] `TASK-031`: **Execute 17-Step Core Audit User Journey**
  - Verify complete workflow from Login -> Client -> Engagement -> Upload ->
    Financials -> Risk -> Compliance -> AI -> Working Papers -> Report ->
    Export.

- [x] `TASK-032`: **Run Automated Test Suite & Type Checks**
  - Confirm 100% test pass rate across `pytest` suite.
