# FinAuditPro — Data Classification & Inventory

This document inventory categorizes data handled by **FinAuditPro** into risk levels.

---

## Data Classification Levels

### 1. HIGHLY CONFIDENTIAL
- **General Ledgers & Bank Statements**: Detailed transaction registers, account balances, vendor payment lists.
- **Source Contracts & Tax Returns**: Uploaded PDF contracts, tax audit filings, GST returns.
- **Audit Findings & Working Papers**: Internal draft findings, material weaknesses, partner review notes.
- **Encrypted Archives & Key Material**: Machine Fernet keys and backup archives.

### 2. CONFIDENTIAL
- **Client Profiles**: Legal entity names, statutory PAN, GSTIN, registered addresses.
- **Audit Engagement Schedules**: Financial years, audit types, team assignments.
- **Audit Event Logs**: Immutable audit log entries.

### 3. INTERNAL / SYSTEM
- **System Settings**: LM Studio endpoint URL, model selection preference.
- **Diagnostic Results**: Launch self-check status (Python version, Tesseract pathing).
