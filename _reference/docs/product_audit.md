# FinAuditPro — Comprehensive Product & Architecture Audit

## 1. Architecture Overview

FinAuditPro is an Enterprise Financial Audit & Assurance Desktop Application built using PySide6 (Qt for Python), SQLAlchemy ORM (SQLite / SQLCipher), and AI Document Intelligence modules.

### High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PySide6 Desktop UI Shell                           │
│ (Main Window, Sidebar Navigation, Header Context Selector, Workspace Panel) │
└──────────────────────┬──────────────────────────────┬───────────────────────┘
                       │                              │
                       ▼                              ▼
┌──────────────────────────────────────────┐ ┌────────────────────────────────┐
│             UI Controllers               │ │      Workflow Engine           │
│ (Dashboard, Clients, Documents, AI,      │ │ (WorkflowState, Progress,      │
│  Statements, Risk, Compliance, WP, Rep)  │ │  Lifecycle Stepper, Guards)    │
└──────────────────────┬───────────────────┘ └────────────────┬───────────────┘
                       │                                      │
                       ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Service Layer                                   │
│ (ClientService, EngagementService, DocumentService, RiskService,            │
│  ComplianceService, FindingService, WorkingPaperService, ReportService)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Repository & Database Layer                            │
│ (ClientRepo, EngagementRepo, RiskRepo, WorkingPaperRepo, SQLAlchemy Base)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Persistence Engine (SQLite DB)                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Application Map & Screen Map

| Screen ID | Screen Name | Class / File | Primary Purpose | Current Status |
|-----------|-------------|--------------|-----------------|----------------|
| SCR-01 | Splash Screen | `SplashScreen` (`src/ui/splash.py`) | Application bootstrap, DB migration, AI pre-flight check | Functional |
| SCR-02 | Login Window | `LoginWindow` (`src/ui/login.py`) | User authentication & role initialization | Functional |
| SCR-03 | Master Dashboard | `DashboardWindow` (`src/ui/dashboard.py`) | Audit overview, active context, workspace stepper, metrics | Functional (Context issue) |
| SCR-04 | Client Management | `ClientsPage` (`src/ui/clients.py`) | Client CRUD, GSTIN/PAN validation, engagement history | Functional |
| SCR-05 | Document Intelligence | `DocumentsPage` (`src/ui/documents.py`) | Audit document upload, OCR status, document viewer | Functional |
| SCR-06 | Financial Statements | `FinancialStatementsPage` (`src/ui/financial_statements.py`) | Trial balance import, FS mapping, balance sheet & P&L review | Partial in-memory |
| SCR-07 | GST Verification | `GSTVerificationPage` (`src/ui/gst_verification.py`) | GSTR-2B vs Purchase Register 2A/2B reconciliation | Partial in-memory |
| SCR-08 | Compliance Checklist | `CompliancePage` (`src/ui/compliance.py`) | Statutory compliance checklist (CARO, Tax Audit, Companies Act) | Functional |
| SCR-09 | Risk & Materiality | `RiskAnalysisPage` (`src/ui/risk_analysis.py`) | Risk matrix, ISA 320 materiality benchmark calculations | Functional |
| SCR-10 | AI Audit Assistant | `AIAnalysisPage` (`src/ui/ai_analysis.py`) | Anomaly detection, document query copilot, finding extraction | Functional |
| SCR-11 | Working Papers | `WorkingPapersPage` (`src/ui/working_papers.py`) | Audit index (A to Z), working paper drafting, review notes | Functional |
| SCR-12 | Audit Reports | `ReportsPage` (`src/ui/reports.py`) | Audit report builder, PDF export, opinion drafting | Functional |
| SCR-13 | Audit History & Logs | `HistoryPage` (`src/ui/history.py`) | Immutable SHA-256 audit trail logs & activity history | Functional |
| SCR-14 | Application Settings | `SettingsPage` (`src/ui/settings.py`) | AI engine setup, firm profile, database encryption | Functional |
| SCR-15 | About Dialog | `AboutDialog` (`src/ui/about_dialog.py`) | Application version, license, system info | Functional |

