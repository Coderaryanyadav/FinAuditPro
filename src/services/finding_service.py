from typing import List
from core.exceptions import ValidationError
from database.repositories.working_paper_repo import WorkingPaperRepository
from database.models import Finding

class FindingService:
    """
    Service responsible for managing Audit Findings.
    
    Repositories used:
    - WorkingPaperRepository
    
    Business Rules:
    - Severity must be one of (High, Medium, Low).
    - Findings must be linked to a Working Paper.
    """

    VALID_SEVERITY = ['High', 'Medium', 'Low']

    def __init__(self, wp_repo: WorkingPaperRepository):
        self.wp_repo = wp_repo

    def create_finding(self, working_paper_id: int, description: str, severity: str = 'Low', financial_impact: float = 0.0) -> Finding:
        """Create a new finding."""
        if not description:
            raise ValidationError("Finding description is required.")
        if severity not in self.VALID_SEVERITY:
            raise ValidationError(f"Invalid severity. Must be one of {self.VALID_SEVERITY}")
            
        finding = self.wp_repo.add_finding(working_paper_id, description, severity)
        finding.financial_impact = financial_impact
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(finding)
        return finding

    def resolve_finding(self, finding_id: int) -> Finding:
        """Mark finding as resolved."""
        finding = self.wp_repo.session.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise ValidationError(f"Finding {finding_id} not found.")
            
        finding.is_resolved = True
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(finding)
        return finding
