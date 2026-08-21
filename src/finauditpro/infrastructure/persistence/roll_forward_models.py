"""SQLAlchemy ORM models for Roll Forward Audit Records and Opening Balance Links."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.infrastructure.persistence.database import Base


class RollForwardRecordModel(Base):
    """ORM Model representing a multi-year roll-forward execution."""

    __tablename__ = "roll_forward_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    new_engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    source_engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    source_fy: Mapped[str] = mapped_column(String, nullable=False)
    items_carried_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    performed_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class OpeningBalanceLinkModel(Base):
    """ORM Model representing SA 510 opening balance links and tie-out comparisons."""

    __tablename__ = "opening_balance_links"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    source_engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False)
    account_code: Mapped[str] = mapped_column(String, nullable=False)
    account_name: Mapped[str] = mapped_column(String, nullable=False)
    opening_dr_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opening_cr_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prior_closing_dr_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prior_closing_cr_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_tied_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_verified_by_auditor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_at: Mapped[str | None] = mapped_column(String, nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