---

## 3. Workflow & Data-Flow Map

The complete core user audit lifecycle is structured as follows:

```text
[LOGIN] ──► [SELECT / CREATE CLIENT] ──► [CREATE AUDIT ENGAGEMENT]
                                                     │
                                                     ▼
                                          [ACTIVE AUDIT CONTEXT]
                                                     │
         ┌──────────────────┬────────────────────────┼────────────────────────┬──────────────────┐
         ▼                  ▼                        ▼                        ▼                  ▼
   [DOCUMENTS]     [FINANCIAL STMT]           [RISK & MAT.]             [COMPLIANCE]       [AI ANALYSIS]
   Upload PDF/     Import TB & Map            ISA 320 Mat &             Statutory CARO     Anomaly Detect &
   Excel docs      BS / P&L                   Risk Matrix               Checklist          Finding Extract
         │                  │                        │                        │                  │
         └──────────────────┴────────────────────────┼────────────────────────┴──────────────────┘
                                                     ▼
                                          [FINDINGS PERSISTENCE]
                                                     │
                                                     ▼
                                          [WORKING PAPERS INDEX]
                                          Draft WP, Review Notes
                                                     │
                                                     ▼
                                           [REPORT GENERATION]
                                           Compile PDF & Export
                                                     │
                                                     ▼
                                          [AUDIT TRAIL LOGGING]
```

---

## 4. Key Architectural & Technical Debt Findings

1. **Dual Audit Context Models (`AuditProject` vs `Engagement`)**:
   - `src/database/models.py` defines both `Engagement` and `AuditProject`.
   - `Engagement` owns `documents`, `risks`, `compliance_tasks`, `materiality_calculations`, `working_paper_indices`, and `audit_reports`.
   - `AuditProject` owns `findings` and `working_papers` directly via `audit_id`.
   - `DashboardWindow.on_active_engagement_changed` sets `page.active_engagement_id = proj.id` using `AuditProject.id`.
   - **Impact**: Services querying `Engagement` using `active_engagement_id` fail or query wrong records, breaking data synchronization across screens.

2. **In-Memory Trial Balance & GST Reconciliation State**:
   - `FinancialStatementsPage` and `GSTVerificationPage` perform computations in local UI memory without persisting mapped records back to database repositories.

3. **String Parsing for Findings in Working Papers**:
   - Findings stored in `Finding.description` use string delimiters (`"Issue | ₹ 0.00 | ..."`), causing fragile parsing in `risk_analysis.py` and `working_papers.py`.

4. **Hardcoded / Dummy Progress Calculations**:
   - Chart data points in `DashboardWindow` and `AuditWorkspacePanel` fell back to hardcoded arrays instead of calculating real database metrics.

---

## 5. Screen-by-Screen Product Audit Breakdown

### 1. Login Screen
- **PURPOSE**: Authenticate auditor credentials & load user session.
- **PRIMARY USER**: All Audit Staff (Partner, Manager, Assistant).
- **PRIMARY ACTION**: Click "Sign In to FinAuditPro".
- **DATA SOURCE**: `User` database model via `PasswordHasher`.
- **CURRENT UX/FUNCTIONAL ISSUES**: Lacks explicit loading spinner during authentication; password toggle button styling needs polish.
- **REDESIGN PLAN**: Add crisp loading indicator, polish form focus ring, and ensure keyboard Enter submits login cleanly.

### 2. Dashboard Screen
- **PURPOSE**: Master command center for active audit metrics, 16-stage stepper, and quick navigation.
- **PRIMARY USER**: Audit Manager / Partner.
- **PRIMARY ACTION**: Select active audit engagement from top header combo.
- **DATA SOURCE**: `DashboardService`, `Engagement`, `AuditProject`, `Finding`.
- **CURRENT UX/FUNCTIONAL ISSUES**: Dual model ID confusion (`proj.id` vs `engagement.id`); hardcoded trend line numbers.
- **REDESIGN PLAN**: Unify context to `Engagement`, bind chart metrics to real database counts, polish stepper UI.

