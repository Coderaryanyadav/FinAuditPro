from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import WorkingPaper, WorkingPaperIndex, Finding, AuditProcedure

class WorkingPaperRepository:
    def __init__(self, session: Session):
        self.session = session

    STANDARD_SECTIONS = [
        ("A", "A - Legal, Secretarial & General Permanent File"),
        ("B", "B - Financial Statements & Trial Balance Analysis"),
        ("C", "C - Property, Plant, Equipment & Intangibles"),
        ("D", "D - Inventories & Cost of Goods Sold"),
        ("E", "E - Cash, Bank & Trade Receivables"),
        ("F", "F - Revenue Recognition & Sales Verification"),
        ("G", "G - Operating Expenses & Statutory Payroll"),
        ("H", "H - Direct & Indirect Tax Compliance (GST & IT)"),
    ]

    def get_indices_by_engagement(self, engagement_id: int) -> List[WorkingPaperIndex]:
        indices = self.session.query(WorkingPaperIndex).filter(WorkingPaperIndex.engagement_id == engagement_id).order_by(WorkingPaperIndex.section_code).all()
        if not indices and engagement_id:
            for code, name in self.STANDARD_SECTIONS:
                idx = WorkingPaperIndex(engagement_id=engagement_id, section_code=code, section_name=name)
                self.session.add(idx)
            self.session.commit()
            indices = self.session.query(WorkingPaperIndex).filter(WorkingPaperIndex.engagement_id == engagement_id).order_by(WorkingPaperIndex.section_code).all()
        return indices

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
