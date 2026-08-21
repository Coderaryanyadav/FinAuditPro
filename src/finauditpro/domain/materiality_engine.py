"""Pure domain calculation engine for SA 320 Audit Materiality."""

from decimal import ROUND_HALF_UP, Decimal

from finauditpro.domain.audit_matrix_entities import BenchmarkTypeEnum, MaterialityAssessment


class BenchmarkOption:
    """Benchmark guidance option carrying source and non-statutory disclaimer."""

    def __init__(self, benchmark_type: BenchmarkTypeEnum, default_overall_pct: float, source: str, description: str):
        self.benchmark_type = benchmark_type
        self.default_overall_pct = default_overall_pct
        self.source = source
        self.is_verified_statutory = False  # Always False: percentages are professional judgement, not hardcoded law
        self.description = description


BENCHMARK_GUIDANCE_OPTIONS = [
    BenchmarkOption(
        benchmark_type=BenchmarkTypeEnum.REVENUE,
        default_overall_pct=1.0,
        source="SA 320 Illustrative Guidance (Non-Statutory Suggestion)",
        description="Typically 0.5% to 2.0% of Gross Revenue for commercial enterprises.",
    ),
    BenchmarkOption(
        benchmark_type=BenchmarkTypeEnum.PROFIT_BEFORE_TAX,
        default_overall_pct=5.0,
        source="SA 320 Illustrative Guidance (Non-Statutory Suggestion)",
        description="Typically 5.0% to 10.0% of Profit Before Tax for profit-oriented entities.",
    ),
    BenchmarkOption(
        benchmark_type=BenchmarkTypeEnum.TOTAL_ASSETS,
        default_overall_pct=1.0,
        source="SA 320 Illustrative Guidance (Non-Statutory Suggestion)",
        description="Typically 0.5% to 1.0% of Total Assets for asset-intensive entities.",
    ),
    BenchmarkOption(
        benchmark_type=BenchmarkTypeEnum.EQUITY,
        default_overall_pct=2.0,
        source="SA 320 Illustrative Guidance (Non-Statutory Suggestion)",
        description="Typically 1.0% to 5.0% of Net Worth / Equity for financial holdings.",
    ),
]


def calculate_paise_percentage(amount_paise: int, percentage: float) -> int:
    """Compute exact paise amount from percentage using Decimal HALF_UP rounding."""
    dec_amount = Decimal(amount_paise)
    dec_pct = Decimal(str(percentage)) / Decimal("100.0")
    result = dec_amount * dec_pct
    return int(result.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class MaterialityEngine:
    """Deterministic, reproducible SA 320 Materiality Calculation Engine."""

    @staticmethod
    def calculate(
        engagement_id: str,
        benchmark_type: BenchmarkTypeEnum,
        benchmark_amount_paise: int,
        overall_percentage: float = 1.0,
        performance_percentage: float = 75.0,
        trivial_percentage: float = 5.0,
        benchmark_source: str = "SA 320 Guidance (Editable Suggestion)",
        methodology_notes: str = "",
        version: int = 1,
        created_by: str = "Lead Auditor",
    ) -> MaterialityAssessment:
        if benchmark_amount_paise < 0:
            raise ValueError("Benchmark amount in paise cannot be negative.")

        overall_paise = calculate_paise_percentage(benchmark_amount_paise, overall_percentage)
        performance_paise = calculate_paise_percentage(overall_paise, performance_percentage)
        trivial_paise = calculate_paise_percentage(overall_paise, trivial_percentage)

        return MaterialityAssessment(
            engagement_id=engagement_id,
            benchmark_type=benchmark_type,
            benchmark_amount_paise=benchmark_amount_paise,
            benchmark_source=benchmark_source,
            is_verified_statutory=False,
            overall_percentage=overall_percentage,
            overall_materiality_paise=overall_paise,
            performance_percentage=performance_percentage,
            performance_materiality_paise=performance_paise,
            trivial_percentage=trivial_percentage,
            clearly_trivial_threshold_paise=trivial_paise,
            version=version,
            methodology_notes=methodology_notes,
            created_by=created_by,
        )

    @staticmethod
    def classify_monetary_amount(amount_paise: int, assessment: MaterialityAssessment) -> str:
        """Classify a monetary exception amount against OM, PM, and CTT thresholds."""
        if amount_paise < assessment.clearly_trivial_threshold_paise:
            return "Clearly Trivial"
        if amount_paise >= assessment.overall_materiality_paise:
            return "Above Overall Materiality"
        if amount_paise >= assessment.performance_materiality_paise:
            return "Above Performance Materiality"
        return "Requires Auditor Review"
