# FinAuditPro — Final Remediation Backlog

This document organizes all findings identified during the Prompt 17 Independent Audit and Red-Team Review across severity tiers, detailing remediated items and ongoing quality improvement roadmaps.

---

## Tier P0 — Critical (Fixed Immediately in Prompt 17)

### FIND-SEC-001: Session Unlock Authentication Bypass via None Passcode
- **ID**: `FIND-SEC-001`
- **Severity**: P0
- **Status**: **RESOLVED**
- **Problem**: `RBACManager.unlock_session(None)` accepted a missing passcode and unlocked the active user session without validation. Concurrently, `SecurityContext.enforce_permission` omitted checking `session.is_locked`.
- **Why It Matters**: An unauthorized actor sitting at a locked workstation could call `unlock_session(None)` or trigger protected actions without authenticating.
- **Files**:
  - `src/finauditpro/application/security/rbac.py`
  - `src/finauditpro/application/security/security_context.py`
- **Fix**: Replaced permissive `None` branch with mandatory passcode check and explicit verified biometric flag; enforced `session.is_locked` in `SecurityContext.enforce_permission`.
- **Test**: `tests/test_redteam_hardening_audit.py::test_redteam_session_unlock_bypass_blocked`
- **Dependency**: None
- **Estimated Complexity**: Low

### FIND-FIN-001: Engagement Finalization Mutation Bypass
- **ID**: `FIND-FIN-001`
- **Severity**: P0
- **Status**: **RESOLVED**
- **Problem**: Mutation services (`AuditAdjustmentService`, `FinancialDataService`, `DocumentService`, `WorkingPaperService`) did not check if the parent engagement had status `COMPLETED` or `ARCHIVED`.
- **Why It Matters**: Allowed silent alteration of financial datasets, AJEs, working papers, and evidence on cryptographically locked statutory audit files.
- **Files**:
  - `src/finauditpro/application/security/engagement_lock_guard.py` [NEW]
  - `src/finauditpro/application/services/audit_adjustment_service.py`
  - `src/finauditpro/application/services/financial_data_service.py`
  - `src/finauditpro/application/services/document_service.py`
  - `src/finauditpro/application/services/working_paper_service.py`
  - `src/finauditpro/application/services/working_paper_scaffolder.py`
  - `src/finauditpro/application/services/engagement_finalization_service.py`
- **Fix**: Implemented central `assert_engagement_not_locked` guard on all mutation methods and locked all working papers upon partner sign-off.
- **Test**: `tests/test_redteam_hardening_audit.py::test_redteam_finalization_mutation_bypass_blocked`
- **Dependency**: None
- **Estimated Complexity**: Medium

---

## Tier P1 — Major (Fixed in Prompt 17)

### FIND-ACC-001: Concurrent Debit/Credit Journal Line Invariants
- **ID**: `FIND-ACC-001`
- **Severity**: P1
- **Status**: **RESOLVED**
- **Problem**: `AuditJournalEntry.validate_double_entry()` allowed individual lines to possess both non-zero debit and credit amounts or zero amounts for both.
- **Why It Matters**: Violates core double-entry accounting principles and distorts lead schedule account breakdowns.
- **Files**: `src/finauditpro/domain/audit_adjustment_entities.py`
- **Fix**: Validated each line in `validate_double_entry` to enforce mutual exclusivity (`debit_paise > 0 and credit_paise == 0` or vice versa) and reject zero-amount lines.
- **Test**: `tests/test_redteam_hardening_audit.py::test_redteam_double_entry_line_level_invariants`
- **Dependency**: None
- **Estimated Complexity**: Low

---

## Tier P2 — Fix Before Wider Enterprise Deployment

### FIND-DAT-001: Idempotent Migration Runner Guard
- **ID**: `FIND-DAT-001`
- **Severity**: P2
- **Problem**: If an external database inspection tool interrupts schema migration execution halfway through a multi-statement DDL, partial tables could remain without migration row insertion.
- **Why It Matters**: Can require manual database intervention during enterprise recovery.
- **Files**: `src/finauditpro/infrastructure/first_run.py`
- **Fix**: Wrap individual migration execution blocks in explicit DDL transaction savepoints where supported by SQLite.
- **Test**: `tests/test_migration_failure_recovery.py`
- **Dependency**: SQLite 3.35+
- **Estimated Complexity**: Medium

### FIND-REP-001: High-Precision Rounding Display in Large PDF Exports
- **ID**: `FIND-REP-001`
- **Severity**: P2
- **Problem**: When generating PDF lead schedules with hundreds of micro-accounts, small rounding differences on paise-to-rupee float conversions can show cosmetic ±₹0.01 discrepancies in footer sums.
- **Why It Matters**: Auditors demand exact mathematical tie-out between line totals and footers.
- **Files**: `src/finauditpro/application/services/report_service.py`
- **Fix**: Enforce integer paise summation before converting to rupee presentation format in report templates.
- **Test**: `tests/test_report_precision.py`
- **Dependency**: ReportLab / Jinja2
- **Estimated Complexity**: Low

---

## Tier P3 — Quality & Reliability Improvements

### FIND-UX-001: High-DPI Scaling on 4K Multi-Monitor Setups
- **ID**: `FIND-UX-001`
- **Severity**: P3
- **Problem**: Complex nested QSplitters in the Working Paper and Financial Data views may experience slight text clipping when dragged between standard DPI and 4K displays on Windows/macOS.
- **Why It Matters**: Minor visual polish issue for partner review sessions.
- **Files**: `src/finauditpro/ui/main_window.py`
- **Fix**: Enable `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` during application launch.
- **Test**: Manual UI smoke test.
- **Dependency**: PySide6
- **Estimated Complexity**: Low

### FIND-PERF-001: Batch Insert for High-Volume GL Imports (>500k rows)
- **ID**: `FIND-PERF-001`
- **Severity**: P3
- **Problem**: General ledger line insertion currently uses ORM model addition in chunks of 5,000 rows. For datasets exceeding 500,000 transactions, bulk Core insert would improve import speed by 3x.
- **Why It Matters**: Large manufacturing clients with millions of transactional rows.
- **Files**: `src/finauditpro/infrastructure/persistence/repositories/financial_data_repository.py`
- **Fix**: Implement `session.execute(insert(GeneralLedgerLineModel), list_of_dicts)` bulk operation.
- **Test**: `tests/test_continuous_audit_performance.py`
- **Dependency**: SQLAlchemy 2.0 Core
- **Estimated Complexity**: Medium

---

## Tier P4 — Nice to Have / Future Enhancements

### FIND-EXT-001: Streaming Kafka / Webhook Live ERP Connector
- **ID**: `FIND-EXT-001`
- **Severity**: P4
- **Problem**: Data ingestion currently occurs via file uploads (CSV, Excel) rather than direct real-time Kafka or ERP webhook streams.
- **Why It Matters**: Enables instantaneous sub-second fraud and risk alerting.
- **Files**: `src/finauditpro/infrastructure/streaming/`
- **Fix**: Add optional Kafka / RabbitMQ consumer plugin.
- **Test**: `tests/test_streaming_ingestion.py`
- **Dependency**: External message broker
- **Estimated Complexity**: High
