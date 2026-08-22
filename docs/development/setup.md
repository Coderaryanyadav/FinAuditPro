# Developer Environment Setup & Installation

Follow these steps to configure a local development environment for FinAuditPro.

---

## 1. Prerequisites

- **Python**: Python 3.12 or higher (verified on Python 3.14.7)
- **OS**: macOS (Apple Silicon arm64 / Intel) or Linux
- **Optional Tools**:
  - `brew install tesseract` (for OCR on scanned documents)
  - [LM Studio](https://lmstudio.ai/) (for local AI copilot and RAG features)

---

## 2. Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/finauditpro.git
cd finauditpro

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode with development tooling
pip install -e .[ocr,ai]
pip install -r requirements-dev.txt

# 4. Verify system environment
python scripts/automated_system_check.py

# 5. Launch application
python -m finauditpro
```
