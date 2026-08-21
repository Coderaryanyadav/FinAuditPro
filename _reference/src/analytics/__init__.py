"""
FinAuditPro Executive Intelligence & Business Intelligence (BI) Analytics Package.
Provides automated KPI computation, trend analytics, forecasting, heatmaps, benchmarks, and 4 role-based dashboards.
"""

from .kpi_engine import KPIEngine, KPIMetrics
from .trend_engine import TrendEngine, TrendMetrics
from .forecast_engine import ForecastEngine, ForecastMetrics
from .heatmap_engine import HeatmapEngine, HeatmapData
from .chart_engine import AnalyticsChartEngine
from .benchmark_engine import BenchmarkEngine, BenchmarkComparison
from .export_engine import AnalyticsExportEngine
from .dashboard_engine import ExecutiveDashboardEngine, DashboardView
from .analytics_engine import AnalyticsEngine, ExecutiveIntelligencePack

__all__ = [
    "KPIEngine",
    "KPIMetrics",
    "TrendEngine",
    "TrendMetrics",
    "ForecastEngine",
    "ForecastMetrics",
    "HeatmapEngine",
    "HeatmapData",
    "AnalyticsChartEngine",
    "BenchmarkEngine",
    "BenchmarkComparison",
    "AnalyticsExportEngine",
    "ExecutiveDashboardEngine",
    "DashboardView",
    "AnalyticsEngine",
    "ExecutiveIntelligencePack",
]
