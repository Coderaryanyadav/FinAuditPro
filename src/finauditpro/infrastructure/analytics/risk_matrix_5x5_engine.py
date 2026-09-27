"""Interactive 5x5 Inherent Risk & Control Heatmap Matrix Engine."""

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any


class LikelihoodLevelEnum(IntEnum):
    RARE = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    ALMOST_CERTAIN = 5


class ImpactLevelEnum(IntEnum):
    INSIGNIFICANT = 1
    MINOR = 2
    MODERATE = 3
    MAJOR = 4
    CATASTROPHIC = 5


class RiskRatingBandEnum(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL_ROMM = "Critical / RoMM"


@dataclass
class RiskScoringResult:
    risk_code: str
    risk_title: str
    category: str
    likelihood: int
    impact: int
    inherent_score: int
    inherent_rating: RiskRatingBandEnum
    control_effectiveness_pct: float
    residual_score: float
    residual_rating: RiskRatingBandEnum
    is_significant_risk: bool


@dataclass
class HeatmapCell:
    likelihood: int
    impact: int
    rating_band: RiskRatingBandEnum
    color_hex: str
    risks_count: int = 0
    risk_codes: list[str] = field(default_factory=list)


class RiskMatrix5x5Engine:
    """Computes 5x5 Inherent Risk and Residual Risk ratings with ICAI SA 315 alignment."""

    @staticmethod
    def get_rating_band(score: float) -> RiskRatingBandEnum:
        """Map numeric score (1-25) to standard 4-tier risk band."""
        if score >= 20.0:
            return RiskRatingBandEnum.CRITICAL_ROMM
        if score >= 12.0:
            return RiskRatingBandEnum.HIGH
        if score >= 6.0:
            return RiskRatingBandEnum.MEDIUM
        return RiskRatingBandEnum.LOW

    @classmethod
    def evaluate_risk(
        cls,
        risk_code: str,
        risk_title: str,
        category: str,
        likelihood: int,
        impact: int,
        control_status: str = "Effective",
    ) -> RiskScoringResult:
        """Calculate inherent score, apply control offset, and derive residual rating."""
        l_clamped = max(1, min(5, likelihood))
        i_clamped = max(1, min(5, impact))
        inh_score = l_clamped * i_clamped
        inh_band = cls.get_rating_band(float(inh_score))

        # Control offset
        cs = control_status.strip().capitalize()
        if "Effective" in cs:
            ctrl_reduction = 0.50  # 50% risk mitigation
        elif "Deficiency" in cs:
            ctrl_reduction = 0.20  # 20% risk mitigation
        else:
            ctrl_reduction = 0.00  # 0% mitigation for material weakness/untested

        res_score = round(inh_score * (1.0 - ctrl_reduction), 2)
        res_band = cls.get_rating_band(res_score)

        # Significant risk definition per SA 315
        is_sig = inh_band in (RiskRatingBandEnum.HIGH, RiskRatingBandEnum.CRITICAL_ROMM)

        return RiskScoringResult(
            risk_code=risk_code,
            risk_title=risk_title,
            category=category,
            likelihood=l_clamped,
            impact=i_clamped,
            inherent_score=inh_score,
            inherent_rating=inh_band,
            control_effectiveness_pct=ctrl_reduction * 100.0,
            residual_score=res_score,
            residual_rating=res_band,
            is_significant_risk=is_sig,
        )

    @classmethod
    def generate_5x5_heatmap(
        cls, scored_risks: list[RiskScoringResult]
    ) -> list[list[HeatmapCell]]:
        """Generate a 5x5 matrix grid populated with aggregated risks."""
        grid: list[list[HeatmapCell]] = []

        # Color definitions for bands
        color_map = {
            RiskRatingBandEnum.LOW: "#22C55E",           # Green
            RiskRatingBandEnum.MEDIUM: "#EAB308",        # Yellow
            RiskRatingBandEnum.HIGH: "#F97316",          # Orange
            RiskRatingBandEnum.CRITICAL_ROMM: "#EF4444", # Red
        }

        for l in range(5, 0, -1):  # Likelihood rows (5 down to 1)
            row: list[HeatmapCell] = []
            for i in range(1, 6):  # Impact cols (1 to 5)
                score = l * i
                band = cls.get_rating_band(float(score))
                matching_codes = [
                    r.risk_code for r in scored_risks if r.likelihood == l and r.impact == i
                ]
                cell = HeatmapCell(
                    likelihood=l,
                    impact=i,
                    rating_band=band,
                    color_hex=color_map[band],
                    risks_count=len(matching_codes),
                    risk_codes=matching_codes,
                )
                row.append(cell)
            grid.append(row)

        return grid
