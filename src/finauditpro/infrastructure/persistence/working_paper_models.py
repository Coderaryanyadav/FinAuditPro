"""SQLAlchemy ORM models for Working Papers, Review Notes, and Sign-offs."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class WorkingPaperModel(Base):
    __tablename__ = "working_papers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True)
    index_reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft", index=True)
    conclusion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    preparer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_locked: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class WorkingPaperSectionModel(Base):
    __tablename__ = "working_paper_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    working_paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class WorkingPaperLinkModel(Base):
    __tablename__ = "working_paper_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    working_paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    link_type: Mapped[str] = mapped_column(String(50), nullable=False)  # procedure, risk, finding, evidence
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ReviewNoteModel(Base):
    __tablename__ = "review_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    working_paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    raised_by: Mapped[str] = mapped_column(String(255), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Open", index=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cleared_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class SignOffRecordModel(Base):
    __tablename__ = "sign_offs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    working_paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("working_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(100), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    disclaimer_notice: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
