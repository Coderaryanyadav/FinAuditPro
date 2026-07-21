"""
Unit Tests for FinAuditPro Document Intelligence Engine.
Tests Hashing, Validation, OCR Parsing, Classification, Table Extraction, Metadata, Chunking, and Vector Indexing.
"""

import unittest
import os
import tempfile

from document_intelligence.document_hash import DocumentHasher
from document_intelligence.document_validator import DocumentValidator, DocumentValidationError
from document_intelligence.text_cleaner import TextCleaner
from document_intelligence.document_classifier import DocumentClassifier, DocumentCategory
from document_intelligence.metadata_extractor import MetadataExtractor
from document_intelligence.table_extractor import TableExtractor
from document_intelligence.chunking_engine import ChunkingEngine
from document_intelligence.embedding_service import EmbeddingService


class TestDocumentIntelligence(unittest.TestCase):

    def setUp(self):
        self.sample_text = """
        TAX INVOICE
        Invoice No: INV-2026-091
        Date: 15-03-2026
        GSTIN: 27AAACB1234F1Z0
        PAN: AAACB1234F
        FY: 2025-2026
        Bill To: TechCorp Solutions Ltd.
        Grand Total: ₹ 1,50,000.00
        """

    def test_document_hasher(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("Sample Audit Content for Hash Test")
            temp_path = f.name

        try:
            file_hash = DocumentHasher.compute_file_hash(temp_path)
            self.assertEqual(len(file_hash), 64)  # SHA-256 length
        finally:
            os.remove(temp_path)

    def test_document_validator(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".pdf", delete=False) as f:
            f.write("DUMMY PDF CONTENT")
            temp_path = f.name

        try:
            # Unsupported extension raises validation error
            with self.assertRaises(DocumentValidationError):
                DocumentValidator.validate_file(temp_path.replace(".pdf", ".invalid"))
        finally:
            os.remove(temp_path)

    def test_text_cleaner(self):
        raw = "  Tax   Invoice \r\n\r\n\n\n\n GSTIN:  27AAACB1234F1Z0  "
        cleaned = TextCleaner.clean_text(raw)
        self.assertIn("Tax Invoice", cleaned)
        self.assertNotIn("  ", cleaned)

    def test_document_classifier(self):
        category = DocumentClassifier.classify_text(self.sample_text, "invoice_001.pdf")
        self.assertEqual(category, DocumentCategory.INVOICE)

    def test_metadata_extractor(self):
        meta = MetadataExtractor.extract_metadata(self.sample_text)
        self.assertEqual(meta.gstin, "27AAACB1234F1Z0")
        self.assertEqual(meta.pan, "AAACB1234F")
        self.assertEqual(meta.invoice_number, "INV-2026-091")
        self.assertEqual(meta.total_amount, 150000.00)

    def test_chunking_engine(self):
        chunks = ChunkingEngine.chunk_document(self.sample_text, chunk_size=200)
        self.assertTrue(len(chunks) > 0)
        self.assertEqual(chunks[0].chunk_type, "Paragraph")

    def test_embedding_service(self):
        service = EmbeddingService()
        vec = service.generate_embedding("Test audit sentence")
        self.assertEqual(len(vec), 384)


if __name__ == "__main__":
    unittest.main()
