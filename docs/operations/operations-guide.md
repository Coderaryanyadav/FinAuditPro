# FinAuditPro — Operational Runbook & Diagnostics Guide

This guide details configuration settings, environment variable overrides, diagnostic health probes, and runtime error remediation for FinAuditPro.

---

## 1. Environment Variables & Runtime Settings

FinAuditPro supports zero-config defaults out of the box with optional overrides:

| Variable Name | Purpose | Default Value | Example |
| :--- | :--- | :--- | :--- |
| `FINAUDITPRO_DB_PATH` | Path to custom SQLite database file. | Platform default path | `/var/data/finauditpro.db` |
| `FINAUDITPRO_APP_DATA_DIR` | Custom root directory for app data. | Platform default path | `/opt/finauditpro/data` |
| `FINAUDITPRO_ENCRYPTION_KEY` | Explicit Fernet 32-byte urlsafe key override. | Auto-generated via machine salt | `b64encodedstring...` |

### Settings File (`settings.json`):
Stored under the user's application data directory:
```json
{
  "lm_studio_endpoint": "http://localhost:1234",
  "llm_model": "deepseek-r1-distill-qwen-14b",
  "embedding_model": "nomic-embed-text",
  "allow_cloud_ai": false
}
```
> [!IMPORTANT]
> `allow_cloud_ai` must remain `false` to guarantee 100% air-gapped statutory privacy compliance.

---

## 2. Automated Diagnostic Self-Check

Always run the built-in diagnostic probe first when diagnosing issues:
```bash
python scripts/development/automated_system_check.py
```

---

## 3. Common Issues & Remediation Runbook

### A. Tesseract OCR Missing / Degraded Mode
- **Symptom**: System diagnostic warns that Tesseract OCR is not found.
- **Cause**: Tesseract executable not in `$PATH`.
- **Solution**: Install Tesseract binary:
  - macOS: `brew install tesseract`
  - Linux (Ubuntu/Debian): `sudo apt-get install tesseract-ocr`

### B. LM Studio Copilot Offline
- **Symptom**: AI Copilot displays `"Offline Rule Engine Active"`.
- **Cause**: LM Studio local server not running on `http://localhost:1234`.
- **Solution**: Open LM Studio, load `deepseek-r1-distill-qwen-14b`, and start the local HTTP server on port 1234.

### C. Database Lock Timeout
- **Symptom**: `OperationalError: database is locked`.
- **Cause**: Another process or background worker held a write lock past 5000ms.
- **Solution**: Ensure only one desktop instance is running and SQLite WAL files (`-wal`, `-shm`) are accessible.
