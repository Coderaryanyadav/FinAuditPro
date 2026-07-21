# FinAuditPro Cross-Platform Compatibility Matrix & Dependency Specification

## Executive Summary
FinAuditPro is standardized on **Python 3.12** (`>=3.10, <3.13`) to guarantee 100% binary wheel compatibility across deep learning libraries (`torch`, `transformers`), desktop GUI engines (`PySide6`), vector databases (`faiss-cpu`), and document processing tools (`paddleocr`, `pypdf`, `pdfplumber`).

---

## 1. Official Supported Python Version
- **Target Runtime**: Python 3.12 (Tested on 3.12.8 / 3.12.13)
- **Supported Range**: Python 3.10.x – 3.12.x
- **Config Files**: `.python-version`, `pyproject.toml`, `requirements.txt`

---

## 2. Verified Dependency Matrix

| Dependency | Target Version | macOS Apple Silicon (M1/M2/M3/M4) | Windows 11 (x86_64) | Ubuntu 24.04 LTS (x86_64) | Optional / Fallback Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PySide6** | `6.7.3` | ✅ Native arm64 Qt6 | ✅ Native x64 Qt6 | ✅ Native x64 Qt6 | Core GUI Engine (Mandatory) |
| **SQLAlchemy** | `2.0.35` | ✅ Pass | ✅ Pass | ✅ Pass | Core ORM (Mandatory) |
| **Ollama** | `0.3.3` | ✅ Local REST API | ✅ Local REST API | ✅ Local REST API | Core LLM Provider (Mandatory) |
| **PaddleOCR** | `2.7.3` | ✅ Native (Py 3.12) | ✅ Native | ✅ Native | Feature Detected; PyPDF Digital Parser Fallback |
| **sentence-transformers** | `3.1.1` | ✅ PyTorch backend | ✅ PyTorch backend | ✅ PyTorch backend | Vector Embedding Engine |
| **FAISS** | `1.8.0.post1` | ✅ faiss-cpu arm64 | ✅ faiss-cpu x64 | ✅ faiss-cpu x64 | Dense Retrieval Index |
| **PyTorch (torch)** | `2.4.1` | ✅ MPS (Metal) acceleration | ✅ CUDA / CPU | ✅ CUDA / CPU | Deep Learning Core |
| **HuggingFace Transformers** | `4.44.2` | ✅ Pass | ✅ Pass | ✅ Pass | Model Loader & Tokenizers |
| **ReportLab** | `4.2.2` | ✅ Pass | ✅ Pass | ✅ Pass | Executive PDF Generator |
| **Matplotlib** | `3.9.2` | ✅ MacOSX backend | ✅ Win32 backend | ✅ Agg backend | Financial Analytics Charts |
| **PyInstaller** | `6.10.0` | ✅ `.app` / `.dmg` build | ✅ `.exe` bundle | ✅ AppImage binary | Standalone Packaging |

---

## 3. Graceful Feature Detection Architecture

### OCR Engine Strategy
```
+-------------------------------------------------------------+
|                 OCREngine.process_document()                |
+-------------------------------------------------------------+
                               |
                   Is document a Digital PDF?
                              / \
                             /   \
                     YES    /     \   NO / Scanned Image
                           v       v
           +-----------------+   +------------------------------------+
           | PyPDF /         |   | Check OCREngine.is_ocr_available() |
           | Native Parser   |   +------------------------------------+
           +-----------------+                     |
                   |                    Is Paddle/Tesseract Present?
                   v                              / \
            Return High-Conf                     /   \
            Digital Text                 YES    /     \   NO
                                               v       v
                                       Run Native     Disable OCR
                                       OCR Engine     Show UI Warning
                                                      Return Non-Destructive Status
```

### Feature Detection Guarantees:
1. **Zero Crash Policy**: Missing OCR backends will **never** throw unhandled exceptions or crash the desktop application.
2. **UI Warning Banner**: A clear non-blocking warning (`⚠️ OCR Engine Unavailable - Digital PDF Parser Active`) is rendered in `DocumentUploadWidget`.
3. **No Silent Data Mutation**: If OCR cannot run on an image file, explicit status `[OCR Processing Disabled: ...]`) is logged and saved to the audit record rather than faking OCR output.
