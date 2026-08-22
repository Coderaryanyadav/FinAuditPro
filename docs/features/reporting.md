# Report Assembly, Approval & Safe Export Pipeline

FinAuditPro generates statutory audit reports with strict approval controls and formula-injection defenses.

---

## 1. Statutory Report Generation

Reports are assembled from audit findings, SA 320 materiality assessments, risk matrix conclusions, and CARO 2020 compliance items via `ReportService` (`src/finauditpro/application/services/report_service.py`):
- **Draft Reports**: Generated with a semi-transparent diagonal `"DRAFT - FOR INTERNAL REVIEW ONLY"` watermark on every page.
- **Approved Reports**: The watermark is removed only after formal partner sign-off and approval transition (`Approved` status).

---

## 2. Spreadsheet Formula-Injection Neutralization

When exporting audit schedules, financial datasets, or working papers to CSV or XLSX format via OpenPyXL, FinAuditPro runs all cell strings through `src/finauditpro/domain/export_sanitizer.py`:
- Cells beginning with formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with a leading single quote (`'`).
- Prevents remote command execution or DDE payload triggers when opened in Microsoft Excel or LibreOffice Calc.
