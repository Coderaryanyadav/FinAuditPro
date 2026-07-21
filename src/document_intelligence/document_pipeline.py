"""
Master Document Ingestion Pipeline for FinAuditPro.
Orchestrates: Validate -> Hash -> Parse -> OCR -> Clean -> Classify -> Extract Tables -> Extract Metadata -> Chunk -> Embed -> Index.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import logging

from .document_validator import DocumentValidator
from .document_hash import DocumentHasher
from .document_parser import DocumentParser, ParsedDocument
from .document_classifier import DocumentClassifier, DocumentCategory
from .metadata_extractor import MetadataExtractor, ExtractedMetadata
from .chunking_engine import ChunkingEngine, DocumentChunk
from .document_indexer import DocumentIndexer
from workflow.workflow_events import WorkflowEventManager, WorkflowEvent, EventType

logger = logging.getLogger(__name__)

@dataclass
class IngestionResult:
    document_id: Optional[int]
    file_path: str
    file_name: str
    file_hash: str
    category: str
    pages_count: int
    tables_count: int
    chunks_count: int
    extracted_metadata: ExtractedMetadata
    processing_time_seconds: float
    status: str = "SUCCESS"
    error_message: Optional[str] = None


class DocumentPipeline:
    """Production-grade Document Ingestion Pipeline Engine."""

    def __init__(self, document_indexer: Optional[DocumentIndexer] = None, event_manager: Optional[WorkflowEventManager] = None):
        self.indexer = document_indexer or DocumentIndexer()
        self.event_manager = event_manager or WorkflowEventManager()

    def process_and_ingest(
        self,
        file_path: str,
        engagement_id: int,
        client_id: int,
        document_id: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> IngestionResult:
        """
        Executes end-to-end ingestion pipeline with progress callbacks.
        """
        start_time = time.time()

        def _notify(stage_name: str, percent: float):
            if progress_callback:
                try:
                    progress_callback(stage_name, percent)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

        # 1. Validation
        _notify("Validating File", 10.0)
        DocumentValidator.validate_file(file_path)

        # 2. Cryptographic Hash
        _notify("Computing Document Hash", 20.0)
        file_hash = DocumentHasher.compute_file_hash(file_path)

        # 3. Parsing & OCR
        _notify("Extracting Text & OCR", 40.0)
        parsed_doc: ParsedDocument = DocumentParser.parse_document(file_path)

        # 4. Classification
        _notify("Classifying Financial Category", 55.0)
        category: DocumentCategory = DocumentClassifier.classify_text(parsed_doc.cleaned_text, parsed_doc.file_name)

        # 5. Metadata Extraction
        _notify("Extracting Metadata & Identifiers", 70.0)
        meta: ExtractedMetadata = MetadataExtractor.extract_metadata(parsed_doc.cleaned_text)

        # 5b. Rule Engine Evaluation
        _notify("Running Enterprise Audit Rules", 78.0)
        try:
            from rule_engine.rule_engine import AuditRuleEngine
            rule_engine = AuditRuleEngine()
            
            # Extract real transaction amounts from parsed document tables
            extracted_amounts = []
            if parsed_doc.tables:
                import re
                for tbl in parsed_doc.tables:
                    for cell in tbl.get("cells", []):
                        matches = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b", str(cell))
                        for m in matches:
                            try:
                                val = float(m.replace(",", ""))
                                if val > 0:
                                    extracted_amounts.append(val)
                            except ValueError:
                                pass

            rule_eval = rule_engine.evaluate_document({
                "text": parsed_doc.cleaned_text,
                "gstin": meta.gstin,
                "pan": meta.pan,
                "file_name": parsed_doc.file_name,
                "transaction_amounts": extracted_amounts
            })
            if rule_eval.failed_rules:
                from database.database import SessionLocal
                from database.models import Finding
                session = SessionLocal()
                for failed in rule_eval.failed_rules:
                    impact = max(extracted_amounts) if extracted_amounts else 0.0
                    finding = Finding(
                        description=f"[{failed.rule_id}] {failed.rule_name}: {failed.description}",
                        severity=failed.severity.value,
                        risk_level=failed.severity.value,
                        financial_impact=impact
                    )
                    session.add(finding)
                session.commit()
                session.close()
        except Exception as e:
            logger.warning(f"Rule Engine evaluation warning: {e}")

        # 6. Chunking
        _notify("Chunking Document Text & Tables", 85.0)
        base_meta = {
            "file_name": parsed_doc.file_name,
            "category": category.value,
            "gstin": meta.gstin,
            "pan": meta.pan,
            "financial_year": meta.financial_year,
            "file_hash": file_hash,
        }
        chunks: List[DocumentChunk] = ChunkingEngine.chunk_document(
            text=parsed_doc.cleaned_text,
            tables=parsed_doc.tables,
            base_metadata=base_meta
        )

        # 7. Vector Indexing
        _notify("Generating Vector Embeddings & Indexing", 95.0)
        doc_id = document_id if document_id is not None else int(time.time())
        indexed_chunks = self.indexer.index_document_chunks(
            document_id=doc_id,
            engagement_id=engagement_id,
            client_id=client_id,
            chunks=chunks
        )

        # 8. Event Dispatching
        _notify("Ingestion Completed", 100.0)
        event = WorkflowEvent(
            event_type=EventType.DOCUMENT_UPLOADED,
            engagement_id=engagement_id,
            client_id=client_id,
            payload={
                "document_id": doc_id,
                "file_name": parsed_doc.file_name,
                "category": category.value,
                "chunks_count": indexed_chunks
            }
        )
        self.event_manager.dispatch(event)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Ingested {parsed_doc.file_name} in {elapsed}s. Category: {category.value}, Chunks: {indexed_chunks}")

        return IngestionResult(
            document_id=doc_id,
            file_path=file_path,
            file_name=parsed_doc.file_name,
            file_hash=file_hash,
            category=category.value,
            pages_count=parsed_doc.pages_count,
            tables_count=len(parsed_doc.tables),
            chunks_count=indexed_chunks,
            extracted_metadata=meta,
            processing_time_seconds=elapsed,
            status="SUCCESS"
        )
