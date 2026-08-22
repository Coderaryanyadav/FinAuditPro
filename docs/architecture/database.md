# FinAuditPro — Database Architecture & Migrations

FinAuditPro uses a local SQLite 3 database operating in Write-Ahead Logging (WAL) mode for low-latency concurrent desktop reads and transactions.

---

## 1. Database Location & Bootstrap

By default, the database is stored in the user's platform application data directory:
- **macOS**: `~/Library/Application Support/FinAuditPro/db/finauditpro.db`
- **Linux**: `~/.local/share/FinAuditPro/db/finauditpro.db`
- **Windows**: `%APPDATA%\FinAuditPro\db\finauditpro.db`

The location can be customized via the `--db-path` CLI option or the `FINAUDITPRO_DB_PATH` environment variable.

---

## 2. Authoritative Schema Migrations (1 to 9)

Schema versioning is strictly managed via sequential, idempotent SQL migrations defined in `src/finauditpro/infrastructure/persistence/migration_list.py`:

| Version | Migration Identifier | Primary Tables / Schema Objects |
| :--- | :--- | :--- |
| **001** | `001_initial_schema` | `firms`, `clients`, `engagements`, `users`, `audit_events` |
| **002** | `002_create_document_tables_and_fts` | `documents`, `document_pages`, `document_chunks`, `document_tables`, `evidence_links`, `documents_fts` (FTS5 virtual table) |
| **003** | `003_create_financial_tables_and_findings` | `financial_datasets`, `trial_balance_lines`, `ledger_entries`, `bank_statement_lines`, `financial_exceptions`, `findings` |
| **004** | `004_create_audit_planning_and_unified_findings_tables` | `materiality_assessments`, `risks`, `audit_procedures` |
| **005** | `005_create_ai_subsystem_tables` | `ai_conversation_turns`, `ai_suggested_findings`, `ai_query_audits` |
| **006** | `006_create_working_paper_tables` | `working_papers`, `working_paper_versions`, `review_notes`, `sign_offs` |
| **007** | `007_create_reporting_tables` | `audit_reports`, `report_sections`, `report_approvals`, `safe_export_audits` |
| **008** | `008_create_archival_and_retention_tables` | `engagement_archives`, `archive_manifest_items`, `retention_policies`, `reopen_audit_logs` |
| **009** | `009_create_roll_forward_tables` | `roll_forward_records`, `carried_forward_findings`, `opening_balance_links`, `engagements.prior_engagement_id` |
