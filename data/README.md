# FinAuditPro Application Data Directory

This directory serves as the local development and fallback storage location for FinAuditPro runtime artifacts:
- Local SQLite database files (`finauditpro.db`, WAL/SHM journal logs)
- Document storage and extracted OCR artifacts
- Local FAISS vector index files
- Encrypted export archives and backup bundles

In production, the application stores data in the user's platform application directory (`~/Library/Application Support/FinAuditPro` on macOS, `~/.local/share/FinAuditPro` on Linux, `%APPDATA%\FinAuditPro` on Windows).
