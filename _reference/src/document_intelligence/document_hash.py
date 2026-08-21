"""
Document Hashing & Duplicate Detection Module.
Computes SHA-256 digital signatures for document files and binary streams.
"""

import hashlib
import os

class DocumentHasher:
    """Computes cryptographic hashes for files to guarantee deduplication and track versioning."""

    @staticmethod
    def compute_file_hash(file_path: str, block_size: int = 65536) -> str:
        """Calculate SHA-256 hash of a file on disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found for hashing: {file_path}")

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                hasher.update(block)
        return hasher.hexdigest()

    @staticmethod
    def compute_bytes_hash(data: bytes) -> str:
        """Calculate SHA-256 hash of raw in-memory bytes."""
        return hashlib.sha256(data).hexdigest()
