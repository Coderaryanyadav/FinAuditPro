# Document Processing, Security & FTS5 Search

FinAuditPro provides a secure, offline-first document management and full-text search pipeline with zero outbound client data transmission.

---

## 1. Document Ingestion Pipeline

```text
Upload Document (PDF, PNG, JPG, CSV, TXT)
  ├── 1. Security Validation (Sanitize filename, detect MIME magic bytes, verify path traversal safety)
  ├── 2. Cryptographic Integrity (Calculate SHA-256 digest)
  ├── 3. Secure Disk Storage (Store under engagement-partitioned UUID path)
  ├── 4. Text Extraction (PyMuPDF for vector PDFs / Tesseract OCR for scans and images)
  ├── 5. SQLite FTS5 Indexing (Full-text indexing with snippet/highlight capability)
  └── 6. Evidence Linkage (Link pages to audit findings, risks, and working papers)
```

---

## 2. Document Security Contract

Implemented in `src/finauditpro/domain/document_security.py` and `src/finauditpro/infrastructure/documents/`:
- **Path Traversal Protection**: Traversal sequences (`../`, `..\`, absolute paths) are stripped and sanitized.
- **Magic Byte MIME Detection**: Validates file headers to prevent executable extension spoofing.
- **SHA-256 Content Hashing**: Guarantees non-repudiation and evidence tamper detection.
- **ZIP Slip / ZIP Bomb Defense**: Backup/restore extractors enforce file count, decompression ratio, and entry path limits.

---

## 3. SQLite FTS5 Search

Documents are indexed in a dedicated `documents_fts` virtual table, enabling fast keyword queries with porter tokenization:
```sql
SELECT document_id, page_number, snippet(documents_fts, 2, '<b>', '</b>', '...', 15)
FROM documents_fts
WHERE documents_fts MATCH :query AND engagement_id = :engagement_id;
```
