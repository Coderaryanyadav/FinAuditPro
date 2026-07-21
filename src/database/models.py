import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    gst_number = Column(String(15), nullable=True)
    pan_number = Column(String(10), nullable=True)
    industry = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    audits = relationship("AuditProject", back_populates="client", cascade="all, delete-orphan")

class AuditProject(Base):
    __tablename__ = 'audit_projects'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year = Column(String(10), nullable=False) # e.g., '2025-26'
    status = Column(String(20), default='Not Started') # Not Started, In Progress, Pending Review, Completed
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(10), default='Unknown') # Low, Medium, High
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    client = relationship("Client", back_populates="audits")
    documents = relationship("Document", back_populates="audit", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="audit", cascade="all, delete-orphan")
    working_papers = relationship("WorkingPaper", back_populates="audit", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit_projects.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=True) # e.g., 'Bank Statement', 'GST Return'
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    audit = relationship("AuditProject", back_populates="documents")

class Finding(Base):
    __tablename__ = 'findings'
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit_projects.id'), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(String(10), default='Low')
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    audit = relationship("AuditProject", back_populates="findings")

class WorkingPaper(Base):
    __tablename__ = 'working_papers'
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit_projects.id'), nullable=False)
    objective = Column(Text, nullable=True)
    procedure = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    observation = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    audit = relationship("AuditProject", back_populates="working_papers")
