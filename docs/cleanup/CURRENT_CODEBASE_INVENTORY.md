# FinAuditPro — Current Codebase Inventory (Phase 1)

> **Repository State:** Current Working Tree / HEAD (`4f966d5`)  
> **Total Source Python Files:** 273 files  
> **Total Test Suites:** 95 test modules (414 passing tests)  
> **Evaluation Date:** 2026-09-27  

---

## 1. Architectural Module Inventory

### 1.1 Domain Core Layer (`src/finauditpro/domain/`)
The domain layer encapsulates pure statutory audit business rules, value objects, domain invariants, and mathematical formulas with zero external dependencies.

| Module Path | Purpose | Key Public Interfaces | Tests | Status |
| :--- | :--- | :--- | :--- | :---: |
| `domain/entities.py` | Core domain entities (Firm, Client, Engagement, User, AuditEvent) | `Firm`, `Client`, `Engagement`, `User`, `AuditEvent` | `test_domain.py`, `test_phase1_engagement_core.py` | **CORE** |
| `domain/value_objects.py` | Integer-paise Money value object and currency math | `Money`, `Currency`, `RoundingMode` | `test_value_objects.py`, `test_domain.py` | **CORE** |
| `domain/engagement_state_machine.py` | Engagement lifecycle state transitions and rules | `EngagementStateMachine`, `EngagementStatusEnum` | `test_engagement_centric_kernel.py` | **CORE** |
| `domain/audit_execution_entities.py` | Materiality, sampling, and substantive procedure models | `MaterialityThresholds`, `SamplingParameters`, `AuditRisk` | `test_materiality.py`, `test_sampling_engine.py` | **CORE** |
| `domain/audit_matrix_entities.py` | Risk-to-procedure matrix and assertions | `AuditMatrixEntry`, `AssertionEnum`, `RiskLevel` | `test_audit_matrix_service.py` | **CORE** |
| `domain/evidence_state_machine.py` | Evidence lifecycle, SHA-256 verification, provenance | `EvidenceStateMachine`, `EvidenceStatusEnum` | `test_evidence_domain.py` | **CORE** |
| `domain/working_paper_entities.py` | Electronic working paper aggregate, versions, maker-checker | `WorkingPaper`, `ReviewNote`, `SignOffBlock` | `test_working_paper_lifecycle.py` | **CORE** |
| `domain/financial_entities.py` | Trial balances, general ledger vouchers, account mappings | `TrialBalance`, `LedgerEntry`, `AccountMapping` | `test_trial_balance_invariants.py` | **CORE** |
| `domain/methodology_catalog.py` | Catalog of ICAI Standards on Auditing (SA 200–SA 700) | `get_sa_standards_catalog`, `SAMethodologyStandard` | `test_audit_methodology_layer.py` | **CORE** |
| `domain/methodology_statutory_catalog.py` | CARO 2020 21 clauses and Form 3CD 44 clauses | `get_caro_2020_catalog`, `get_form_3cd_catalog` | `test_caro_workflow.py`, `test_tax_audit_form_3cd.py` | **CORE** |
| `domain/finalization_gate_engine.py` | Deterministic completion gates and blockers | `FinalizationGateEngine`, `GateCheckResult` | `test_finalisation_gate.py` | **CORE** |
| `domain/reporting_consistency_engine.py` | Audit opinion evaluation and report consistency | `ReportingConsistencyEngine`, `OpinionTypeEnum` | `test_opinion_decision_support_and_consistency.py` | **CORE** |
| `domain/roll_forward_entities.py` | Multi-year balance roll-forward & finding carrying | `RollForwardPackage`, `CarriedFinding` | `test_archival_and_roll_forward.py` | **CORE** |
| `domain/exceptions.py` | Typed domain exception hierarchy | `FinAuditProException`, `DomainInvariantError`, `EntityNotFoundError` | Unit test suites | **CORE** |

---

### 1.2 Application Service Layer (`src/finauditpro/application/`)
Orchestrates domain logic, executes use cases, enforces RBAC, and coordinates transactions.

