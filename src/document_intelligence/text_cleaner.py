"""
OCR & Document Text Cleaner Module for FinAuditPro.
Normalizes extracted text, strips OCR artifacts, and cleans redundant headers/footers.
"""

import re
from typing import List

class TextCleaner:
    """Cleans and normalizes raw OCR text for vector indexing and LLM prompt consumption."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Applies normalization pipeline to raw document text."""
        if not text:
            return ""

        # 1. Normalize line endings
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Remove non-printable control characters except line breaks
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", cleaned)

        # 3. Replace multiple spaces/tabs with single space
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 4. Remove excessive consecutive blank lines (limit to max 2)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 5. Fix common broken OCR hyphens (e.g. "state-\nment" -> "statement")
        cleaned = re.sub(r"(\w+)-\n(\w+)", r"\1\2", cleaned)

        return cleaned.strip()

    @staticmethod
    def strip_headers_footers(pages_text: List[str], header_margin: int = 2, footer_margin: int = 2) -> List[str]:
        """Strips repeating header and footer lines across multi-page documents."""
        if len(pages_text) <= 1:
            return pages_text

        cleaned_pages = []
        for page in pages_text:
            lines = page.split("\n")
            if len(lines) > (header_margin + footer_margin):
                # Remove first header_margin lines if page number line
                trimmed = lines[header_margin:-footer_margin] if footer_margin > 0 else lines[header_margin:]
                cleaned_pages.append("\n".join(trimmed))
            else:
                cleaned_pages.append(page)

        return cleaned_pages
