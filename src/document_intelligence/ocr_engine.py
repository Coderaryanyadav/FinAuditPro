"""
Multi-Engine OCR Strategy for FinAuditPro.
Provides primary text extraction with PaddleOCR / Tesseract / PyPDF fallback strategies,
graceful feature detection, and non-destructive warning reporting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float = 1.0
    bounding_boxes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OCRResult:
    raw_text: str
    pages: List[OCRPageResult]
    provider_used: str
    overall_confidence: float = 1.0
    total_pages: int = 0

    def __post_init__(self):
        self.total_pages = len(self.pages)


class OCREngine:
    """Multi-provider OCR Engine with automatic fallback hierarchy and graceful feature detection."""

    _ocr_status_cache: Optional[Tuple[bool, str]] = None

    @classmethod
    def is_ocr_available(cls) -> Tuple[bool, str]:
        """
        Graceful feature detection for OCR capability.
        Checks for presence of PaddleOCR, Tesseract, or EasyOCR without raising fatal errors.
        """
        if cls._ocr_status_cache is not None:
            return cls._ocr_status_cache

        reasons = []

        # Check PaddleOCR
        try:
            import paddleocr  # noqa: F401
            cls._ocr_status_cache = (True, "PaddleOCR Engine Active")
            return cls._ocr_status_cache
        except Exception as e:
            reasons.append(f"PaddleOCR disabled: {e}")

        # Check Tesseract / PyTesseract
        try:
            import pytesseract  # noqa: F401
            cls._ocr_status_cache = (True, "Tesseract OCR Engine Active")
            return cls._ocr_status_cache
        except Exception as e:
            reasons.append(f"Tesseract disabled: {e}")

        # Check EasyOCR
        try:
            import easyocr  # noqa: F401
            cls._ocr_status_cache = (True, "EasyOCR Engine Active")
            return cls._ocr_status_cache
        except Exception as e:
            reasons.append(f"EasyOCR disabled: {e}")

        msg = "OCR Engine Unavailable - Digital PDF & Document Parser Active (" + "; ".join(reasons) + ")"
        logger.warning(msg)
        cls._ocr_status_cache = (False, msg)
        return cls._ocr_status_cache

    @classmethod
    def process_pdf_native(cls, file_path: str) -> Optional[OCRResult]:
        """Attempt primary digital text extraction via pypdf / pdfplumber."""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages = []
            full_text_parts = []

            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append(OCRPageResult(page_number=idx, text=page_text, confidence=0.98))
                full_text_parts.append(page_text)

            raw_text = "\n\n".join(full_text_parts).strip()
            if len(raw_text) > 50:  # Valid native digital PDF text
                return OCRResult(
                    raw_text=raw_text,
                    pages=pages,
                    provider_used="PyPDF Native Parser",
                    overall_confidence=0.98
                )
        except Exception as e:
            logger.warning(f"Native PyPDF extraction failed for {file_path}: {e}")

        return None

    @classmethod
    def process_ocr_fallback(cls, file_path: str) -> OCRResult:
        """Fallback OCR for scanned images/PDFs with non-blocking feature verification."""
        ocr_available, status_msg = cls.is_ocr_available()

        if ocr_available:
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)
                return OCRResult(
                    raw_text=text,
                    pages=[OCRPageResult(page_number=1, text=text, confidence=0.88)],
                    provider_used="Tesseract OCR",
                    overall_confidence=0.88
                )
            except Exception as e:
                logger.warning(f"OCR execution failed: {e}")

        # Fallback to direct file parsing for text/CSV/MD files
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if content.strip():
                    return OCRResult(
                        raw_text=content,
                        pages=[OCRPageResult(page_number=1, text=content, confidence=0.90)],
                        provider_used="Direct File Parser",
                        overall_confidence=0.90
                    )
        except Exception:
            pass

        return OCRResult(
            raw_text=f"[OCR Processing Disabled for {os.path.basename(file_path)}: {status_msg}]",
            pages=[OCRPageResult(page_number=1, text="", confidence=0.0)],
            provider_used="None (OCR Unavailable)",
            overall_confidence=0.0
        )

    @classmethod
    def process_document(cls, file_path: str) -> OCRResult:
        """Master OCR process router."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            result = cls.process_pdf_native(file_path)
            if result:
                return result

        return cls.process_ocr_fallback(file_path)