### 3. Client Management Screen
- **PURPOSE**: View, search, create, and manage audit client profiles.
- **PRIMARY USER**: Audit Assistant / Manager.
- **PRIMARY ACTION**: Click "+ Add New Client" or select client to launch engagement.
- **DATA SOURCE**: `Client` and `ClientIndustry` repositories.
- **CURRENT UX/FUNCTIONAL ISSUES**: Client detail modal lacks tabbed organization for KMP (Key Management Personnel) and GSTIN records.
- **REDESIGN PLAN**: Add structured detail drawer, validate GSTIN/PAN regex inline, improve table density.

### 4. Create Audit / Engagement Dialog
- **PURPOSE**: Define client, financial year (e.g. FY 2024-25), audit type (Statutory, Tax, Internal), and assign team.
- **PRIMARY USER**: Audit Manager / Partner.
- **PRIMARY ACTION**: Click "Create Audit Engagement".
- **DATA SOURCE**: `Engagement`, `FinancialYear`, `AuditTeam`.
- **CURRENT UX/FUNCTIONAL ISSUES**: Duplicate check allows duplicate FY engagements if not validated upfront.
- **REDESIGN PLAN**: Validate unique `(client_id, financial_year_id)` constraint before submission and auto-switch active header context upon creation.

### 5. Documents Intelligence Screen
- **PURPOSE**: Upload, organize, and view audit source documents (PDFs, Excel, Scans).
- **PRIMARY USER**: Articled Assistant.
- **PRIMARY ACTION**: Click "Upload Document" or drag/drop files.
- **DATA SOURCE**: `Document`, `DocumentPage`, file system storage.
- **CURRENT UX/FUNCTIONAL ISSUES**: Document OCR text viewer shows blank if `DocumentPage` is missing; drop zone styling needs visual refinement.
- **REDESIGN PLAN**: Implement dual-pane PDF text viewer with search and status badges (Uploaded, Vectorized, Error).

### 6. Financial Statements Screen
- **PURPOSE**: Trial balance import, financial statement mapping, Balance Sheet & P&L preview.
- **PRIMARY USER**: Audit Senior / Manager.
- **PRIMARY ACTION**: Import Trial Balance CSV/Excel and map accounts.
- **DATA SOURCE**: In-memory QTableWidget & SQLite persistence.
- **CURRENT UX/FUNCTIONAL ISSUES**: Unmapped Trial Balance items don't save back to DB; missing empty state view.
- **REDESIGN PLAN**: Add persistent trial balance mapping, out-of-balance alert banner, and exportable financial statements.

### 7. GST Verification Screen
- **PURPOSE**: Reconcile GSTR-2B monthly data against Purchase Register records.
- **PRIMARY USER**: Audit Associate.
- **PRIMARY ACTION**: Load GSTR-2B & Purchase Register files and click "Run Reconciliation".
- **DATA SOURCE**: In-memory pandas/dict reconciliation.
- **CURRENT UX/FUNCTIONAL ISSUES**: Mismatch summary does not persist across page switches; variance threshold control is missing.
- **REDESIGN PLAN**: Persist GST reconciliation runs, add variance filter tabs (Exact Match, Amount Mismatch, Missing in 2B).

### 8. Compliance Checklist Screen
- **PURPOSE**: Execute statutory compliance checklists (CARO 2020, Companies Act 2013, Tax Audit 44AB).
- **PRIMARY USER**: Audit Senior.
- **PRIMARY ACTION**: Toggle compliance item status (Complied, Not Applicable, Exception).
- **DATA SOURCE**: `ComplianceTask` repository.
- **CURRENT UX/FUNCTIONAL ISSUES**: Changing active audit doesn't reload compliance tasks correctly due to engagement ID context mixup.
- **REDESIGN PLAN**: Bind active `engagement_id`, add clause-by-clause progress bar and remarks field.

