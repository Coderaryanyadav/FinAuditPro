# FinAuditPro API & Service Reference

## Services API
- `AuthService`: Authentication, password hashing, and session management.
- `ClientService`: Client CRUD and industry classification.
- `DocumentService`: Ingestion pipeline, digital PDF parsing, text extraction, and vector store indexing.
- `RiskService`: Finding evaluation and anomaly categorization.
- `ReportService`: PDF report pack generation and Excel exports.

## Database Repositories
- `ClientRepository`: Data access for `Client` model.
- `DocumentRepository`: Data access for `Document` model.
- `RiskRepository`: Data access for `Finding` model.
- `AuditLogRepository`: Immutable audit trail logging.
