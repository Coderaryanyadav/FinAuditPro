# FinAuditPro — Desktop Application User Manual

This manual provides operational instructions for Chartered Accountants and audit assistants using FinAuditPro.

---

## 🖥️ Screen Overview

### 1. Dashboard Overview Screen
- **Executive KPIs**: Live SQL aggregations displaying active engagements, average risk score, compliance score, documents processed, and estimated manual audit hours saved.
- **Audit Workflow Tracker**: Visual progress bar indicating stage completion (Planning -> Execution -> Reporting -> Completed).
- **Recent Audit Activity**: Historical ledger feed showing recent document uploads, rule violations, and user actions.

### 2. Client Management Screen
- **Client Directory**: Searchable list of clients filtered by name, GSTIN, or PAN.
- **Client Onboarding Form**: Add new clients with mandatory name, valid 15-character GSTIN, 10-character PAN, CIN, and industry selection.
- **KMP Register**: Track Key Management Personnel (Directors, CFOs, Managing Partners) per client entity.

### 3. Document Intake & Document Intelligence
- **Drag-and-Drop File Intake**: Drop PDF invoices, bank statements, and tax returns into the dropzone.
- **Automatic Encryption Detection**: Password-protected PDFs are intercepted safely with a status notification requiring password removal before intake.
- **Multi-Engine Extraction**: PyPDF digital text extraction with automatic fallback to PaddleOCR/Tesseract for scanned documents.
- **Vector Search Indexing**: Extracted chunks are automatically embedded and indexed in the offline FAISS vector store.

### 4. Statutory Rule Engine Workspace
- **Automated Rule Evaluation**: Automatically runs 7 core rules (GSTIN presence, GST rate slab validation, Vendor PAN verification, Section 40A(3) cash limits > ₹10,000, Benford's Law anomaly detection, Round-sum transactions, and Negative cash balances).
- **Findings List**: Displays severity-flagged findings with AI confidence scores and financial impact estimates.

### 5. Offline AI Assistant Workspace
- **Contextual RAG Chat**: Ask natural-language questions about uploaded audit documents.
- **Local LLM Execution**: Uses Ollama (`llama3.2`) locally over localhost port 11434 with zero internet connectivity.
- **Prompt Injection Boundary**: Automatically sanitizes input queries for security.

### 6. Working Papers & Deliverables Export
- **Standardized Working Papers**: Prepare section-coded working papers (e.g. Fixed Assets, Bank Reconciliation).
- **Report Generation**: One-click PDF audit report generation via ReportLab complete with digital signature metadata and QR verification hash.
- **Excel Audit Pack**: Export structured tables and findings to OpenPyXL workbook packages.

---

## ❓ Frequently Asked Questions & Troubleshooting

**Q: Why does the AI workspace say "Ollama Offline"?**  
A: Ensure the Ollama background daemon is running on your machine (`ollama serve`) and the model is downloaded (`ollama pull llama3.2`).

**Q: Where is my data stored on disk?**  
A: Database (`finauditpro.db`) and encryption keys are stored in your platform user AppData directory (`%APPDATA%\FinAuditPro\` on Windows).

**Q: Can I use password-protected PDF bank statements?**  
A: Remove PDF password protection using Adobe Acrobat or a PDF tool before uploading to allow OCR text extraction.
