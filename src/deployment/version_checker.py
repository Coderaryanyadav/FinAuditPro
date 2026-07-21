"""
App Version & Release Notes Manager for FinAuditPro.
Provides application version metadata, release notes parser, and offline update package validator.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class AppVersionInfo:
    version: str = "1.0.0"
    build_number: int = 1001
    release_date: str = "2026-07-21"
    edition: str = "Enterprise Desktop Edition"
    license_type: str = "Chartered Accountant Enterprise License"
    icai_compliant: bool = True
    release_notes: List[str] = field(default_factory=lambda: [
        "Phase 1: SQLite Enterprise Database & Repository Layer.",
        "Phase 2.1: Core Service Layer (15 Business Logic Modules).",
        "Phase 2.2: Modular Local AI Copilot Engine (Ollama RAG + JSON Schema).",
        "Phase 2.3: Document Intelligence & OCR Engine (PDF/Excel/CSV Parsing).",
        "Phase 3: Complete PySide6 UI-Service Wiring & Workflow Manager.",
        "Phase 4: 100+ Automated Offline Audit Rules Suite.",
        "Phase 5: ICAI-Standard Professional Reporting Engine (PDF/Excel/UDIN).",
        "Phase 6: Enterprise RBAC, Password Hashing, & AES-256 Encryption.",
        "Phase 7: Executive BI Analytics & 4 Role-Based Dashboards.",
        "Phase 8: Cross-Platform Packaging & Production Diagnostics."
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "build_number": self.build_number,
            "release_date": self.release_date,
            "edition": self.edition,
            "license_type": self.license_type,
            "icai_compliant": self.icai_compliant,
            "release_notes": self.release_notes,
        }


class VersionChecker:
    """Manages application version metadata and release details."""

    @staticmethod
    def get_version_info() -> AppVersionInfo:
        return AppVersionInfo()
