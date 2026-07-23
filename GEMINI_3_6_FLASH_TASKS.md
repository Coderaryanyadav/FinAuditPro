# FinAuditPro — Quick Action Plan for Gemini 3.6 Flash

## 🎯 Tech Stack & Architecture Context
- **Framework**: Desktop App built with **PySide6 (Qt 6.7)**. *No React / Tailwind / Web APIs*.
- **Theming**: Centralized QSS in `src/ui/styles.py`. Avoid inline `setStyleSheet()` calls.
- **Backend & AI**: SQLAlchemy 2.0 + SQLite (WAL), Ollama (Local LLM), FAISS (RAG Vector Store), PaddleOCR / Tesseract, ReportLab.
- **Concurrency**: Heavy operations (OCR, Ollama LLM, FAISS search, PDF exports) **MUST** run on background `QThread` workers (`src/ai/workers.py`) to prevent freezing the Qt GUI event loop.

---

## 📋 5-Phase Work Plan Summary

### Phase 1: Architecture & Service Wiring Audit
1. **Map UI to Services**: Trace `src/ui/*.py` calls down through `src/services/*.py` to `src/database/repositories/*.py`.
2. **Eliminate Disguised Crashes**: Audit `PlaceholderWidget` / `safe_load()` in `src/ui/dashboard.py` and across all UI modules. Surface real exceptions instead of hiding them behind "integrated" placeholder labels.
3. **Refactor God Files**: Deconstruct bloated modules (e.g., `dashboard.py` at 780+ lines) into modular controllers and dedicated views.

### Phase 2: Qt/QSS UI/UX Refinement
1. **Centralize Design Tokens**: Extract hardcoded inline `setStyleSheet()` strings across `src/ui/` into reusable QSS classes in `src/ui/styles.py`.
2. **Visual States Audit**: Implement dedicated **Loading**, **Empty**, and **Error** state widgets for all 15 UI pages.
3. **Layout & Accessibility**: Ensure responsive layouts (`QGridLayout`, `QVBoxLayout`), explicit focus policies, keyboard hotkeys (`QShortcut`), and font hierarchy consistency.

### Phase 3: Feature & Handler Verification
1. **Slot Integrity**: Audit every button click, form submission, and tab change handler to confirm non-empty slot bindings.
2. **Input Validation**: Add schema and format checks (GSTIN, PAN, File types, numeric limits) before executing DB or AI tasks.
3. **Feedback Signals**: Ensure toast notifications or status indicators fire on task completion or failure.

### Phase 4: Performance, Threading & Security Audit
1. **QThread Offloading**: Verify all Ollama, OCR, FAISS, and PDF build tasks are dispatched off the main UI loop.
2. **SQLAlchemy Session Safety**: Enforce `try/finally: session.close()`, contextual managers, and rollback mechanisms on write failures.
3. **Security Audit**: Verify PBKDF2 key derivation, AES-256 backup encryption (`src/security/crypto.py`), and SHA-256 hash-chain integrity in `src/security/audit_trail.py`.

### Phase 5: Incremental Implementation & Verification
1. **Prioritized Fixes**: Address issues strictly by severity (Crash/Data Loss > Security > Broken Flow > UX Polish).
2. **Verification**: Run `pytest tests/ -v` after each fix pass to maintain 100% test pass rates across all 45+ test cases.

---

## ⚡ Immediate Next Steps
- [ ] Inspect `src/ui/dashboard.py` for remaining `safe_load()` swallows or inline styles.
- [ ] Audit `src/ai/workers.py` to ensure all long-running AI/OCR pipelines use `QThread` signals.
- [ ] Run `pytest tests/ -v` to confirm full baseline integrity.
