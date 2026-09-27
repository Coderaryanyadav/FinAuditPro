# FinAuditPro — Testing Strategy & Verification

## 1. Test Suite Overview
FinAuditPro contains 130+ comprehensive automated tests:
- `tests/test_domain.py`: Domain entity invariant tests and integer math rules.
- `tests/test_trial_balance_invariants.py`: Trial balance double-entry balancing and mapping tests.
- `tests/test_substantive_engines.py`: Analytical procedure and sampling tests.
- `tests/test_security_hardening.py`: Encryption, prompt injection defense, and SQLite trigger immutability.
- `tests/test_master_e2e_integration.py`: End-to-end full audit lifecycle journeys.

## 2. Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```
