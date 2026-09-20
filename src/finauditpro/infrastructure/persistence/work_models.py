"""SQLAlchemy ORM models for Work Center tasks."""

from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finauditpro.infrastructure.persistence.database import Base


class WorkTaskModel(Base):
    """DB table storing authoritative and AI-suggested work tasks."""

    __tablename__ = "work_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=True
    )
    engagement_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=True
    )
    assignee: Mapped[str] = mapped_column(String(100), nullable=False, default="Unassigned")
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    due_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="TODO")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="MANUAL")
    linked_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_workpaper: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_finding: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_confirmed: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    client: Mapped[Any] = relationship("ClientModel", backref="work_tasks", lazy="joined")
    engagement: Mapped[Any] = relationship("EngagementModel", backref="work_tasks", lazy="joined")
