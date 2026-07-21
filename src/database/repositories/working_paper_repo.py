from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import WorkingPaper, WorkingPaperIndex, Finding, AuditProcedure

class WorkingPaperRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_indices_by_engagement(self, engagement_id: int) -> List[WorkingPaperIndex]:
        return self.session.query(WorkingPaperIndex).filter(WorkingPaperIndex.engagement_id == engagement_id).all()

    def create_index(self, engagement_id: int, section_code: str, section_name: str) -> WorkingPaperIndex:
        idx = WorkingPaperIndex(
            engagement_id=engagement_id,
            section_code=section_code,
            section_name=section_name
        )
        self.session.add(idx)
        self.session.commit()
        self.session.refresh(idx)
        return idx

    def get_papers_by_index(self, index_id: int) -> List[WorkingPaper]:
        return self.session.query(WorkingPaper).filter(WorkingPaper.index_id == index_id).all()

    def create_paper(self, index_id: int, title: str, prepared_by_id: int) -> WorkingPaper:
        paper = WorkingPaper(
            index_id=index_id,
            title=title,
            prepared_by_id=prepared_by_id,
            status='Draft'
        )
        self.session.add(paper)
        self.session.commit()
        self.session.refresh(paper)
        return paper

    def add_finding(self, working_paper_id: int, description: str, severity: str = 'Low') -> Finding:
        finding = Finding(
            working_paper_id=working_paper_id,
            description=description,
            severity=severity
        )
        self.session.add(finding)
        self.session.commit()
        self.session.refresh(finding)
        return finding
