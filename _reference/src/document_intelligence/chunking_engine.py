"""
Financial Document Chunking Engine for FinAuditPro.
Splits text into contextual semantic chunks (by Headings, Tables, Paragraphs, or Pages) with metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class DocumentChunk:
    chunk_index: int
    text: str
    chunk_type: str  # Paragraph, Table, Heading, Page Section
    page_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChunkingEngine:
    """Intelligently chunks document text into semantic units optimized for financial RAG."""

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_OVERLAP = 150

    @classmethod
    def chunk_document(
        cls,
        text: str,
        tables: List[Any] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        base_metadata: Dict[str, Any] = None
    ) -> List[DocumentChunk]:
        """
        Chunks text into semantic overlapping windows and appends extracted table chunks.
        """
        chunks: List[DocumentChunk] = []
        meta = base_metadata or {}
        chunk_idx = 0

        # 1. Chunk structured tables if present
        if tables:
            for tbl in tables:
                page_no = getattr(tbl, "page_number", 1)
                headers = getattr(tbl, "headers", [])
                rows = getattr(tbl, "rows", [])
                header_str = " | ".join(headers) if headers else ""

                # Batch table rows into chunk blocks of 15 rows
                batch_size = 15
                for i in range(0, len(rows), batch_size):
                    batch_rows = rows[i:i + batch_size]
                    row_strs = [" | ".join([str(c) for c in r]) for r in batch_rows]
                    table_text = f"TABLE (Page {page_no}):\n{header_str}\n" + "\n".join(row_strs)

                    chunk_meta = meta.copy()
                    chunk_meta.update({"page_number": page_no, "table_headers": headers})
                    chunks.append(
                        DocumentChunk(
                            chunk_index=chunk_idx,
                            text=table_text,
                            chunk_type="Table",
                            page_number=page_no,
                            metadata=chunk_meta
                        )
                    )
                    chunk_idx += 1

        # 2. Chunk paragraphs and text blocks
        if text:
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            current_buffer = ""

            for p in paragraphs:
                if len(current_buffer) + len(p) <= chunk_size:
                    current_buffer += f"\n\n{p}" if current_buffer else p
                else:
                    if current_buffer:
                        chunk_meta = meta.copy()
                        chunks.append(
                            DocumentChunk(
                                chunk_index=chunk_idx,
                                text=current_buffer,
                                chunk_type="Paragraph",
                                metadata=chunk_meta
                            )
                        )
                        chunk_idx += 1
                    current_buffer = p

            if current_buffer:
                chunk_meta = meta.copy()
                chunks.append(
                    DocumentChunk(
                        chunk_index=chunk_idx,
                        text=current_buffer,
                        chunk_type="Paragraph",
                        metadata=chunk_meta
                    )
                )

        return chunks
