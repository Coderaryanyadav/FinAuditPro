# FinAuditPro — Database Schema & Migrations

FinAuditPro uses SQLite 3 operating in Write-Ahead Logging (WAL) mode for low-latency desktop performance.

---

## 1. Schema Migrations (1 to 9)

Database schema changes are managed via versioned SQL migrations in `migration_list.py`:
1. `001_initial_schema`: Firms, Users, Roles, Clients, Engagements, Audit Events.
2. `002_create_document_tables`: Documents, Document Versions, FTS5 Search Table.
3. `003_create_financial_tables`: Datasets, Trial Balance Lines, Ledger Entries, Bank Lines.
4. `004_create_planning_tables`: Materiality, Risks, Audit Procedures, Findings.
5. `005_create_ai_tables`: AI Findings, Vector Index Metadata.
6. `006_create_working_paper_tables`: Working Papers, Review Notes, Sign-Offs.
7. `007_create_report_tables`: Reports, Safe Export Log.
8. `008_create_archival_and_retention_tables`: Archives, Manifest Seals, Retention Configs.
9. `009_create_roll_forward_tables`: Roll-Forward Records, Opening Balance Links.

---

## 2. Session Lifecycle & Security

- Connections managed via `DatabaseManager` with explicit transaction boundaries (`session_scope()`).
- Archived engagements locked via `PRAGMA query_only=ON`.
