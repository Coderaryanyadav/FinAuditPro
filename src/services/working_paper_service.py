from typing import List, Optional
from core.exceptions import ValidationError, EntityNotFoundError
from database.repositories.working_paper_repo import WorkingPaperRepository
from database.models import WorkingPaper, WorkingPaperIndex

class WorkingPaperService:
    """
    Service responsible for managing Working Papers.
    
    Repositories used:
    - WorkingPaperRepository
    
    Business Rules:
    - Papers must belong to an Index.
    - Status transitions (Draft -> Review -> Completed).
    """

    VALID_STATUSES = ['Draft', 'Review', 'Completed']

    def __init__(self, wp_repo: WorkingPaperRepository):
        self.wp_repo = wp_repo

    def get_indices(self, engagement_id: int) -> List[WorkingPaperIndex]:
        """Fetch all indexes for an engagement."""
        return self.wp_repo.get_indices_by_engagement(engagement_id)

    def create_index(self, engagement_id: int, section_code: str, section_name: str) -> WorkingPaperIndex:
        """Create a new index section."""
        if not section_code or not section_name:
            raise ValidationError("Section code and name are required.")
        return self.wp_repo.create_index(engagement_id, section_code, section_name)

    def create_paper(self, index_id: int, title: str, prepared_by_id: int) -> WorkingPaper:
        """Create a new working paper."""
        if not title:
            raise ValidationError("Working paper title is required.")
        return self.wp_repo.create_paper(index_id, title, prepared_by_id)

    def get_papers_by_index(self, index_id: int) -> List[WorkingPaper]:
        """Get all papers in a specific index."""
        return self.wp_repo.get_papers_by_index(index_id)

    def update_status(self, paper: WorkingPaper, status: str) -> WorkingPaper:
        """Update working paper status."""
        if status not in self.VALID_STATUSES:
            raise ValidationError(f"Invalid status: {status}")
        
        paper.status = status
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(paper)
        return paper
