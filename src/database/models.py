import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Float, Boolean, Index
)
from sqlalchemy.orm import declarative_base, relationship, object_session

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(50), default='Articled Assistant') # Partner, Manager, Articled Assistant
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    teams = relationship("AuditTeam", back_populates="user", cascade="all, delete-orphan")
    prepared_papers = relationship("WorkingPaper", foreign_keys='WorkingPaper.prepared_by_id', back_populates="prepared_by")
    reviewed_papers = relationship("WorkingPaper", foreign_keys='WorkingPaper.reviewed_by_id', back_populates="reviewed_by")

class ClientIndustry(Base):
    __tablename__ = 'client_industries'
    id = Column(Integer, primary_key=True)
    industry_name = Column(String(100), nullable=False, unique=True)
    default_risk_profile = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    clients = relationship("Client", back_populates="industry_rel")

    def __str__(self):
        return self.industry_name or ""

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    gst_number = Column(String(15), nullable=True, index=True)
    pan_number = Column(String(10), nullable=True, index=True)
    cin = Column(String(21), nullable=True)
    registered_address = Column(Text, nullable=True)
    industry_id = Column(Integer, ForeignKey('client_industries.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    industry_rel = relationship("ClientIndustry", back_populates="clients")
    engagements = relationship("Engagement", back_populates="client", cascade="all, delete-orphan")
    kmps = relationship("KeyManagementPersonnel", back_populates="client", cascade="all, delete-orphan")

    @property
    def industry(self):
        if self.industry_rel:
            return self.industry_rel.industry_name
        return getattr(self, '_temp_industry', None)

    @industry.setter
    def industry(self, value):
        if isinstance(value, ClientIndustry):
            self.industry_rel = value
            self._temp_industry = value.industry_name
        elif isinstance(value, str) and value.strip():
            val_str = value.strip()
            self._temp_industry = val_str
            sess = object_session(self)
            if sess:
                existing = sess.query(ClientIndustry).filter_by(industry_name=val_str).first()
                if existing:
                    self.industry_rel = existing
                else:
                    self.industry_rel = ClientIndustry(industry_name=val_str)
            else:
                self.industry_rel = ClientIndustry(industry_name=val_str)
        else:
            self.industry_rel = None
            self._temp_industry = None

class KeyManagementPersonnel(Base):
    __tablename__ = 'kmp'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    name = Column(String(100), nullable=False)
    din = Column(String(20), nullable=True)
    designation = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    client = relationship("Client", back_populates="kmps")

class FinancialYear(Base):
    __tablename__ = 'financial_years'
    id = Column(Integer, primary_key=True)
    label = Column(String(20), nullable=False, unique=True) # e.g., '2024-25'
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagements = relationship("Engagement", back_populates="financial_year")

class Engagement(Base):
    __tablename__ = 'engagements'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year_id = Column(Integer, ForeignKey('financial_years.id'), nullable=False)
    audit_type = Column(String(50), nullable=False) # Statutory, Tax, Internal
    status = Column(String(50), default='Planning') # Planning, Execution, Reporting, Completed
    engagement_letter_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (
        Index('idx_client_fy', 'client_id', 'financial_year_id', unique=True),
    )

    client = relationship("Client", back_populates="engagements")
    financial_year = relationship("FinancialYear", back_populates="engagements")
    teams = relationship("AuditTeam", back_populates="engagement", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="engagement", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="engagement", cascade="all, delete-orphan")
    materiality = relationship("MaterialityCalculation", back_populates="engagement", cascade="all, delete-orphan")
    wp_indices = relationship("WorkingPaperIndex", back_populates="engagement", cascade="all, delete-orphan")
    compliance_tasks = relationship("ComplianceTask", back_populates="engagement", cascade="all, delete-orphan")

class AuditProject(Base):
    __tablename__ = 'audit_projects'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year = Column(String(50), default='2025-26')
    status = Column(String(50), default='In Progress')
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(50), default='Low')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    client = relationship("Client")

class AuditTeam(Base):
    __tablename__ = 'audit_teams'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role_in_engagement = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    engagement = relationship("Engagement", back_populates="teams")
    user = relationship("User", back_populates="teams")

class MaterialityCalculation(Base):
    __tablename__ = 'materiality_calculations'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    benchmark_used = Column(String(100), nullable=True)
    benchmark_amount = Column(Float, nullable=True)
    overall_materiality = Column(Float, nullable=True)
    performance_materiality = Column(Float, nullable=True)
    sum_threshold = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement", back_populates="materiality")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=True)
    audit_id = Column(Integer, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=True)
    doc_type = Column(String(50), default='Uploaded')
    upload_status = Column(String(50), default='Uploaded')
    is_vectorized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement", back_populates="documents")
    evidence_links = relationship("EvidenceLink", back_populates="document", cascade="all, delete-orphan")

class Risk(Base):
    __tablename__ = 'risks'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    description = Column(Text, nullable=False)
    likelihood = Column(String(50), nullable=True) # High, Medium, Low
    impact = Column(String(50), nullable=True)
    is_significant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement", back_populates="risks")

class ComplianceTask(Base):
    __tablename__ = 'compliance_tasks'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    task_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement", back_populates="compliance_tasks")

class WorkingPaperIndex(Base):
    __tablename__ = 'working_paper_index'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    section_code = Column(String(10), nullable=False) # e.g. 'A'
    section_name = Column(String(100), nullable=False) # e.g. 'Fixed Assets'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement", back_populates="wp_indices")
    working_papers = relationship("WorkingPaper", back_populates="index", cascade="all, delete-orphan")

class WorkingPaper(Base):
    __tablename__ = 'working_papers'
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit_projects.id'), nullable=True)
    index_id = Column(Integer, ForeignKey('working_paper_index.id'), nullable=False)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    status = Column(String(50), default='Draft')
    prepared_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    audit_project = relationship("AuditProject", backref="working_papers")
    index = relationship("WorkingPaperIndex", back_populates="working_papers")
    prepared_by = relationship("User", foreign_keys=[prepared_by_id], back_populates="prepared_papers")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id], back_populates="reviewed_papers")
    procedures = relationship("AuditProcedure", back_populates="working_paper", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="working_paper", cascade="all, delete-orphan")
    review_notes = relationship("ReviewNote", back_populates="working_paper", cascade="all, delete-orphan")

