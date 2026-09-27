# FinAuditPro — Comprehensive Codebase & Directory Architecture Guide

This document provides a complete, module-by-module breakdown of all files, directories, domain models, services, UI components, test suites, and build scripts in the **FinAuditPro** repository.

---

## 1. High-Level Architectural Layout

FinAuditPro is built following **Clean / Hexagonal Architecture** principles, enforcing strict separation of concerns across four core layers:

```
                  ┌──────────────────────────────────────────────┐
                  │               Presentation (UI)              │
                  │  PySide6 Views, Dialogs, Widgets & Workers   │
                  └──────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────▼───────────────────────┐
                  │              Application Layer               │
                  │  DTOs, Orchestration Services, Security/RBAC │
                  └──────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────▼───────────────────────┐
                  │                 Domain Layer                 │
                  │ Pure Entities, State Machines, Gate Invariants│
                  └──────────────────────▲───────────────────────┘
                                         │
                  ┌──────────────────────┴───────────────────────┐
                  │             Infrastructure Layer             │
                  │ SQLite Persistence, Analytics, AI, Document  │
                  └──────────────────────────────────────────────┘
```

---

## 2. Root-Level Files & Configuration

| File | Purpose & Description |
| :--- | :--- |
| [`pyproject.toml`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/pyproject.toml) | Primary project configuration, PEP 517/518 build system (`hatchling`), runtime dependencies, dev dependencies, tool settings (`ruff`, `mypy`, `pytest`). |
| [`finauditpro.spec`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/finauditpro.spec) | PyInstaller specification for compiling macOS `.app` bundles and Windows `.exe` standalone packages. |
| [`README.md`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/README.md) | Primary project introduction, feature highlights, installation instructions, and quick start guide. |
| [`LICENSE`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/LICENSE) | Open-source/proprietary licensing terms for the FinAuditPro software suite. |
| [`CHANGELOG.md`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/CHANGELOG.md) | Chronological version release notes and feature history. |
| [`SECURITY.md`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/SECURITY.md) | Security policy, vulnerability reporting guidelines, and local cryptographic isolation rules. |
| [`RELEASE.md`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/RELEASE.md) | Release packaging checklist, checksum generation, and distribution steps. |
| [`.gitignore`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/.gitignore) | Git ignore specification preventing accidental commit of virtual environments, SQLite databases, caches, and client data. |
| [`requirements.txt`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/requirements.txt) | Standard pip requirements reference for runtime dependencies. |
| [`requirements-dev.txt`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/requirements-dev.txt) | Development, testing, and linting tool requirements. |
| [`uv.lock`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/uv.lock) | Deterministic dependency lockfile managed by `uv`. |

---

## 3. Source Code (`src/finauditpro/`) Breakdown

### 3.1 Domain Layer (`src/finauditpro/domain/`)
Pure Python business logic, immutable domain models, state machines, and mathematical invariants with zero external I/O or framework dependencies.

| File | Responsibilities |
| :--- | :--- |
| [`entities.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/entities.py) | Core Pydantic domain models: `Firm`, `Client`, `Engagement`, `User`, `AuditEvent`, `RoleEnum` (Admin, Checker, Maker), `EngagementStatusEnum`. |
| [`value_objects.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/value_objects.py) | Immutable value objects: `Money` (64-bit integer paise arithmetic), `PAN`, `GSTIN`, `CIN`, `DIN`. |
| [`standard_ifc_controls.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/standard_ifc_controls.py) | 12 standard ICAI Internal Financial Controls (RCM) catalogue across 5 business cycles. |
| [`finalization_gate_engine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/finalization_gate_engine.py) | 10-point deterministic finalisation gate checking TB balance, sign-offs, open review notes, and evidence completeness. |
| [`engagement_state_machine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/engagement_state_machine.py) | Engagement lifecycle transitions: `DRAFT` $\rightarrow$ `PLANNING` $\rightarrow$ `FIELDWORK` $\rightarrow$ `REVIEW` $\rightarrow$ `FINALISATION` $\rightarrow$ `ARCHIVED`. |
| [`audit_matrix_entities.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/audit_matrix_entities.py) | 4-tier audit execution hierarchy: `AuditArea` $\rightarrow$ `Risk` $\rightarrow$ `Assertion` $\rightarrow$ `Procedure`. |
| [`audit_execution_entities.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/audit_execution_entities.py) | Fieldwork execution entities: `WorkingPaper`, `EvidenceFile`, `AuditFinding`, `ReviewNote`. |
| [`compliance_entities.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/compliance_entities.py) | CARO 2020 21-clause records, Form 3CD tax clauses, and Schedule III presentation checks. |
| [`completion_checklist_entities.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/completion_checklist_entities.py) | Completion registers for SA 560 (Subsequent Events), SA 570 (Going Concern), SA 580 (MRL), and SA 240. |
| [`methodology_catalog.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/methodology_catalog.py) | Built-in ICAI methodology knowledge catalog and Standard Operating Procedures. |
| [`exceptions.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/exceptions.py) | Domain exceptions: `ValidationError`, `PermissionDeniedError`, `GateBlockedError`, `LockError`. |
| [`clock.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/domain/clock.py) | Deterministic timezone-aware UTC clock utility. |

