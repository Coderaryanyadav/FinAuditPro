"""
Master Executive Intelligence & Analytics Engine Facade for FinAuditPro.
Unifies KPIs, trends, forecasting models, heatmaps, benchmarks, and 4 role dashboards into one BI suite.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

from .kpi_engine import KPIEngine, KPIMetrics
from .trend_engine import TrendEngine, TrendMetrics
from .forecast_engine import ForecastEngine, ForecastMetrics
from .heatmap_engine import HeatmapEngine, HeatmapData
from .chart_engine import AnalyticsChartEngine
from .benchmark_engine import BenchmarkEngine, BenchmarkComparison
from .dashboard_engine import ExecutiveDashboardEngine, DashboardView

@dataclass
class ExecutiveIntelligencePack:
    kpis: KPIMetrics
    trends: TrendMetrics
    forecast: ForecastMetrics
    heatmap: HeatmapData
    benchmark: BenchmarkComparison
    ceo_dashboard: DashboardView
    partner_dashboard: DashboardView
    computation_time_seconds: float


class AnalyticsEngine:
    """Master Facade for Enterprise Business Intelligence & Executive Analytics."""

    def __init__(self):
        self.kpi_engine = KPIEngine()
        self.trend_engine = TrendEngine()
        self.forecast_engine = ForecastEngine()
        self.heatmap_engine = HeatmapEngine()
        self.benchmark_engine = BenchmarkEngine()

    def generate_executive_pack(self, projects_data: Optional[List[Dict[str, Any]]] = None) -> ExecutiveIntelligencePack:
        """Computes complete BI executive intelligence pack."""
        start_time = time.time()

        kpis = self.kpi_engine.calculate_kpis(projects_data)
        trends = self.trend_engine.compute_trends(projects_data)
        forecast = self.forecast_engine.forecast_workload(len(projects_data) if projects_data else 10)
        heatmap = self.heatmap_engine.generate_industry_risk_heatmap()
        benchmark = self.benchmark_engine.compare_year_over_year()

        ceo_db = ExecutiveDashboardEngine.get_ceo_dashboard()
        partner_db = ExecutiveDashboardEngine.get_partner_dashboard()

        elapsed = round(time.time() - start_time, 4)

        return ExecutiveIntelligencePack(
            kpis=kpis,
            trends=trends,
            forecast=forecast,
            heatmap=heatmap,
            benchmark=benchmark,
            ceo_dashboard=ceo_db,
            partner_dashboard=partner_db,
            computation_time_seconds=elapsed
        )
