"""
FinAuditPro Document Intelligence Engine Package
Provides automated document ingestion, OCR parsing, table extraction, metadata parsing, chunking, and vector indexing.
"""

from .document_hash import DocumentHasher
from .document_validator import DocumentValidator, DocumentValidationError
from .text_cleaner import TextCleaner
from .document_classifier import DocumentClassifier, DocumentCategory
from .metadata_extractor import MetadataExtractor, ExtractedMetadata
from .table_extractor import TableExtractor, ExtractedTable
from .ocr_engine import OCREngine, OCRResult
from .document_parser import DocumentParser, ParsedDocument
from .chunking_engine import ChunkingEngine, DocumentChunk
from .embedding_service import EmbeddingService
from .document_indexer import DocumentIndexer
from .document_pipeline import DocumentPipeline, IngestionResult

__all__ = [
    "DocumentHasher",
    "DocumentValidator",
    "DocumentValidationError",
    "TextCleaner",
    "DocumentClassifier",
    "DocumentCategory",
    "MetadataExtractor",
    "ExtractedMetadata",
    "TableExtractor",
    "ExtractedTable",
    "OCREngine",
    "OCRResult",
    "DocumentParser",
    "ParsedDocument",
    "ChunkingEngine",
    "DocumentChunk",
    "EmbeddingService",
    "DocumentIndexer",
    "DocumentPipeline",
    "IngestionResult",
]