---

### 3.2 Application Layer (`src/finauditpro/application/`)
Application use cases, transactional workflows, DTOs, and fail-closed security enforcement.

| Directory / File | Responsibilities |
| :--- | :--- |
| **`security/`** | |
| ├── [`rbac.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/security/rbac.py) | Fail-closed Role-Based Access Control (`RBACManager`), 3-tier Maker $\rightarrow$ Checker $\rightarrow$ Admin SoD permissions. |
| └── [`security_context.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/security/security_context.py) | Thread-local ambient user session manager. |
| **`services/`** | |
| ├── [`auth_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/auth_service.py) | Credential verification, 2FA/TOTP management, user creation, admin password reset. |
| ├── [`firm_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/firm_service.py) | CA firm profile and practice management. |
| ├── [`client_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/client_service.py) | Audit client directory and corporate profile management. |
| ├── [`engagement_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/engagement_service.py) | Engagement orchestration, team assignment, FY management. |
| ├── [`audit_planning_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/audit_planning_service.py) | SA 300 planning, audit strategy documentation, team briefings. |
| ├── [`materiality_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/materiality_service.py) | SA 320 Overall Materiality (OM), Performance Materiality (PM), and CTT calculations. |
| ├── [`financial_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/financial_service.py) | Trial balance import, account mapping, journal scrutiny, integer balance verification. |
| ├── [`audit_execution_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/audit_execution_service.py) | Working paper drafting, review note threads, sign-off state machine. |
| ├── [`audit_matrix_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/audit_matrix_service.py) | Risk-assertion-procedure tree creation, sampling execution. |
| ├── [`compliance_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/compliance_service.py) | CARO 2020 clause responses, Form 3CD tax schedules, Schedule III validation. |
| ├── [`engagement_finalization_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/engagement_finalization_service.py) | Orchestrates finalisation gate checks and partner sign-off readiness. |
| ├── [`report_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/report_service.py) | Independent Auditor's Report assembly, PDF generation, CARO reporting. |
| ├── [`archival_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/archival_service.py) | SA 230 60-day audit file assembly, cryptographic locking, roll-forward engine. |
| ├── [`ai_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/ai_service.py) | AI copilot orchestration, local RAG retrieval, prompt sanitization. |
| └── [`settings_service.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/application/services/settings_service.py) | Local LM Studio endpoint and security posture settings. |
| **DTO Files** | Data Transfer Objects decoupling Domain from UI (e.g. `financial_dtos.py`, `completion_dtos.py`, `report_dtos.py`). |

---

### 3.3 Infrastructure Layer (`src/finauditpro/infrastructure/`)
Database persistence, database migrations, mathematical engines, AI/vector search, and document extractors.

| Directory / File | Responsibilities |
| :--- | :--- |
| **`persistence/`** | |
| ├── [`database.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/persistence/database.py) | SQLite database manager, session scopes, WAL connection configuration. |
| ├── [`models.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/persistence/models.py) | SQLAlchemy ORM mapped tables for firms, clients, engagements, TBs, users. |
| ├── **`repositories/`** | Repository implementations (`user_repository.py`, `working_paper_repository.py`, etc.). |
| └── **`migrations/`** | Sequential schema migrations (`001_initial_schema.py` through `009_archival_and_roll_forward.py`). |
| **`analytics/`** | |
| ├── [`ifc_automated_testing_engine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/analytics/ifc_automated_testing_engine.py) | SA 530 dynamic sample sizing and automated IFC control test runner. |
| ├── [`risk_matrix_5x5_engine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/analytics/risk_matrix_5x5_engine.py) | 5x5 Inherent Risk $\times$ Likelihood scoring and visual heatmap grid generator. |
| ├── [`tax_gstr2b_reconciler.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/analytics/tax_gstr2b_reconciler.py) | 3-way GST reconciler (Books vs 2B vs 3B) with Section 16(2) and 17(5) checks. |
| ├── [`benford_engine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/analytics/benford_engine.py) | Benford's 1st Law Chi-Square ($\chi^2$) digit distribution analysis. |
| └── [`cash_flow_engine.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/analytics/cash_flow_engine.py) | Automated AS-3 / Ind AS 7 Cash Flow Statement generation. |
| **`knowledge/`** | |
| └── [`icai_knowledge_centre.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/infrastructure/knowledge/icai_knowledge_centre.py) | Searchable database of Standards on Auditing, CARO 2020 clauses, and Schedule III. |
| **`security/`** | Encryption ciphers, PBKDF2 hashing, biometric authentication, and lockout state. |
| **`documents/`** | PyMuPDF text/OCR extraction, Excel parsers, and SHA-256 evidence hashing. |
| **`ai/`** | FAISS local vector indexer and LM Studio local LLM client. |

---

### 3.4 Presentation / UI Layer (`src/finauditpro/ui/`)
Modern PySide6 (Qt) desktop interface following professional CA engagement workflows.

| Directory / File | Responsibilities |
| :--- | :--- |
| [`main_window.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/main_window.py) | Primary desktop shell, sidebar navigation, header context switcher, command palette shortcut. |
| [`theme.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/theme.py) & [`styles.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/styles.py) | Design tokens, typography, glassmorphism badges, and unified styling. |
| **`views/`** | Full workspace views: |
| ├── `dashboard_view.py` | Engagement Command Center (status, materiality, open notes, readiness). |
| ├── `working_paper_view.py` | 3-pane Audit Workbench (Audit areas $\rightarrow$ WP Editor $\rightarrow$ Evidence/Review). |
| ├── `financial_data_view.py` | Trial Balance importer, Schedule III mapping, journal entry scrutiny. |
| ├── `audit_matrix_view.py` | 5x5 Inherent Risk matrix, assertion mapping, sampling execution. |
| ├── `compliance_view.py` | CARO 2020 21-clause matrix and Schedule III financial statement viewer. |
| ├── `report_view.py` | Independent Auditor's Report viewer, CARO annexure, PDF exporter. |
| ├── `archival_view.py` | SA 230 tamper-sealing archive management and roll-forward wizard. |
| ├── `settings_view.py` | System settings, local AI endpoints, team management button. |
| └── `ai_assistant_view.py` | AI Copilot query workspace. |
| **`dialogs/`** | Interactive modal dialogs: |
| ├── [`user_management_dialog.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/dialogs/user_management_dialog.py) | Admin User Management (Maker/Checker/Admin creation, password reset, role edit). |
| ├── [`login_dialog.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/dialogs/login_dialog.py) | Clean, secure login window with 2FA and forced reset handling. |
| ├── [`command_palette_dialog.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/src/finauditpro/ui/dialogs/command_palette_dialog.py) | Keyboard-driven command palette ($\mathbf{\Cmd+K}$ / $\mathbf{Ctrl+K}$). |
| ├── `audit_completion_dialog.py` | 10-gate deterministic finalisation gate review dialog. |
| └── `create_aje_dialog.py`, `sampling_dialog.py`, `review_notes_dialog.py`, etc. | Task-specific audit dialogs. |

---

## 4. Test Suite (`tests/`)

The `tests/` directory contains **135 test suites** validating every layer of the system (445 total test cases):

- **End-to-End User Journeys**: `test_full_system_user_journeys.py`, `test_canonical_financial_workflow.py`, `test_phase_a_comprehensive_foundation.py` through `test_phase_f_simulation.py`.
- **Capstone & 3-Tier Governance**: `test_capstone_features_and_governance.py`, `test_maker_checker.py`, `test_rbac.py`, `test_auth_and_user_service.py`.
- **Mathematical Invariants & Engines**: `test_deterministic_analytics.py`, `test_trial_balance_invariants.py`, `test_journal_analytics_and_benford.py`, `test_cash_flow_statement_engine.py`.
- **Security & Adversarial Audits**: `test_defensive_security_audit.py`, `test_language_safety.py`, `test_architecture.py`, `test_formula_injection_escaping.py`, `test_prompt_injection.py`.
- **Archival & Durability**: `test_archival_and_roll_forward.py`, `test_backup_restore.py`, `test_migrations.py`.

---

## 5. Automation & Packaging Scripts (`scripts/`)

| Script | Purpose |
| :--- | :--- |
| [`scripts/packaging/build_macos.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/scripts/packaging/build_macos.py) | Builds standalone macOS `.app` bundle, signs it, and packages into `.dmg` with drag-and-drop presentation. |
| [`scripts/packaging/build_windows.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/scripts/packaging/build_windows.py) | Compiles Windows `.exe` executable and Inno Setup installer package. |
| [`scripts/packaging/verify_release.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/scripts/packaging/verify_release.py) | Pre-build and post-build release verification and SHA-256 checksum generation. |
| [`scripts/packaging/generate_icons.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/scripts/packaging/generate_icons.py) | Generates high-resolution `.icns`, `.ico`, and `.png` application icons. |
| [`scripts/packaging/clean.py`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/scripts/packaging/clean.py) | Cleans temporary build artifacts, `.pyc` caches, and distribution folders. |

---

## 6. Documentation Directory (`docs/`)

- **`docs/engineering/`**: Deep technical architecture guides (`FULL_SYSTEM_TEST_REPORT.md`, `DOMAIN_INVARIANTS.md`, `DOMAIN_GRAPH.md`, `FINANCIAL_ANALYTICS_AUDIT.md`).
- **`docs/release/`**: Formal release reports ([`RELEASE_READINESS_REPORT.md`](file:///Users/aryanyadav/Desktop/PROJECTS/Audit/docs/release/RELEASE_READINESS_REPORT.md)).
- **`docs/architecture/`**: Component relationship graphs, SQLite schema layouts, and security blueprints.
