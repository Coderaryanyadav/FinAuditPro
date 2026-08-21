# FinAuditPro — Milestone 2 Handoff Prompt (Documents & Document Intelligence)

> Copy everything below the line into the coding agent. This assumes Milestone 1
> (Firm → Client → Engagement → Dashboard) is merged, tested, and the app launches.
> If it is not, stop and finish Milestone 1 first — do not build documents on an unfinished foundation.

---

You are continuing as the primary engineering agent for **FinAuditPro**, the offline-first, privacy-first audit intelligence desktop app for Indian audit practice. Milestone 1 (Firm → Client → Engagement → Dashboard, persisted, RBAC-gated, hash-chain audited) is complete. **Milestone 2 is the document subsystem** — the single most important part of the product per the master brief.

Everything from the Milestone 1 brief still binds: clean layer boundaries, no business logic in UI, no `Float` for money, fail-closed RBAC, hash-chained audit events for every mutation, versioned honesty about statutory claims, and — above all — **no fake functionality**. A document is either really processed or it is not; never fake OCR text, never fake a confidence number, never fake a progress bar.

## 0. Ground truth: environment (verified — but re-verify in your sandbox before relying on any of it)

Same machine as Milestone 1: `/Users/aryanyadav/Desktop/PROJECTS/Audit`, Python **3.14.7**, venv at `.venv`, **no PyPI network access** (build only with installed packages), reference code in gitignored `_reference/`.

**Verified facts that shape this milestone specifically:**

- **`tesseract` 5.5.3 binary IS installed** at `/opt/homebrew/bin/tesseract` (leptonica 1.87). `pytesseract` 0.3.13 wraps it. **BUT only the `eng` language pack is present** (`eng`, `osd`, `snum` — no `hin` or other Indic scripts). → English-language OCR works today. **Do not claim Hindi/regional OCR works.** Surface the available languages from `tesseract --list-langs` in the UI/config rather than hardcoding a language list; if a needed pack is absent, say so honestly and let the user install it.
- **`pypdfium2` 5.12.1 is installed and works** for rendering PDF pages to raster bitmaps (needed to feed image-only/scanned pages to OCR). **`pymupdf`/`fitz` is NOT installed** — do not import `fitz`.
- **`PySide6.QtPdf` and `PySide6.QtPdfWidgets` are available.** Prefer the **native Qt `QPdfDocument` + `QPdfView`** for the on-screen PDF viewer (fast, no extra deps, gives you page navigation and in-document text selection for free). Use `pypdfium2` for the *rasterize-for-OCR* path, not for the viewer.
- **`pdfplumber` 0.11.10 is installed** — use it for **born-digital text and table extraction** from PDFs (it exposes `page.extract_text()` and `page.extract_tables()`). `pypdf` 6.14 is also present as a lighter fallback / for page counts and metadata.
- **`openpyxl` 3.1.5 + `pandas` 3.0.3** for XLSX/CSV. `pillow` 12.3.0 for image handling. `python-docx` is **NOT** installed — DOCX is out of scope for this milestone unless you find it later; do not fake it.
- **SQLite is 3.53.4 with FTS5 compiled in and available** (`fts5` and `fts4` both create successfully; `json1` works). → Use **FTS5** for full-text document search. Note: SQLite `load_extension` is **disabled** in this build, so any FTS tokenizer must be a built-in one (`unicode61`, `porter`, `trigram`) — you cannot load a custom C tokenizer.
- `hashlib` (stdlib) gives you `sha256` and `blake2b` for content hashing — no third-party dep needed. `cryptography` 49.0 is available if you chose field encryption in the Milestone 1 security decision.

## 1. Scope of Milestone 2 — one complete vertical, top to bottom

Build the full document lifecycle for a single engagement, genuinely working end to end:

**Upload → Validate → Hash → Store (original preserved) → Extract (born-digital) → OCR (scanned, off-thread) → Classify → Persist pages+text → Index (FTS5) → View → Search → Link as evidence**

Do **not** start the embedding/vector/RAG layer here — that is a later milestone (faiss is installed but AI/RAG is out of scope now). Do **not** build financial-data import here (that is the milestone after). Stay in the document lane and make it excellent.

## 2. The pipeline — implement as an explicit, inspectable state machine