| Module Path | Purpose | Key Public Interfaces | Tests | Status |
| :--- | :--- | :--- | :--- | :---: |
| `application/services/engagement_service.py` | Manages 3-tier Firm -> Client -> Engagement operations | `EngagementService` | `test_engagement_centric_kernel.py` | **CORE** |
| `application/services/financial_service.py` | Trial balance ingestion, lead schedule assembly | `FinancialService` | `test_financial_services.py`, `test_financial_workflow.py` | **CORE** |
| `application/services/audit_planning_service.py` | Materiality determination and procedure planning | `AuditPlanningService` | `test_materiality_engine.py` | **CORE** |
| `application/services/audit_matrix_service.py` | Matrix risk-to-assertion orchestration | `AuditMatrixService` | `test_audit_matrix_service.py` | **CORE** |
| `application/services/working_paper_service.py` | Working paper creation, review notes, maker-checker sign-off | `WorkingPaperService` | `test_working_paper_lifecycle.py` | **CORE** |
| `application/services/evidence_service.py` | Evidence intake, SHA-256 validation, document linking | `EvidenceService` | `test_evidence_domain.py`, `test_evidence_links.py` | **CORE** |
| `application/services/methodology_service.py` | Standards execution, CARO 2020 & 3CD clause evaluations | `MethodologyService` | `test_audit_methodology_layer.py` | **CORE** |
| `application/services/engagement_finalization_service.py` | Pre-release gates, opinion support, SQC 1 sealing | `EngagementFinalizationService` | `test_finalisation_gate.py` | **CORE** |
| `application/services/ai_copilot_service.py` | Bounded local RAG copilot with prompt defenses | `AICopilotService` | `test_ai_copilot.py` | **CORE** |
| `application/services/roll_forward_service.py` | Prior year opening balance tie-out & roll forward | `RollForwardService` | `test_archival_and_roll_forward.py` | **CORE** |
| `application/security/rbac.py` | 4-tier Role-Based Access Control enforcement | `RBACGuard`, `UserSession`, `RoleEnum` | `test_rbac.py` | **CORE** |
| `application/security/engagement_lock_guard.py` | Guard rejecting writes on archived engagements | `assert_engagement_not_locked` | `test_archived_readonly_enforcement.py` | **CORE** |

---

### 1.3 Infrastructure & Persistence Layer (`src/finauditpro/infrastructure/`)
Handles SQLite persistence, encryption, migrations, file parsing, and LM Studio HTTP communication.

| Module Path | Purpose | Key Public Interfaces | Tests | Status |
| :--- | :--- | :--- | :--- | :---: |
| `infrastructure/persistence/database.py` | SQLite WAL connection manager and trigger config | `DatabaseManager`, `create_sqlite_engine` | `test_persistence.py`, `test_database.py` | **CORE** |
| `infrastructure/persistence/models.py` | SQLAlchemy ORM models for core schema | `EngagementModel`, `TrialBalanceModel`, `WorkingPaperModel` | `test_persistence.py` | **CORE** |
| `infrastructure/persistence/repositories/` | Concrete repository implementations | `EngagementRepository`, `WorkingPaperRepository`, etc. | All service test suites | **CORE** |
| `infrastructure/persistence/migration_list.py` | Master linear migration sequence (001–017) | `get_all_migrations` | `test_migrations.py` | **CORE** |
| `infrastructure/security/encryption.py` | Fernet AES-128-CBC with PBKDF2 key derivation | `WorkspaceCryptoManager`, `derive_key` | `test_security_hardening.py` | **CORE** |
| `infrastructure/security/totp.py` | RFC 6238 TOTP generator and step-up validator | `generate_totp_code`, `verify_totp_code` | `test_biometrics_and_stepup_totp.py` | **CORE** |
| `infrastructure/financial/financial_importer.py` | Excel/CSV ingestion with formula injection escaping | `FinancialImporter`, `parse_indian_currency` | `test_financial_importer.py` | **CORE** |
| `infrastructure/ai/lmstudio_supervisor.py` | LM Studio daemon health probe and process manager | `LMStudioSupervisor` | `test_lmstudio_supervisor.py` | **CORE** |

---

### 1.4 Presentation UI Layer (`src/finauditpro/ui/`)
PyQt6 / PySide6 desktop interface with dark-mode design system.

| Module Path | Purpose | Key Public Interfaces | Tests | Status |
| :--- | :--- | :--- | :--- | :---: |
| `ui/main_window.py` | Application shell, navigation rail, and status bar | `MainWindow` | `test_gui.py`, `test_shell_navigation.py` | **CORE** |
| `ui/views/dashboard_view.py` | Engagement KPI dashboard & completion gates | `DashboardView` | `test_financial_gui.py` | **CORE** |
| `ui/views/working_paper_view.py` | 3-pane electronic audit workbench | `WorkingPaperView` | `test_audit_workbench_and_working_paper_lifecycle.py` | **CORE** |
| `ui/views/compliance_view.py` | CARO 2020 and Form 3CD compliance view | `ComplianceView` | `test_caro_workflow.py` | **CORE** |
| `ui/views/ai_copilot_drawer.py` | Persistent slide-over local AI assistant | `AICopilotDrawer` | `test_ai_gui.py` | **CORE** |
| `ui/dialogs/engagement_dialog.py` | Client & Engagement creation dialog | `EngagementDialog` | `test_ui_engagement_workflow.py` | **CORE** |
| `ui/dialogs/command_palette_dialog.py` | `Ctrl+K` global command palette | `CommandPaletteDialog` | `test_gui.py` | **CORE** |
