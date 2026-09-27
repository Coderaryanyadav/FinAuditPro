# FinAuditPro — Database Architecture & Migrations

## 1. SQLite WAL Configuration
FinAuditPro utilizes local SQLite configured with optimal ACID settings for enterprise desktop reliability:
- `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent reads).
- `PRAGMA synchronous = NORMAL;` (High throughput with full crash safety).
- `PRAGMA foreign_keys = ON;` (Strict referential integrity enforcement).
- `PRAGMA busy_timeout = 5000;` (5-second retry window on concurrent writes).

## 2. Immutability Triggers
Database-level triggers enforce that once `working_papers.status = 'APPROVED'` or `engagements.status = 'ARCHIVED'`, SQL `UPDATE` and `DELETE` commands are rejected with an `ABORT` error at the SQLite engine level.

## 3. Migration Mechanics
- Versioned linear migrations stored in `src/infrastructure/migrations/`.
- Schema migrations execute automatically inside atomic transactions upon application startup.