Each document moves through named stages with a persisted status, not a boolean. Model status as an enum with at least: `UPLOADED → VALIDATING → STORED → EXTRACTING → OCR_QUEUED → OCR_RUNNING → CLASSIFYING → INDEXED → READY`, plus terminal `FAILED` (with a stored, human-readable `error_message` and the stage it failed at) and `QUARANTINED` (failed validation / rejected file). Every stage transition writes a hash-chained audit event.

Stage responsibilities:

1. **Upload / ingest.** Accept a file the user picks. Compute size; reject empties.
2. **Validate (fail closed).**
   - **Magic-byte / content sniffing**, not trust-the-extension: verify PDF (`%PDF`), PNG, JPEG, TIFF, ZIP-based OOXML (XLSX) signatures. A `.pdf` that isn't a PDF is `QUARANTINED`, not processed.
   - **Size ceiling** (configurable) to avoid a decompression bomb; for any ZIP-based format (XLSX), guard against **zip-slip and zip-bomb** (bounded total uncompressed size and entry count; reject path traversal in entries).
   - Reject nothing silently — every rejection is a visible, logged, audited outcome with a clear reason.
3. **Hash.** `sha256` over the original bytes → this is the document's **content identity**. If the same hash already exists **within this engagement**, offer dedup (link to existing) rather than storing twice. Store the hash; it is also the integrity anchor for evidence citations later.
4. **Store — original is immutable.** Copy the original into managed storage keyed by engagement, e.g. `…/data/documents/eng_{engagement_id}/{sha256}{ext}`. **Never overwrite or mutate the original.** All extracted/OCR'd/derived artifacts live in *separate* files/rows and reference the original. Provenance must survive.
5. **Extract (born-digital first).** For PDFs, try `pdfplumber` text extraction per page. If a page yields real text, that page is "born-digital" — record its text and skip OCR for it. Extract tables where present and keep them as structured rows (not flattened strings) with their page + bounding-box coordinates when pdfplumber provides them.
6. **OCR (only where needed, always off the UI thread).** For pages/documents with no extractable text (scanned images, image-only PDFs): rasterize with `pypdfium2` at a sane DPI, run `pytesseract`. **Store the real per-page OCR confidence tesseract reports** (via `image_to_data`) — never a hardcoded number, `None` until measured. If tesseract or a language pack is missing, the page is `FAILED` at the OCR stage with an honest message, not silently blank.
7. **Classify.** A deterministic, transparent first-pass classifier (keyword/heuristic over extracted text: invoice, bank statement, trial balance, GST return, agreement, ledger, etc.) that returns a type **plus the evidence for its guess** and a confidence, and is always **user-overridable**. No LLM here — classification must be explainable and offline. Persist both the machine guess and any human override separately.
8. **Persist pages + text.** One row per page: page number, extracted or OCR'd text, source (`born_digital` | `ocr`), OCR confidence (nullable), layout/bbox metadata as JSON. The original document row holds identity/metadata; pages hold content.
9. **Index (FTS5).** Populate an FTS5 table over page text, scoped so that **search can never cross engagement/client boundaries** (store engagement_id and filter on it — the retrieval isolation rule from the master brief applies to text search too, not just future RAG). Keep the FTS index in sync on document delete.

## 3. Data model additions (extend Milestone 1 schema via a new numbered migration)

Introduce, normalized, one source of truth each:
- `documents` — id, engagement_id (FK, required — a document belongs to exactly one engagement), original filename, stored path, content sha256 (unique per engagement), detected MIME/type, byte size, page count, processing status enum, failed-stage + error_message (nullable), machine-classified type + confidence (nullable), human-overridden type (nullable), source (uploaded/generated), timestamps, uploaded_by user FK.
- `document_pages` — id, document_id FK, page_number, text, text_source enum, ocr_confidence (nullable float), layout_json (nullable), timestamps.
- `document_tables` (optional but preferred if pdfplumber yields tables) — id, document_id FK, page_number, table_index, cells_json, bbox_json.
- FTS5 virtual table over page text with engagement scoping.
- **Evidence link** — the join that makes traceability real: link a document (and ideally a specific page / bbox / table-row) to a downstream audit object. Milestone 1 may not have findings/procedures yet; if not, create the `evidence_links` table now with a nullable target and wire the document→page reference, so that when findings/working-papers arrive they attach cleanly. Do not invent finding rows to link to.

