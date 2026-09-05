# FinAuditPro Known Limitations & Operating Boundaries (v1.0.0)

## 1. Architectural Scope Boundaries
1. **Single-Workstation Architecture**: FinAuditPro is designed as a standalone, offline desktop application. It does not provide real-time multi-user concurrent editing or cloud-hosted database synchronization.
2. **Not an Accounting ERP / Bookkeeping Tool**: FinAuditPro is an audit workstation. It does not provide general bookkeeping, sales invoicing, inventory billing, payroll generation, or double-entry voucher creation for client business operations.
3. **Local AI Model Availability**: Local AI assistant and semantic search capabilities require a running local LLM instance (e.g. LM Studio on `http://localhost:1234`). When the local AI server is offline, core deterministic audit routines operate normally with AI features disabled.

---

## 2. Operational Limitations
1. **Operating System File System Controls**: While SQLite triggers and HMAC signatures protect data from within the application, root/administrator users on the host workstation possess physical control of local files. Physical disk encryption (FileVault / BitLocker) is recommended.
2. **OCR Engine Dependencies**: Processing scanned image evidence and raster PDFs requires the system-level Tesseract binary (`tesseract`) and PyMuPDF bindings to be available.
3. **Platform Code Signing**: Pre-built binaries are tested on macOS Darwin arm64 and Windows x64. Enterprise distributions requiring Apple Developer ID notarization or Windows EV code signing must be signed with your organization's signing credentials in CI/CD.
