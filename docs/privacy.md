# FinAuditPro — Privacy Policy & Data Minimization Model

FinAuditPro is engineered as a **privacy-first, local-only desktop operating system** for Indian statutory audit practice.

---

## 1. What Data FinAuditPro Stores

- **Audit Working Papers & Findings**: Stored locally in SQLite database (`finauditpro.db`).
- **Source Documents**: Invoices, contracts, and financial statements stored locally in `~/.gemini/antigravity-ide/app_data/documents`.
- **Vector Indices**: Document chunks and embeddings stored locally in `~/.gemini/antigravity-ide/app_data/vector_store`.

---

## 2. Zero Network Outbound Transmissions

FinAuditPro makes **zero outbound network connections** by default:
- **No Telemetry**: No analytics or usage metrics are transmitted to any remote server.
- **Local AI Only**: Connects exclusively to a user-configured local LM Studio instance (`http://localhost:1234`).
- **No External Cloud AI**: External cloud AI integrations default to `OFF` (`allow_cloud_ai: false`).

---

## 3. Data Deletion & Retention

- **Non-Statutory Retention Rules**: Expiry deadlines (default: 7 years per SA 230) are policy guidance carrying `verified_statutory: False` disclaimers.
- **No Auto-Purge**: The application **never** automatically deletes audit files upon reaching retention deadlines. Expiry notifications are surfaced for auditor review.
