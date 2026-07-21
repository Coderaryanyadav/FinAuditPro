"""
ICAI-Standard Working Paper Engine for FinAuditPro.
Generates structured Audit Working Papers with assertions, evidence citations, AI findings, and review status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from .digital_signature import SignatureBlock

@dataclass
class ICAIWorkingPaper:
    working_paper_number: str  # e.g. "WP-AUD-2026-001"
    audit_area: str  # e.g. "Revenue Recognition / GST Reconciliation"
    prepared_by: str
    reviewed_by: Optional[str] = None
    review_status: str = "DRAFT"  # DRAFT, PENDING_REVIEW, APPROVED
    audit_objective: str = ""
    assertions: List[str] = field(default_factory=list)  # Completeness, Existence, Accuracy, Valuation
    procedure_performed: str = ""
    evidence_citations: List[str] = field(default_factory=list)
    supporting_documents: List[str] = field(default_factory=list)
    ai_findings: List[str] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)
    risk_rating: str = "Low Risk"
    cross_references: List[str] = field(default_factory=list)
    review_notes: List[str] = field(default_factory=list)
    conclusion: str = ""
    signature_block: Optional[SignatureBlock] = None
    version_number: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "working_paper_number": self.working_paper_number,
            "audit_area": self.audit_area,
            "prepared_by": self.prepared_by,
            "reviewed_by": self.reviewed_by or "Unassigned",
            "review_status": self.review_status,
            "audit_objective": self.audit_objective,
            "assertions": self.assertions,
            "procedure_performed": self.procedure_performed,
            "evidence_citations": self.evidence_citations,
            "supporting_documents": self.supporting_documents,
            "ai_findings": self.ai_findings,
            "failed_rules": self.failed_rules,
            "risk_rating": self.risk_rating,
            "cross_references": self.cross_references,
            "review_notes": self.review_notes,
            "conclusion": self.conclusion,
            "signature_block": self.signature_block.to_dict() if self.signature_block else None,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
        }


class WorkingPaperEngine:
    """Generates ICAI-standard working papers for audit files."""

    @staticmethod
    def generate_working_paper(
        wp_number: str,
        audit_area: str,
        prepared_by: str,
        objective: str,
        procedure: str,
        ai_findings: List[str] = None,
        failed_rules: List[str] = None,
        conclusion: str = ""
    ) -> ICAIWorkingPaper:
        """Instantiates a complete ICAI audit working paper."""
        return ICAIWorkingPaper(
            working_paper_number=wp_number,
            audit_area=audit_area,
            prepared_by=prepared_by,
            audit_objective=objective,
            assertions=["Completeness", "Accuracy", "Existence", "Valuation"],
            procedure_performed=procedure,
            ai_findings=ai_findings or [],
            failed_rules=failed_rules or [],
            risk_rating="Low Risk" if not failed_rules else "High Risk",
            conclusion=conclusion or "Audit procedure completed without material exception."
        )