### 9. Risk & Materiality Analysis Screen
- **PURPOSE**: Calculate ISA 320 materiality thresholds & evaluate risk matrix.
- **PRIMARY USER**: Audit Manager.
- **PRIMARY ACTION**: Calculate materiality using benchmark % and assess financial risks.
- **DATA SOURCE**: `MaterialityCalculation` & `Risk` models.
- **CURRENT UX/FUNCTIONAL ISSUES**: Materiality calculation values do not auto-save to database upon calculation.
- **REDESIGN PLAN**: Auto-save materiality parameters to `materiality_calculations` table and reflect OM/PM thresholds in working papers.

### 10. AI Analysis Screen
- **PURPOSE**: Run document anomaly scanning, fraud detection rules, and extract audit findings.
- **PRIMARY USER**: Audit Staff & Reviewer.
- **PRIMARY ACTION**: Click "Run Full Audit Scan" and review findings cards.
- **DATA SOURCE**: `FindingService`, AI engine engine, `Finding`.
- **CURRENT UX/FUNCTIONAL ISSUES**: "Add Finding to Working Papers" action does not reliably update the selected working paper index.
- **REDESIGN PLAN**: Wire finding creation directly to `Finding` table and connect each finding to its target Working Paper index (e.g. A-Fixed Assets).

### 11. Working Papers Screen
- **PURPOSE**: Standardized Audit Working Paper file (Index A-Z, procedures, review notes).
- **PRIMARY USER**: Audit Associate & Reviewer.
- **PRIMARY ACTION**: Draft working paper, execute procedures, sign off.
- **DATA SOURCE**: `WorkingPaperIndex`, `WorkingPaper`, `AuditProcedure`, `ReviewNote`.
- **CURRENT UX/FUNCTIONAL ISSUES**: Empty indices do not auto-generate standard ISA working paper structure.
- **REDESIGN PLAN**: Auto-seed standard audit working paper indices (A: Legal, B: Financial Statements, C: Fixed Assets, etc.) per engagement and show sign-off status.

### 12. Reports Screen
- **PURPOSE**: Assemble, preview, and export final Audit Report & Independent Auditor's Opinion.
- **PRIMARY USER**: Audit Partner.
- **PRIMARY ACTION**: Click "Generate Audit Report PDF".
- **DATA SOURCE**: `ReportService`, `AuditReport`, `Engagement`.
- **CURRENT UX/FUNCTIONAL ISSUES**: Executive summary uses generic fallback text instead of aggregating real findings and materiality.
- **REDESIGN PLAN**: Dynamically compile findings, materiality thresholds, and compliance exceptions into the rendered report text and PDF preview.

### 13. Audit History & Audit Trail Screen
- **PURPOSE**: Cryptographically verifiable SHA-256 audit log of all system activities.
- **PRIMARY USER**: Quality Control / Administrator.
- **PRIMARY ACTION**: Filter audit logs by user, action type, or date.
- **DATA SOURCE**: `AuditLog` table.
- **CURRENT UX/FUNCTIONAL ISSUES**: Log table lacks export to CSV capability.
- **REDESIGN PLAN**: Add real-time search, date range filter, and CSV log export.

### 14. Settings Screen
- **PURPOSE**: Configure AI provider (Ollama / OpenAI / Local), firm branding, DB backup & encryption.
- **PRIMARY USER**: Administrator.
- **PRIMARY ACTION**: Test AI connection and save settings.
- **DATA SOURCE**: `ConfigManager` (`src/core/config.py`).
- **CURRENT UX/FUNCTIONAL ISSUES**: AI connection test status indicator needs clear error feedback when connection fails.
- **REDESIGN PLAN**: Add inline connection status badge with response latency test and diagnostic retry button.

### 15. About Dialog
- **PURPOSE**: Display software license, build info, system diagnosis.
- **PRIMARY USER**: All Users.
- **PRIMARY ACTION**: Close dialog.
- **DATA SOURCE**: System metadata.
- **CURRENT UX/FUNCTIONAL ISSUES**: Minor spacing polish needed.
- **REDESIGN PLAN**: Refine typography, padding, and add copyable diagnostic details button.
