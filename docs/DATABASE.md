# FinAuditPro Database Architecture & Migrations (v1.0.0)

## 1. Engine & Configuration
FinAuditPro uses **SQLite 3.45+** configured for robust single-user local concurrency and transaction safety:
- **Journal Mode**: `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent reads and atomic writes).
- **Synchronous**: `PRAGMA synchronous = NORMAL;` (Ensures durability on OS filesystem commits).
- **Foreign Keys**: `PRAGMA foreign_keys = ON;` (Strict relational referential integrity).
- **Busy Timeout**: `PRAGMA busy_timeout = 5000;` (5-second retry window for busy locks).

---

## 2. Migration Framework
Schema evolution is managed via sequential, deterministic Python migration scripts (`src/finauditpro/infrastructure/database/migrations/`).
- **Migration Tracking Table**: `schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT)`.
- **Migration History**:
  1. `001_initial_schema.py`: Firms, clients, engagements, users, roles, audit_events.
  2. `002_financial_data.py`: Trial balance, general ledger accounts, transactions, lead schedules.
  3. `003_audit_matrix.py`: Materiality benchmarks, risks, planned procedures, findings.
  4. `004_documents_and_fts.py`: Document records, evidence links, SQLite FTS5 full-text search index.
  5. `005_working_papers.py`: SA 230 working papers, review notes, sign-off chains.
  6. `006_compliance_and_caro.py`: CARO 2020 clauses, Form 3CD tax audit schedules, GSTR reconciliations.
  7. `007_archival_and_rollforward.py`: SQC 1 archival records, opening balance tie-out schedules.
  8. `008_audit_trail_triggers.py`: SQLite `BEFORE UPDATE` and `BEFORE DELETE` triggers enforcing immutable `audit_events`.
  9. `009_security_and_indexes.py`: Unique compound constraints, performance indexes, and query isolation.

---

## 3. Immutability & Trigger Protection
To protect audit integrity even against direct SQLite manipulation, database-level triggers prevent modification of signed records:
```sql
CREATE TRIGGER IF NOT EXISTS trg_protect_audit_events_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(FAIL, 'UPDATE operations are strictly prohibited on audit_events');
END;

CREATE TRIGGER IF NOT EXISTS trg_protect_audit_events_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(FAIL, 'DELETE operations are strictly prohibited on audit_events');
END;
```
