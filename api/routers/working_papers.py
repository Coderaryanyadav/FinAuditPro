from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.middleware.rbac import require_permission
from api.schemas.working_paper import IndexCreate, WorkingPaperCreate, StatusUpdate, WorkingPaperRead
from database.models import User, WorkingPaper
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.working_paper_service import WorkingPaperService
from security.rbac import Permission
from core.exceptions import ValidationError, EntityNotFoundError, AuthError

router = APIRouter(prefix="/working-papers", tags=["Working Papers"])


@router.get("/index/{engagement_id}")
def get_indices(
    engagement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch indices for engagement."""
    wp_repo = WorkingPaperRepository(db)
    wp_service = WorkingPaperService(wp_repo)
    indices = wp_service.get_indices(engagement_id)
    return [
        {"id": idx.id, "section_code": idx.section_code, "section_name": idx.section_name}
        for idx in indices
    ]


@router.post("/index", status_code=status.HTTP_201_CREATED)
def create_index(
    request: IndexCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EDIT_WORKING_PAPERS))
):
    """Create working paper index section."""
    wp_repo = WorkingPaperRepository(db)
    wp_service = WorkingPaperService(wp_repo)
    try:
        idx = wp_service.create_index(
            engagement_id=request.engagement_id,
            section_code=request.section_code,
            section_name=request.section_name
        )
        return {"id": idx.id, "section_code": idx.section_code, "section_name": idx.section_name}
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/paper", response_model=WorkingPaperRead, status_code=status.HTTP_201_CREATED)
def create_paper(
    request: WorkingPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.EDIT_WORKING_PAPERS))
):
    """Create new working paper."""
    wp_repo = WorkingPaperRepository(db)
    wp_service = WorkingPaperService(wp_repo)
    try:
        return wp_service.create_paper(
            index_id=request.index_id,
            title=request.title,
            prepared_by_id=request.prepared_by_id
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/paper/index/{index_id}", response_model=List[WorkingPaperRead])
def get_papers_by_index(
    index_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all working papers for an index."""
    wp_repo = WorkingPaperRepository(db)
    wp_service = WorkingPaperService(wp_repo)
    return wp_service.get_papers_by_index(index_id)


@router.put("/paper/{paper_id}/status", response_model=WorkingPaperRead)
def update_status(
    paper_id: int,
    request: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.REVIEW_WORKING_PAPERS))
):
    """Update working paper review status."""
    wp_repo = WorkingPaperRepository(db)
    wp_service = WorkingPaperService(wp_repo)
    paper = wp_repo.session.query(WorkingPaper).filter_by(id=paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Working paper {paper_id} not found")

    try:
        return wp_service.update_status(paper=paper, status=request.status)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
