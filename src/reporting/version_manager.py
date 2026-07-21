"""
Report Versioning & Revision History Manager for FinAuditPro.
Tracks version iterations (v1.0, v1.1, v2.0), reviewer changes, and approval timestamps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class ReportVersion:
    version_number: str  # e.g. "1.0", "1.1", "2.0"
    created_by: str
    reviewer_notes: str
    approval_status: str  # "DRAFT", "PENDING_REVIEW", "APPROVED"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    file_path: Optional[str] = None
    changes_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_number": self.version_number,
            "created_by": self.created_by,
            "reviewer_notes": self.reviewer_notes,
            "approval_status": self.approval_status,
            "timestamp": self.timestamp.isoformat(),
            "file_path": self.file_path,
            "changes_summary": self.changes_summary,
        }


class ReportVersionManager:
    """Manages report version iterations and audit revision trails."""

    def __init__(self, initial_version: str = "1.0"):
        self.versions: List[ReportVersion] = []
        self.current_version_str = initial_version

    def create_version(
        self,
        created_by: str,
        reviewer_notes: str = "",
        approval_status: str = "DRAFT",
        file_path: Optional[str] = None,
        changes_summary: str = ""
    ) -> ReportVersion:
        """Create and append a new report version entry."""
        if not self.versions:
            ver_num = "1.0"
        else:
            major, minor = map(int, self.current_version_str.split("."))
            if approval_status == "APPROVED":
                ver_num = f"{major + 1}.0"
            else:
                ver_num = f"{major}.{minor + 1}"

        self.current_version_str = ver_num
        ver_entry = ReportVersion(
            version_number=ver_num,
            created_by=created_by,
            reviewer_notes=reviewer_notes,
            approval_status=approval_status,
            file_path=file_path,
            changes_summary=changes_summary
        )
        self.versions.append(ver_entry)
        return ver_entry

    def get_latest_version(self) -> Optional[ReportVersion]:
        return self.versions[-1] if self.versions else None
