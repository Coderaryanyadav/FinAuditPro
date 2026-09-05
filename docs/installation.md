# FinAuditPro Installation & Setup Guide (v1.0.0)

## 1. System Requirements
- **Operating System**: macOS 12+ (Apple Silicon arm64 / Intel x86_64), Windows 10/11 (64-bit), or Linux (Ubuntu 22.04+).
- **Python Version**: Python 3.12, 3.13, or 3.14.
- **Memory**: 4 GB RAM minimum (8 GB+ recommended if running local AI models).
- **Disk Space**: 500 MB for core application; additional storage for local document vaults and SQLite database.

---

## 2. Installation via Standalone Packages (Recommended)

### macOS (Apple Silicon & Intel)
1. Download `FinAuditPro-1.0.0-macOS-arm64.dmg` (or Intel `x86_64`).
2. Double-click the `.dmg` installer.
3. Drag **FinAuditPro** into your `/Applications` directory.
4. Launch from Applications or Spotlight.

### Windows (64-bit)
1. Download `FinAuditPro-Setup-1.0.0-x64.exe` (or standalone portable `.zip`).
2. Run the setup wizard and choose your installation path.
3. Launch **FinAuditPro** from the Start Menu.

---

## 3. Installation from Source (Developers & IT Admins)

```bash
# 1. Clone repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install core and optional dependencies
pip install -e .[ocr,ai]

# 4. Initialize and launch application
python -m finauditpro
```

---

## 4. Optional Local AI Setup (LM Studio)
To enable local LLM-assisted audit summaries and working paper analysis without cloud transmission:
1. Install [LM Studio](https://lmstudio.ai/).
2. Load a supported model (e.g. `deepseek-r1-distill-qwen-14b` or `nomic-embed-text`).
3. Start the local server on `http://localhost:1234`.
4. FinAuditPro will automatically connect to the local endpoint upon launch.
