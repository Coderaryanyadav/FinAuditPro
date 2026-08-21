from typing import List
from database.repositories.working_paper_repo import WorkingPaperRepository
from database.models import ReviewNote
from core.exceptions import ValidationError, EntityNotFoundError

class ReviewNoteService:
    """
    Service responsible for managing Review Notes.
    
    Repositories used:
    - WorkingPaperRepository (manages session for WPs and their notes)
    """

    VALID_STATUSES = ['Open', 'Cleared', 'Closed']

    def __init__(self, wp_repo: WorkingPaperRepository):
        self.wp_repo = wp_repo

    def create_note(self, working_paper_id: int, note_text: str, raised_by_id: int, assigned_to_id: int = None) -> ReviewNote:
        """Create a new review note on a working paper."""
        if not note_text:
            raise ValidationError("Note text is required.")
            
        note = ReviewNote(
            working_paper_id=working_paper_id,
            note_text=note_text,
            raised_by_id=raised_by_id,
            assigned_to_id=assigned_to_id
        )
        self.wp_repo.session.add(note)
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(note)
        return note

    def update_status(self, note_id: int, status: str) -> ReviewNote:
        """Update review note status."""
        if status not in self.VALID_STATUSES:
            raise ValidationError(f"Invalid status: {status}")
            
        note = self.wp_repo.session.query(ReviewNote).filter(ReviewNote.id == note_id).first()
        if not note:
            raise EntityNotFoundError(f"Review Note {note_id} not found.")
            
        note.status = status
        self.wp_repo.session.commit()
        self.wp_repo.session.refresh(note)
        return note
