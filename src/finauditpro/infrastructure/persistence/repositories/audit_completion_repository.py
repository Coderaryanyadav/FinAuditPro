"""Persistence repository for Phase D: Audit Completion (SA 570, SA 580, SA 560, and SA 520)."""

import json

from sqlalchemy.orm import Session

from finauditpro.domain.audit_completion_entities import (
    FinalAnalyticalReview,
    GoingConcernAssessment,
    GoingConcernConclusionEnum,
    GoingConcernMitigation,
    ManagementRepresentationLetter,
    MRLClause,
    MRLClauseCategoryEnum,
    MRLStatusEnum,
    RatioCategoryEnum,
    RatioComparisonLine,
    SolvencyRiskLevelEnum,
    SubsequentEvent,
    SubsequentEventProcedureEnum,
    SubsequentEventTypeEnum,
)
from finauditpro.infrastructure.persistence.audit_completion_models import (
    FinalAnalyticalReviewModel,
    GoingConcernAssessmentModel,
    ManagementRepresentationLetterModel,
    SubsequentEventModel,
)


class AuditCompletionRepository:
    """SQLAlchemy-backed repository for audit completion domain models."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ==========================================
    # SA 570: Going Concern Assessments
    # ==========================================

    def save_going_concern_assessment(
        self, assessment: GoingConcernAssessment
    ) -> GoingConcernAssessment:
        existing = (
            self.session.query(GoingConcernAssessmentModel)
            .filter(GoingConcernAssessmentModel.id == assessment.id)
            .first()
        )
        mitigations_json = json.dumps([m.model_dump() for m in assessment.mitigations])
        solvency_val = getattr(
            assessment.solvency_risk_level, "value", str(assessment.solvency_risk_level)
        )
        conclusion_val = getattr(
            assessment.audit_conclusion, "value", str(assessment.audit_conclusion)
        )

        if existing:
            existing.assessment_period_months = assessment.assessment_period_months
            existing.has_operating_losses = assessment.has_operating_losses
            existing.has_negative_operating_cashflow = (
                assessment.has_negative_operating_cashflow
            )
            existing.has_negative_net_worth = assessment.has_negative_net_worth
            existing.has_covenant_breaches = assessment.has_covenant_breaches
            existing.has_delayed_statutory_dues = assessment.has_delayed_statutory_dues
            existing.has_debt_maturity_unfunded = assessment.has_debt_maturity_unfunded
            existing.current_ratio = assessment.current_ratio
            existing.debt_equity_ratio = assessment.debt_equity_ratio
            existing.solvency_risk_level = solvency_val
            existing.material_uncertainty_identified = (
                assessment.material_uncertainty_identified
            )
            existing.mitigations_json = mitigations_json
            existing.audit_conclusion = conclusion_val
            existing.conclusion_rationale = assessment.conclusion_rationale
            existing.preparer = assessment.preparer
            existing.reviewer = assessment.reviewer
            existing.partner_signoff = assessment.partner_signoff
        else:
            model = GoingConcernAssessmentModel(
                id=assessment.id,
                engagement_id=assessment.engagement_id,
                assessment_period_months=assessment.assessment_period_months,
                has_operating_losses=assessment.has_operating_losses,
                has_negative_operating_cashflow=assessment.has_negative_operating_cashflow,
                has_negative_net_worth=assessment.has_negative_net_worth,
                has_covenant_breaches=assessment.has_covenant_breaches,
                has_delayed_statutory_dues=assessment.has_delayed_statutory_dues,
                has_debt_maturity_unfunded=assessment.has_debt_maturity_unfunded,
                current_ratio=assessment.current_ratio,
                debt_equity_ratio=assessment.debt_equity_ratio,
                solvency_risk_level=solvency_val,
                material_uncertainty_identified=assessment.material_uncertainty_identified,
                mitigations_json=mitigations_json,
                audit_conclusion=conclusion_val,
                conclusion_rationale=assessment.conclusion_rationale,
                preparer=assessment.preparer,
                reviewer=assessment.reviewer,
                partner_signoff=assessment.partner_signoff,
            )
            self.session.add(model)
        self.session.flush()
        return assessment

    def get_going_concern_assessment(
        self, engagement_id: str
    ) -> GoingConcernAssessment | None:
        model = (
            self.session.query(GoingConcernAssessmentModel)
            .filter(GoingConcernAssessmentModel.engagement_id == engagement_id)
            .first()
        )
        if not model:
            return None
        mitigations = [
            GoingConcernMitigation(**m) for m in json.loads(model.mitigations_json)
        ]
        return GoingConcernAssessment(
            id=model.id,
            engagement_id=model.engagement_id,
            assessment_period_months=model.assessment_period_months,
            has_operating_losses=model.has_operating_losses,
            has_negative_operating_cashflow=model.has_negative_operating_cashflow,
            has_negative_net_worth=model.has_negative_net_worth,
            has_covenant_breaches=model.has_covenant_breaches,
            has_delayed_statutory_dues=model.has_delayed_statutory_dues,
            has_debt_maturity_unfunded=model.has_debt_maturity_unfunded,
            current_ratio=model.current_ratio,
            debt_equity_ratio=model.debt_equity_ratio,
            solvency_risk_level=SolvencyRiskLevelEnum(model.solvency_risk_level),
            material_uncertainty_identified=model.material_uncertainty_identified,
            mitigations=mitigations,
            audit_conclusion=GoingConcernConclusionEnum(model.audit_conclusion),
            conclusion_rationale=model.conclusion_rationale,
            preparer=model.preparer,
            reviewer=model.reviewer,
            partner_signoff=model.partner_signoff,
            created_at=model.created_at.isoformat(),
        )

    # ==========================================
    # SA 580: Management Representation Letters
    # ==========================================

    def save_mrl(
        self, mrl: ManagementRepresentationLetter
    ) -> ManagementRepresentationLetter:
        existing = (
            self.session.query(ManagementRepresentationLetterModel)
            .filter(ManagementRepresentationLetterModel.id == mrl.id)
            .first()
        )
        clauses_json = json.dumps([c.model_dump() for c in mrl.clauses])
        status_val = getattr(mrl.status, "value", str(mrl.status))

        if existing:
            existing.status = status_val
            existing.requested_date = mrl.requested_date
            existing.signed_date = mrl.signed_date
            existing.signatory_name = mrl.signatory_name
            existing.signatory_designation = mrl.signatory_designation
            existing.clauses_json = clauses_json
            existing.is_chronologically_valid = mrl.is_chronologically_valid
        else:
            model = ManagementRepresentationLetterModel(
                id=mrl.id,
                engagement_id=mrl.engagement_id,
                mrl_number=mrl.mrl_number,
                financial_year=mrl.financial_year,
                status=status_val,
                requested_date=mrl.requested_date,
                signed_date=mrl.signed_date,
                signatory_name=mrl.signatory_name,
                signatory_designation=mrl.signatory_designation,
                clauses_json=clauses_json,
                is_chronologically_valid=mrl.is_chronologically_valid,
            )
            self.session.add(model)
        self.session.flush()
        return mrl

    def get_mrl(self, mrl_id: str) -> ManagementRepresentationLetter | None:
        model = (
            self.session.query(ManagementRepresentationLetterModel)
            .filter(ManagementRepresentationLetterModel.id == mrl_id)
            .first()
        )
        if not model:
            return None
        return self._to_mrl_domain(model)

    def get_mrl_by_number(
        self, engagement_id: str, mrl_number: str
    ) -> ManagementRepresentationLetter | None:
        model = (
            self.session.query(ManagementRepresentationLetterModel)
            .filter(
                ManagementRepresentationLetterModel.engagement_id == engagement_id,
                ManagementRepresentationLetterModel.mrl_number == mrl_number,
            )
            .first()
        )
        if not model:
            return None
        return self._to_mrl_domain(model)

    def list_mrls(
        self, engagement_id: str
    ) -> list[ManagementRepresentationLetter]:
        models = (
            self.session.query(ManagementRepresentationLetterModel)
            .filter(ManagementRepresentationLetterModel.engagement_id == engagement_id)
            .all()
        )
        return [self._to_mrl_domain(m) for m in models]

    def _to_mrl_domain(
        self, model: ManagementRepresentationLetterModel
    ) -> ManagementRepresentationLetter:
        clauses_raw = json.loads(model.clauses_json)
        clauses = [
            MRLClause(
                id=c["id"],
                clause_number=c["clause_number"],
                category=MRLClauseCategoryEnum(c["category"]),
                title=c["title"],
                text_content=c["text_content"],
                is_mandatory=c.get("is_mandatory", True),
                is_accepted_by_management=c.get("is_accepted_by_management", True),
            )
            for c in clauses_raw
        ]
        return ManagementRepresentationLetter(
            id=model.id,
            engagement_id=model.engagement_id,
            mrl_number=model.mrl_number,
            financial_year=model.financial_year,
            status=MRLStatusEnum(model.status),
            requested_date=model.requested_date,
            signed_date=model.signed_date,
            signatory_name=model.signatory_name,
            signatory_designation=model.signatory_designation,
            clauses=clauses,
            is_chronologically_valid=model.is_chronologically_valid,
            created_at=model.created_at.isoformat(),
        )

    # ==========================================
    # SA 560: Subsequent Events
    # ==========================================

    def add_subsequent_event(self, event: SubsequentEvent) -> SubsequentEvent:
        type_val = getattr(event.event_type, "value", str(event.event_type))
        proc_val = getattr(
            event.procedure_applied, "value", str(event.procedure_applied)
        )
        model = SubsequentEventModel(
            id=event.id,
            engagement_id=event.engagement_id,
            event_date=event.event_date,
            event_type=type_val,
            description=event.description,
            estimated_amount_paise=event.estimated_amount_paise,
            accounting_treatment=event.accounting_treatment,
            is_adjusted_in_fs=event.is_adjusted_in_fs,
            is_disclosed_in_notes=event.is_disclosed_in_notes,
            working_paper_ref=event.working_paper_ref,
            procedure_applied=proc_val,
            auditor_conclusion=event.auditor_conclusion,
        )
        self.session.add(model)
        self.session.flush()
        return event

    def list_subsequent_events(self, engagement_id: str) -> list[SubsequentEvent]:
        models = (
            self.session.query(SubsequentEventModel)
            .filter(SubsequentEventModel.engagement_id == engagement_id)
            .order_by(SubsequentEventModel.event_date.asc())
            .all()
        )
        return [
            SubsequentEvent(
                id=m.id,
                engagement_id=m.engagement_id,
                event_date=m.event_date,
                event_type=SubsequentEventTypeEnum(m.event_type),
                description=m.description,
                estimated_amount_paise=m.estimated_amount_paise,
                accounting_treatment=m.accounting_treatment,
                is_adjusted_in_fs=m.is_adjusted_in_fs,
                is_disclosed_in_notes=m.is_disclosed_in_notes,
                working_paper_ref=m.working_paper_ref,
                procedure_applied=SubsequentEventProcedureEnum(m.procedure_applied),
                auditor_conclusion=m.auditor_conclusion,
                created_at=m.created_at.isoformat(),
            )
            for m in models
        ]

    # ==========================================
    # SA 520: Final Analytical Review
    # ==========================================

    def save_final_analytical_review(
        self, review: FinalAnalyticalReview
    ) -> FinalAnalyticalReview:
        existing = (
            self.session.query(FinalAnalyticalReviewModel)
            .filter(FinalAnalyticalReviewModel.id == review.id)
            .first()
        )
        ratio_json = json.dumps([r.model_dump() for r in review.ratio_lines])

        if existing:
            existing.ratio_lines_json = ratio_json
            existing.has_unexplained_significant_variances = (
                review.has_unexplained_significant_variances
            )
            existing.overall_consistency_conclusion = (
                review.overall_consistency_conclusion
            )
            existing.completed_by = review.completed_by
            existing.reviewed_by = review.reviewed_by
        else:
            model = FinalAnalyticalReviewModel(
                id=review.id,
                engagement_id=review.engagement_id,
                ratio_lines_json=ratio_json,
                has_unexplained_significant_variances=review.has_unexplained_significant_variances,
                overall_consistency_conclusion=review.overall_consistency_conclusion,
                completed_by=review.completed_by,
                reviewed_by=review.reviewed_by,
            )
            self.session.add(model)
        self.session.flush()
        return review

    def get_final_analytical_review(
        self, engagement_id: str
    ) -> FinalAnalyticalReview | None:
        model = (
            self.session.query(FinalAnalyticalReviewModel)
            .filter(FinalAnalyticalReviewModel.engagement_id == engagement_id)
            .first()
        )
        if not model:
            return None
        lines_raw = json.loads(model.ratio_lines_json)
        lines = [
            RatioComparisonLine(
                ratio_name=line["ratio_name"],
                category=RatioCategoryEnum(line["category"]),
                current_year_value=line["current_year_value"],
                previous_year_value=line["previous_year_value"],
                variance_percentage=line["variance_percentage"],
                is_significant_variance=line["is_significant_variance"],
                auditor_explanation=line.get("auditor_explanation", ""),
            )
            for line in lines_raw
        ]
        return FinalAnalyticalReview(
            id=model.id,
            engagement_id=model.engagement_id,
            ratio_lines=lines,
            has_unexplained_significant_variances=model.has_unexplained_significant_variances,
            overall_consistency_conclusion=model.overall_consistency_conclusion,
            completed_by=model.completed_by,
            reviewed_by=model.reviewed_by,
            created_at=model.created_at.isoformat(),
        )