class AuditProcedure(Base):
    __tablename__ = 'audit_procedures'
    id = Column(Integer, primary_key=True)
    working_paper_id = Column(Integer, ForeignKey('working_papers.id'), nullable=False)
    description = Column(Text, nullable=False)
    assertion_covered = Column(String(100), nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    working_paper = relationship("WorkingPaper", back_populates="procedures")
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    evidence_links = relationship("EvidenceLink", back_populates="procedure", cascade="all, delete-orphan")

class EvidenceLink(Base):
    __tablename__ = 'evidence_links'
    id = Column(Integer, primary_key=True)
    procedure_id = Column(Integer, ForeignKey('audit_procedures.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    page_reference = Column(Integer, nullable=True)
    bounding_box_data = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    procedure = relationship("AuditProcedure", back_populates="evidence_links")
    document = relationship("Document", back_populates="evidence_links")

class Finding(Base):
    __tablename__ = 'findings'
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit_projects.id'), nullable=True)
    working_paper_id = Column(Integer, ForeignKey('working_papers.id'), nullable=True)
    description = Column(Text, nullable=False)
    financial_impact = Column(Float, nullable=True)
    severity = Column(String(50), default='Low') # High, Medium, Low
    risk_level = Column(String(50), default='Low')
    ai_confidence_score = Column(Integer, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    audit_project = relationship("AuditProject", backref="findings")
    working_paper = relationship("WorkingPaper", back_populates="findings")

class ReviewNote(Base):
    __tablename__ = 'review_notes'
    id = Column(Integer, primary_key=True)
    working_paper_id = Column(Integer, ForeignKey('working_papers.id'), nullable=False)
    note_text = Column(Text, nullable=False)
    raised_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(50), default='Open') # Open, Cleared, Closed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    working_paper = relationship("WorkingPaper", back_populates="review_notes")
    raised_by = relationship("User", foreign_keys=[raised_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

class DocumentPage(Base):
    __tablename__ = 'document_pages'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    page_number = Column(Integer, nullable=False)
    ocr_text = Column(Text, nullable=True)
    layout_metadata = Column(Text, nullable=True) # JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class RiskProcedureLink(Base):
    __tablename__ = 'risk_procedure_links'
    id = Column(Integer, primary_key=True)
    risk_id = Column(Integer, ForeignKey('risks.id'), nullable=False)
    procedure_id = Column(Integer, ForeignKey('audit_procedures.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditReport(Base):
    __tablename__ = 'audit_reports'
    id = Column(Integer, primary_key=True)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=False)
    version_label = Column(String(50), nullable=False)
    report_text = Column(Text, nullable=True)
    pdf_hash = Column(String(64), nullable=True)
    generated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    engagement = relationship("Engagement")
    generated_by = relationship("User", foreign_keys=[generated_by_id])

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    engagement_id = Column(Integer, ForeignKey('engagements.id'), nullable=True)
    action = Column(String(100), nullable=False)
    target_entity = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

