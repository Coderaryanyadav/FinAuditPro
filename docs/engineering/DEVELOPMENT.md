# FinAuditPro — Developer Guide & Coding Standards

## 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# Virtual environment setup
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Launch desktop app
python3 src/main.py
```

## 2. Coding Standards
- **Strict Typing:** All signatures require Python type hints (`mypy` compliant).
- **Currency Arithmetic:** Use `Money` / integer paise only. Floating-point types (`float`) are prohibited in financial domain code.
- **Decoupled DDD Layers:** Domain layer must never import from presentation or infrastructure.
- **Formatting:** Code formatted with `black` (line length 100) and linted with `ruff`.
