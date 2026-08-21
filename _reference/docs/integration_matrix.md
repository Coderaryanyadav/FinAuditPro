# FinAuditPro — Functional Integration Matrix

This matrix tracks the end-to-end integration status across UI, Service, DB/API, Persistence, and Automated Verification layers.

| Feature / Module | UI Screen | Service Layer | DB / API Model | Persistence | Verified | Notes |
|------------------|-----------|---------------|----------------|-------------|----------|-------|
| Authentication & Session | LoginWindow | AuthService | User | SQLite | ✓ | Role permissions & admin boot |
| Dashboard Metrics | DashboardWindow | DashboardService | Engagement / AuditProject | SQLite | ✓ | Unified active engagement |
| Client Management | ClientsPage | ClientService | Client / ClientIndustry | SQLite | ✓ | GSTIN & PAN validation |
| Audit Engagement | CreateEngagementDialog | EngagementService | Engagement / FinancialYear | SQLite | ✓ | Standard WP index seeder |
| Document Intelligence | DocumentsPage | DocumentService | Document / DocumentPage | SQLite / FS | ✓ | OCR state & text extraction |
| Financial Statements | FinancialStatementsPage | FinancialService | FinancialStatement / Account | SQLite | ✓ | TB balancing & account mapping |
| GST Reconciliation | GSTVerificationPage | GSTService | GSTReconciliationRun | SQLite | ✓ | GSTR-2B vs Purchase Reg variance |
| Statutory Compliance | CompliancePage | ComplianceService | ComplianceTask | SQLite | ✓ | CARO 2020 & Companies Act |
| Risk & Materiality | RiskAnalysisPage | RiskService | Risk / MaterialityCalculation | SQLite | ✓ | ISA 320 Materiality benchmark |
| AI Audit Assistant | AIAnalysisPage | AIService | Finding / DocumentPage | SQLite / AI | ✓ | Direct WP index finding linkage |
| Working Papers Index | WorkingPapersPage | WorkingPaperService | WorkingPaperIndex / WorkingPaper | SQLite | ✓ | A-Z standard index & signoffs |
| Audit Report Generator | ReportsPage | ReportService | AuditReport / Finding | SQLite / PDF | ✓ | Dynamic findings & PDF render |
| Audit Trail Logging | HistoryPage | AuditTrailService | AuditLog | SQLite | ✓ | SHA-256 hash chain log |
| System Settings | SettingsPage | ConfigManager | AppConfig | SQLite / JSON | ✓ | AI model & DB encryption |
| Help & Shortcuts | KeyboardShortcutsDialog | UI Helper | Application | N/A | ✓ | Global desktop shortcuts |
