# FinAuditPro — Document Processing & Evidence Pipeline

FinAuditPro handles multi-format audit document ingestion, OCR extraction, and full-text indexing.

---

## 1. Document Pipeline Stages

```
Upload Document PDF/Image
       ⬇
Compute Cryptographic SHA-256 Hash
       ⬇
Store Original File in App Storage
       ⬇
Text Extraction (PyMuPDF for vector PDFs / Tesseract OCR for scans)
       ⬇
SQLite FTS5 Full-Text Indexing
       ⬇
FAISS Vector Chunking & Embedding
       ⬇
Evidence Link Creation
```

---

## 2. Asynchronous Execution Safety

Document parsing and OCR extraction are executed in background worker threads (`DocumentProcessingWorker`), keeping the main PySide6 UI thread completely responsive.
