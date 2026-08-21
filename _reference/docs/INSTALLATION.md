# FinAuditPro — Installation & Deployment Guide

This guide covers developer setup, local execution, and standalone desktop installer compilation across platforms.

---

## 1. System Prerequisites

- **Python**: Version 3.10, 3.11, or 3.12 (64-bit)
- **OS**: Windows 10/11 (64-bit), macOS 12+, Ubuntu 22.04 LTS+
- **Local AI**: [Ollama](https://ollama.ai/) installed and running
- **Hardware**: 8 GB RAM (16 GB recommended), 5 GB free disk space

---

## 2. Windows Installation (Developer / Source)

```cmd
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

python -m venv .venv
.venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

# Start Ollama service (separate terminal)
ollama pull llama3.2

# Launch App
python src/main.py
```

---

## 3. macOS & Linux Setup

```bash
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

ollama pull llama3.2

python src/main.py
```

---

## 4. Packaging Standalone Executables (PyInstaller)

FinAuditPro uses PyInstaller to bundle the application into a standalone executable directory.

```bash
# Run PyInstaller build spec
pyinstaller FinAuditPro.spec
```

The output standalone binary is located at `dist/FinAuditPro/FinAuditPro.exe`.

### Included Hidden Imports in Spec
- `PySide6.QtCore`, `PySide6.QtWidgets`, `PySide6.QtGui`, `PySide6.QtCharts`
- `sqlalchemy`, `cryptography`, `pydantic`, `pypdf`, `pdfplumber`
- `faiss`, `sentence_transformers`, `torch`, `numpy`

---

## 5. Building Windows Installer (Inno Setup)

To compile the single-file setup installer `FinAuditPro_v1.0.0_Setup.exe`:

1. Download and install [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Build the PyInstaller dist folder first (`pyinstaller FinAuditPro.spec`).
3. Compile `scripts/installer.iss`:
   ```cmd
   iscc scripts/installer.iss
   ```
4. Output installer will be created in `Output/FinAuditPro_v1.0.0_Setup.exe`.
