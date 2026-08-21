# FinAuditPro — Testing Strategy & Quality Assurance

FinAuditPro uses a comprehensive automated testing suite built with Pytest.

---

## 1. Test Pyramid & Suites

- **AST Architecture Enforcer (`tests/test_architecture.py`)**: Enforces domain layer purity, UI layer isolation, and module line count limits (<= 400 lines).
- **Language Safety Enforcer (`tests/test_language_safety.py`)**: Enforces zero-fraud terminology rules.
- **Unit & Math Tests**: Verifies value objects, SA 320 materiality calculations, and SA 510 tie-out math in paise.
- **Integration Tests**: Verifies SQLite migrations, document FTS5 search, backup Fernet encryption, and multi-tenant client isolation.
- **Packaging & Diagnostics Tests**: Verifies data directory bootstrap, launch self-checks, and settings persistence.

---

## 2. Running Automated Tests

```bash
# Run full test suite
pytest -v tests

# Run coverage report
pytest --cov=src/finauditpro tests
```
