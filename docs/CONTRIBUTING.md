# Developer Contribution Guidelines

## Setup Development Environment
```bash
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd Audit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests
All code modifications must be verified against the test suite prior to submitting pull requests:
```bash
.venv/bin/pytest tests/test_fatal_fixes.py
```

## Coding Rules
1. **Zero Hardcoded Data**: Never write hardcoded sample arrays or metrics in UI or service code.
2. **Database First**: All metrics must be computed via live SQL queries against SQLAlchemy models.
