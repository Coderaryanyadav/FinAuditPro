## Summary
Provide a brief description of the changes introduced by this pull request.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Architectural refactoring (no functional changes)
- [ ] Documentation update

## Verification Checklist
- [ ] `pip install -e .` builds cleanly.
- [ ] `.venv/bin/python -m pytest -v tests` passes 100% cleanly.
- [ ] `tests/test_architecture.py` AST enforcer passes (zero UI/DB layer leaks; module lines <= 400).
- [ ] `tests/test_language_safety.py` Zero-Fraud terminology enforcer passes.
- [ ] No real client data, PAN, GSTIN, or secret keys are committed.
- [ ] `domain/` layer contains zero external framework dependencies.

## Related Issues
Closes #
