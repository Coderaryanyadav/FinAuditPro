# Phase 18 Baseline — Type Safety & Code Quality Hardening

**Date:** 2026-09-21  
**Repository:** FinAuditPro  
**Environment:** macOS (Python 3.14.7, PySide6 6.11.2, pytest 9.1.1)

---

## 1. Baseline Summary

| Metric | Measured Baseline Value | Status / Notes |
| :--- | :--- | :--- |
| **Pytest Suite** | 373 Passed, 4 Failed, 5 Blocked by unmocked UI prompt | 4 objective test failures in first run, guided workflow, doc intelligence |
| **Coverage** | 86% (13,525 / 15,777 statements) | High baseline coverage across core domain and application |
| **Ruff Check** | 2 Errors (F401, I001) | In `src/finauditpro/application/services/guided_workflow_service.py` |
| **MyPy Check** | 18 Errors across 4 files | Attributed to model imports, missing attributes, and enum literal typing |

---

## 2. Baseline Test Results Breakdown

### Command:
```bash
pytest -q
pytest -q --cov=src/finauditpro
```

- **Collected Items:** 382 test cases across 86 test modules
- **Passed:** 373
- **Failed:** 4
  - `tests/test_first_run.py::test_initialize_database_runs_all_migrations`: Expected 17 migrations, actual 18 migrations registered.
  - `tests/test_guided_workflow_stepper.py::test_factual_workflow_evaluation_empty_engagement`: Mismatch on incomplete reason wording (`'Trial balance not imported / imbalanced'` vs `'Trial Balance data not imported'`).
  - `tests/test_guided_workflow_stepper.py::test_factual_workflow_evaluation_in_progress`: Incomplete reason matching logic for pending review notes.
  - `tests/test_smart_document_intelligence.py::test_document_metadata_persistence_and_confirmation`: ImportError attempting to import `DocumentStructuredMetadata` from `finauditpro.domain.entities` instead of `finauditpro.domain.document_entities`.
- **UI Blocking / Modal Lock:** 5 tests in `tests/test_working_paper_evidence_split_view.py` invoking interactive `QMessageBox.information` without headless/mock interception.

---

## 3. Baseline Ruff Status

### Command:
```bash
ruff check src tests
```

- **Total Errors:** 2
- **Files Affected:**
  1. `src/finauditpro/application/services/guided_workflow_service.py:9:5`: `F401` `DocumentModel` imported but unused.
  2. `src/finauditpro/application/services/guided_workflow_service.py:156:13`: `I001` Import block is un-sorted / un-formatted.

---

## 4. Baseline MyPy Status

### Command:
```bash
mypy src/finauditpro
```

- **Total Errors:** 18 errors across 4 files (checked 289 source files)
- **Top Files by Error Count:**
  1. `src/finauditpro/application/services/practice_dashboard_service.py`: 11 errors
  2. `src/finauditpro/application/services/guided_workflow_service.py`: 4 errors
  3. `src/finauditpro/infrastructure/documents/smart_document_intelligence.py`: 2 errors
  4. `src/finauditpro/application/services/document_service.py`: 1 error

---

## 5. Categories of Errors & Technical Debt

1. **ORM / Persistence Model Drift:** Services importing models that were refactored or referencing attributes with changed names (`AuditEventModel.event_type` vs `action`, `details_json` vs `details`).
2. **Missing Entity Exports:** `DocumentStructuredMetadata` referenced across application services but not re-exported cleanly in top-level domain namespace.
3. **Enum Subtype / Literal Narrowing:** Mismatch between narrowed literals in classifiers vs general category enumerations.
4. **Interactive UI Modals in Automated Tests:** Calling blocking Qt message boxes in test environments without abstraction/mocking.
