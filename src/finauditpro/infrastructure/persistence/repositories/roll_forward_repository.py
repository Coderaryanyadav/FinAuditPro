"""Repository managing Roll-Forward Records and Opening Balance Link persistence."""

import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.roll_forward_entities import OpeningBalanceLink, RollForwardRecord
from finauditpro.infrastructure.persistence.roll_forward_models import OpeningBalanceLinkModel, RollForwardRecordModel


class RollForwardRepository:
    """Repository handling persistence of roll-forward executions and SA 510 opening balance links."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_record_entity(self, model: RollForwardRecordModel) -> RollForwardRecord:
        items = json.loads(model.items_carried_json) if model.items_carried_json else []
        return RollForwardRecord(
            id=model.id,
            new_engagement_id=model.new_engagement_id,
            source_engagement_id=model.source_engagement_id,
            source_fy=model.source_fy,
            items_carried=items,
            performed_by=model.performed_by,
            created_at=model.created_at,
        )

    def _to_link_entity(self, model: OpeningBalanceLinkModel) -> OpeningBalanceLink:
        return OpeningBalanceLink(
            id=model.id,
            engagement_id=model.engagement_id,
            source_engagement_id=model.source_engagement_id,
            account_code=model.account_code,
            account_name=model.account_name,
            opening_dr_paise=model.opening_dr_paise,
            opening_cr_paise=model.opening_cr_paise,
            prior_closing_dr_paise=model.prior_closing_dr_paise,
            prior_closing_cr_paise=model.prior_closing_cr_paise,
            is_tied_out=bool(model.is_tied_out),
            is_verified_by_auditor=bool(model.is_verified_by_auditor),
            verified_at=model.verified_at,
            verified_by=model.verified_by,
            created_at=model.created_at,
        )

    def add_roll_forward_record(self, record: RollForwardRecord) -> RollForwardRecord:
        model = RollForwardRecordModel(
            id=record.id,
            new_engagement_id=record.new_engagement_id,
            source_engagement_id=record.source_engagement_id,
            source_fy=record.source_fy,
            items_carried_json=json.dumps(record.items_carried),
            performed_by=record.performed_by,
            created_at=record.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_record_entity(model)

    def get_roll_forward_record(self, engagement_id: str) -> RollForwardRecord | None:
        stmt = (
            select(RollForwardRecordModel)
            .where(RollForwardRecordModel.new_engagement_id == engagement_id)
            .order_by(RollForwardRecordModel.created_at.desc())
            .limit(1)
        )
        model = self.session.scalars(stmt).first()
        return self._to_record_entity(model) if model else None

    def add_opening_balance_links(self, links: list[OpeningBalanceLink]) -> list[OpeningBalanceLink]:
        models = [
            OpeningBalanceLinkModel(
                id=link.id,
                engagement_id=link.engagement_id,
                source_engagement_id=link.source_engagement_id,
                account_code=link.account_code,
                account_name=link.account_name,
                opening_dr_paise=link.opening_dr_paise,
                opening_cr_paise=link.opening_cr_paise,
                prior_closing_dr_paise=link.prior_closing_dr_paise,
                prior_closing_cr_paise=link.prior_closing_cr_paise,
                is_tied_out=int(link.is_tied_out),
                is_verified_by_auditor=int(link.is_verified_by_auditor),
                verified_at=link.verified_at,
                verified_by=link.verified_by,
                created_at=link.created_at,
            )
            for link in links
        ]
        self.session.add_all(models)
        self.session.flush()
        return [self._to_link_entity(m) for m in models]

    def list_opening_balance_links(self, engagement_id: str) -> list[OpeningBalanceLink]:
        stmt = (
            select(OpeningBalanceLinkModel)
            .where(OpeningBalanceLinkModel.engagement_id == engagement_id)
            .order_by(OpeningBalanceLinkModel.account_code.asc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_link_entity(m) for m in models]

    def confirm_opening_balance_tie_out(self, engagement_id: str, verified_by: str, verified_at: str) -> None:
        stmt = select(OpeningBalanceLinkModel).where(OpeningBalanceLinkModel.engagement_id == engagement_id)
        models = self.session.scalars(stmt).all()
        for m in models:
            m.is_verified_by_auditor = 1
            m.verified_at = verified_at
            m.verified_by = verified_by
        self.session.flush()
