# FinAuditPro — Testing Strategy & Specification

This document details the automated test suite structure, test execution standards, and regression quality gates for FinAuditPro.

---

## 1. Overview

FinAuditPro uses `pytest` for unit and integration testing. All core business services, database repositories, security mechanisms, document processing fallback paths, and UI widgets are covered by automated tests.

---

## 2. Test Execution

To run the complete test suite:

```bash
# Clean execution of 45 test cases
python -m pytest -o addopts="" tests/
```

To run with coverage report:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## 3. Test Module Summary (45 Tests)

| Test Module | Component / Scope Covered | Test Count | Status |
|---|---|---|---|
| `tests/test_analytics.py` | SQL KPI Engine, Trend Engine, Risk Heatmap Engine | 3 | ✅ Pass |
| `tests/test_deployment.py` | App logging setup, System Diagnostics, Schema Migrations | 4 | ✅ Pass |
| `tests/test_document_intelligence.py` | Multi-engine OCR fallback, PyPDF parser, Chunking, Embedding | 7 | ✅ Pass |
| `tests/test_fatal_fixes.py` | Database session leak prevention, Exception handlers, Failure paths | 5 | ✅ Pass |
| `tests/test_reporting.py` | ReportLab PDF generator, OpenPyXL Excel export, Working Paper Engine | 4 | ✅ Pass |
| `tests/test_rule_engine.py` | GST rules, Income Tax rules, Fraud rules, Accounting rules | 4 | ✅ Pass |
| `tests/test_security.py` | PBKDF2 Password Hashing, AES-256 Backups, Audit Ledger Hash Chain | 6 | ✅ Pass |
| `tests/test_ui_components.py` | PySide6 Windows, Dialogs, Navigation signals, Table widgets | 12 | ✅ Pass |

---

## 4. CI/CD Quality Gate

Before any merge into `main`:
- 100% pass rate on all 45 automated tests required.
- Zero `sqlite3.OperationalError` database lock leaks.
- All domain exceptions must inherit from `FinAuditError`.
