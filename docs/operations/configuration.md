# Configuration & Environment Variables Reference

FinAuditPro supports zero-config defaults out of the box, with optional overrides via environment variables or `settings.json`.

---

## 1. Environment Variables

| Variable Name | Purpose | Default Value | Example |
| :--- | :--- | :--- | :--- |
| `FINAUDITPRO_DB_PATH` | Path to custom SQLite database file. | Platform default path | `/var/data/finauditpro.db` |
| `FINAUDITPRO_APP_DATA_DIR` | Custom root directory for app data. | Platform default path | `/opt/finauditpro/data` |
| `FINAUDITPRO_ENCRYPTION_KEY` | Explicit Fernet 32-byte urlsafe key override. | Auto-generated via machine salt | `b64encodedstring...` |

---

## 2. Settings File (`settings.json`)

Stored under the user's application data directory:
```json
{
  "lm_studio_endpoint": "http://localhost:1234",
  "llm_model": "deepseek-r1-distill-qwen-14b",
  "embedding_model": "nomic-embed-text",
  "allow_cloud_ai": false
}
```
- `allow_cloud_ai`: Must remain `false` for air-gapped privacy compliance.
