# FinAuditPro Troubleshooting & Operational Runbook (v1.0.0)

## 1. Application Launch Issues

### Problem: Application fails to start or database locked
- **Cause**: An earlier background instance may still hold a lock on the SQLite database file.
- **Solution**:
  1. Check for running Python/FinAuditPro processes:
     - On macOS/Linux: `pkill -f finauditpro`
     - On Windows: Task Manager $\rightarrow$ End Task `FinAuditPro.exe`
  2. Verify directory permissions on your data folder (`~/Library/Application Support/FinAuditPro` or `%APPDATA%\FinAuditPro`).

---

## 2. Authentication & Account Lockout

### Problem: Account locked due to repeated invalid password attempts
- **Mechanism**: After 5 consecutive failed login attempts, the account is placed in a 15-minute lockout state.
- **Solution**:
  1. Wait for the 15-minute security timer to expire.
  2. Alternatively, log in as another administrative user with the `Admin` role to reset the user's password or lockout status.

---

## 3. Financial Ingestion & Trial Balance Errors

### Problem: "Trial balance is out of balance (Debit != Credit)"
- **Cause**: Ingested spreadsheet contains unequal debit and credit totals.
- **Solution**:
  1. Verify the client source spreadsheet for unmapped suspense accounts or rounding discrepancies.
  2. Inspect the discrepancy amount displayed in the Ingestion Preview dialog.
  3. Ensure credit amounts follow consistent negative or credit-column conventions.

---

## 4. Local AI & LM Studio Connectivity

### Problem: "AI Assistant is Offline / Fallback Mode Active"
- **Cause**: FinAuditPro cannot connect to `http://localhost:1234`.
- **Solution**:
  1. Open LM Studio and start the local server.
  2. Confirm the server is listening on port `1234` and CORS is enabled if needed.
  3. Ensure an embedding model (e.g. `nomic-embed-text`) and a chat model (e.g. `deepseek-r1-distill-qwen-14b`) are loaded.
