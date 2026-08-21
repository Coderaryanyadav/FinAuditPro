"""SQLAlchemy 2.0 ORM models for AI Subsystem (Provider Config, Document Chunks, AI Runs)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.database import Base


class AIProviderConfigModel(Base):
    __tablename__ = "ai_provider_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    base_url: Mapped[str] = mapped_column(
        String(255), nullable=False, default="http://localhost:1234/v1"
    )
    chat_model_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default="deepseek/deepseek-r1-distill-qwen-14b"
    )
    embedding_model_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default="text-embedding-nomic-embed-text-v1.5"
    )
    temperature: Mapped[float] = mapped_column(nullable=False, default=0.6)
    top_p: Mapped[float] = mapped_column(nullable=False, default=0.95)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(nullable=False)
    char_start: Mapped[int] = mapped_column(nullable=False, default=0)
    char_end: Mapped[int] = mapped_column(nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dimension: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )


class AIRunModel(Base):
    __tablename__ = "ai_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    retrieved_chunk_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    reasoning_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Completed")
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Auditor")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
