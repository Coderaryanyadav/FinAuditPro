# Contributing to FinAuditPro

Thank you for your interest in contributing to **FinAuditPro**. This document outlines development setup, coding standards, branch conventions, and pull request procedures.

---

## 1. Development Environment Setup

1. **Fork & Clone Repository**:
   ```bash
   git clone https://github.com/your-username/finauditpro.git
   cd finauditpro
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Editable Package with Development Dependencies**:
   ```bash
   pip install -e .[ocr,ai]
   pip install pytest pytest-cov ruff mypy
   ```

---

## 2. Architectural Boundaries & AST Rules

FinAuditPro enforces clean layer boundaries verified automatically by `tests/test_architecture.py` on every commit and CI run:

1. **Domain Layer Purity**: `src/finauditpro/domain/` must contain zero imports from SQLAlchemy, PySide6, HTTP clients, or infrastructure.
2. **UI Layer Isolation**: `src/finauditpro/ui/` must import zero SQLAlchemy or infrastructure modules directly. Access must pass through application services.
3. **Module Line Count Limit**: No single Python module may exceed 400 lines of code.

---

## 3. Code Style & Quality Tools

- **Linter & Formatter**: Ruff (`ruff check src tests scripts`, `ruff format src tests scripts`).
- **Type Checker**: MyPy (`mypy src/finauditpro`).
- **Test Suite**: Pytest (`pytest -v tests`).
- **Diagnostics**: `python scripts/development/automated_system_check.py`.

---

## 4. Pull Request Checklist

Before submitting a PR, ensure:
- [ ] All 130+ tests pass cleanly (`pytest -v tests`).
- [ ] `tests/test_architecture.py` AST enforcer passes (0 layer violations, $\le 400$ lines per module).
- [ ] `tests/test_language_safety.py` passes.
- [ ] Zero secrets, real PAN/GSTIN, or real client audit records are committed.
- [ ] Documentation under `docs/` is updated for new features.

