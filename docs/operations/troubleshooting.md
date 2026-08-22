# Troubleshooting & Diagnostics Guide

Use this guide to diagnose and resolve common environment or runtime issues.

---

## 1. Automated Diagnostic Tool

Always run the built-in diagnostic tool first:
```bash
python scripts/automated_system_check.py
```

---

## 2. Common Issues & Solutions

### A. Tesseract OCR Missing / Degraded Mode
- **Symptom**: System diagnostic warns that Tesseract OCR is not found.
- **Cause**: Tesseract executable not in `$PATH`.
- **Solution**: Install Tesseract binary:
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`

### B. LM Studio Copilot Offline
- **Symptom**: AI Copilot displays `"Offline Rule Engine Active"`.
- **Cause**: LM Studio local server not running on `http://localhost:1234`.
- **Solution**: Open LM Studio, load `deepseek-r1-distill-qwen-14b`, and start the local HTTP server on port 1234.

### C. Database Lock Timeout
- **Symptom**: `OperationalError: database is locked`.
- **Cause**: Another process or background worker held a write lock past 5000ms.
- **Solution**: Ensure only one desktop instance is running and SQLite WAL files (`-wal`, `-shm`) are accessible.
