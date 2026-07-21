from typing import Optional
from core.exceptions import ValidationError
from database.repositories.working_paper_repo import WorkingPaperRepository
from database.models import EvidenceLink

class EvidenceService:
    """
    Service responsible for managing Evidence links.
    
    Repositories used:
    - WorkingPaperRepository (which can handle EvidenceLink creation via session)
    
    Business Rules:
    - Evidence must correctly link a Document to a Procedure with optional bounding boxes.
    """

    def __init__(self, wp_repo: WorkingPaperRepository):
        self.wp_repo = wp_repo

    def link_evidence(self, procedure_id: int, document_id: int, page_reference: int = None, bounding_box_data: str = None) -> EvidenceLink:
        """Create a link between an audit procedure and a document."""
        if not procedure_id or not document_id:
            raise ValidationError("Procedure ID and Document ID are required to link evidence.")
            
        link = EvidenceLink(
            procedure_id=procedure_id,
            document_id=document_id,
            page_reference=page_reference,
            bounding_box_data=bounding_box_data
        )
        self.wp_repo.session.add(link)
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(link)
        return link
