# FinAuditPro — Installation & From-Source Execution Guide

FinAuditPro is an offline-first, privacy-first desktop audit intelligence
operating system for Indian statutory audit practice.

---

## 1. Prerequisites

- **Operating System**: macOS (Apple Silicon arm64 / Intel x86_64) or Linux
- **Python**: Python 3.12 or higher (verified on Python 3.14.7)
- **Tesseract OCR Binary** (Optional, for document image/scanned PDF OCR):
  ```bash
  brew install tesseract
  ```
- **LM Studio** (Optional, for local RAG and AI copilot capabilities):
  - Download & launch [LM Studio](https://lmstudio.ai/)
  - Download and load `deepseek-r1-distill-qwen-14b` and `nomic-embed-text`
  - Enable local server at `http://localhost:1234`

---

## 2. From-Source Setup & Execution (Verified)

### Step 1: Clone Repository & Create Virtual Environment

```bash
cd /path/to/Audit
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Package in Editable Mode

```bash
pip install -e .
```

### Step 3: Launch FinAuditPro Application

```bash
# Via Python module entrypoint:
python -m finauditpro

# Or via installed console script entrypoint:
finauditpro
```

### Step 4: Sign In

On initial launch, sign in with the pre-seeded local administrator account:
- **Username:** `admin@finauditpro.com`
- **Password:** `Admin@123`

You can add additional Partner, Manager, and Associate accounts via the user management service.

---

## 3. Environment Self-Check Diagnostics

On launch, click **Settings $\rightarrow$ Run System Diagnostics** to inspect
real system prerequisite probes. FinAuditPro gracefully degrades when optional
features (LM Studio, Tesseract) are unavailable.