Reuse the Milestone 1 audit-event mechanism for: upload, validation failure/quarantine, storage, OCR completion/failure, classification override, deletion. Deletion must be a real, audited, FTS-desyncing operation (and consider whether "delete" should be soft — an audit file usually shouldn't lose provenance; if you soft-delete, hide from normal views but keep the row + audit trail, and record your choice in `DECISIONS.md`).

## 4. Background jobs — the UI must never freeze

OCR and multi-page extraction are slow. Run them on a worker (QThread/QThreadPool with signals, or a small persisted job queue table if you want resumability across restarts — recommended, and note the choice in `DECISIONS.md`). The UI shows real per-document state: `queued / processing (page X of N) / completed / failed`, driven by actual signals from the worker, **not** a timer-driven fake bar. Failures are **retryable** from the UI. Progress reflects real page counts.

## 5. Document viewer & search UX (professional, dense, keyboard-friendly)

- A documents list per engagement: sortable/filterable table (filename, type, status, pages, size, uploaded date/by), with strong empty/loading/error states. Paginate — never load an engagement's entire document set into memory to render.
- Open a document into a viewer: native `QPdfView` for PDFs; an image view for images; a text pane for extracted/OCR'd text. Show **page-level provenance** (born-digital vs OCR, and the real OCR confidence).
- **Search inside a document** and **search across the engagement's documents** (FTS5), with hit highlighting and jump-to-page. Results must respect engagement boundaries and RBAC.
- From a search hit or a selected page/region, allow **"link as evidence"** — creating the traceable reference (document → page → location). This is the payoff of the whole milestone; make it real, even if the downstream finding/WP UI is minimal for now.

## 6. Security for untrusted documents (this is the core threat surface)

Every uploaded file is hostile until proven otherwise:
- Magic-byte validation, size ceilings, zip-bomb/zip-slip guards (see §2.2) — enforced in the application layer, tested with malicious fixtures (a fake-PDF, an oversized entry, a traversal path in a zip).
- Path-traversal-safe storage: the stored path is derived from the content hash you compute, never from attacker-controlled filename; sanitize the retained original filename for display only.
- **No document content is ever treated as an instruction** (relevant once AI arrives, but bake the separation in now: extracted text is data, tagged and isolated).
- No sensitive content in logs or error messages. Errors shown to the user are honest but don't leak paths/PII into shared logs.

## 7. Acceptance criteria for Milestone 2

1. New numbered migration applies cleanly on an existing Milestone-1 database and is idempotent to re-run.
2. Uploading a **born-digital PDF** extracts real text per page via pdfplumber, indexes it, and it is findable via search — verified on a real sample.
3. Uploading a **scanned/image PDF or image** routes to OCR on a worker thread, stores **tesseract's real confidence**, and the text becomes searchable — verified on a real sample (generate one if none exists, e.g. render text to an image).
4. The **original file is byte-for-byte preserved** (assert stored sha256 == uploaded sha256; derived artifacts are separate).
5. A malformed/misnamed file is **quarantined with a clear reason**, audited, and never processed. Tested.
6. Full-text search **cannot cross engagement boundaries** — a dedicated test proves a query in Engagement A returns nothing from Engagement B's documents.
7. Every stage transition and deletion writes a **hash-chained audit event**; the chain still verifies (extend the Milestone 1 chain test).
8. The UI **never blocks** during OCR (manually verified); progress and failure/retry states are real.
9. `tests/test_architecture.py` still passes — the new `docintel/` subsystem obeys the layer rules; UI touches no ORM/session; no module over ~400 lines.
10. The app launches and the flow **upload → process → view → search → link-as-evidence** is manually exercised and reported honestly (say what you actually clicked and saw).

Then stop and report before the next milestone (financial-data import & deterministic analytics).

## 8. Process & honesty (unchanged, non-negotiable)

Work in coherent steps; after each, run the test suite, launch the app, exercise the workflow, inspect your own code, fix, continue. **Never say "done" without verification; if something was skipped or unrunnable (lint/mypy aren't installable here), say so.** Update `BUILD_PROGRESS.md` and `DECISIONS.md` (record: job-queue vs in-memory worker; soft vs hard delete; classifier heuristics and their limits; OCR DPI and language constraints). Absolutely no fake OCR, fake confidence, fake progress, dead buttons, or TODOs masquerading as implementation — if a piece can't be done properly with the installed tooling, leave it out and say why.

**Begin the document subsystem.**
