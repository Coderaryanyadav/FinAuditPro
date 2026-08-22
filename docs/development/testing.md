# Testing Strategy & Quality Assurance Suite

FinAuditPro incorporates a comprehensive automated test suite covering unit tests, integration tests, security boundaries, and architecture invariants.

---

## 1. Running Automated Tests

```bash
# Run all 130 tests
pytest -v tests

# Run tests with code coverage
pytest --cov=src/finauditpro tests

# Run static linter
ruff check src/ tests/

# Run static type checker (strict mode)
mypy src/finauditpro

# Run master 1,000-point forensic runner
python scripts/run_1000_verifications.py
```

---

## 2. Test Suite Architecture

- **`test_architecture.py`**: Enforces strict AST import boundary rules and module line count limits ($\le 400$ lines).
- **`test_security_hardening.py` & `test_document_security.py`**: Validates path traversal defense, ZIP slip protection, and encryption key derivation.
- **`test_consolidated_cross_engagement_isolation.py`**: Verifies multi-tenant database isolation.
- **`test_deterministic_analytics.py` & `test_materiality_engine.py`**: Validates Benford's Law and SA 320 materiality calculations in paise precision.
- **`test_working_paper_lifecycle.py` & `test_review_workflow_and_notes.py`**: Tests maker-checker workflows and open notes blocking.
- **`test_roll_forward_lifecycle.py` & `test_opening_balance_tie_out.py`**: Tests multi-year roll-forward and SA 510 tie-out logic.
