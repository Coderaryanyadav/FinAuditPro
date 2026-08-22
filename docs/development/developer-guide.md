# FinAuditPro — Developer Onboarding & QA Guide

This guide covers developer environment setup, dependency management, coding standards, and test execution for FinAuditPro.

---

## 1. Prerequisites & Environment Setup

- **Python**: Python 3.12 or higher (verified on Python 3.14.7)
- **OS**: macOS (Apple Silicon arm64 / Intel), Linux x64, or Windows x64
- **Optional Tools**:
  - `brew install tesseract` (for OCR on scanned documents)
  - [LM Studio](https://lmstudio.ai/) (for local AI assistant features)

### Step-by-Step Setup:
```bash
# 1. Clone repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode with development tooling
pip install --upgrade pip
pip install -e .[ocr,ai]
pip install -r requirements-dev.txt

# 4. Verify system environment
python scripts/development/automated_system_check.py

# 5. Launch application
python -m finauditpro
```

---

## 2. Code Quality & Automated Test Suite

FinAuditPro enforces strict static typing, zero lint errors, and 100% test pass rate across 130 unit/integration tests:

```bash
# Run all 130 tests
pytest -v tests

# Run tests with code coverage
pytest --cov=src/finauditpro tests

# Run static linter
ruff check src/ tests/ scripts/

# Run static type checker (strict mode)
mypy src/finauditpro

# Run master 15-stage 1,000-point forensic runner
python scripts/development/run_1000_verifications.py
```

---

## 3. Test Suite Architecture & AST Guards

- **`test_architecture.py`**: Enforces strict AST import boundary rules (zero framework imports in `domain/`) and module line limits ($\le 400$ lines).
- **`test_security_hardening.py` & `test_document_security.py`**: Validates path traversal defense, ZIP slip protection, and encryption key derivation.
- **`test_consolidated_cross_engagement_isolation.py`**: Verifies multi-tenant database isolation.
- **`test_deterministic_analytics.py` & `test_materiality_engine.py`**: Validates Benford's Law and SA 320 materiality calculations in paise precision.
- **`test_working_paper_lifecycle.py` & `test_review_workflow_and_notes.py`**: Tests maker-checker workflows and open notes blocking.
- **`test_roll_forward_lifecycle.py` & `test_opening_balance_tie_out.py`**: Tests multi-year roll-forward and SA 510 tie-out logic.
