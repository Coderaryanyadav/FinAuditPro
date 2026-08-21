"""
Unit Tests for FinAuditPro Executive Intelligence & Business Intelligence (BI) Engine.
Tests KPI Engine, Trend Analytics, Predictive Forecasting, Heatmaps, Benchmarks, and Executive Dashboards.
"""

import unittest
from analytics.analytics_engine import AnalyticsEngine
from analytics.dashboard_engine import ExecutiveDashboardEngine
from analytics.chart_engine import AnalyticsChartEngine


class TestAnalyticsEngine(unittest.TestCase):

    def setUp(self):
        from database.database import init_db
        init_db()
        self.engine = AnalyticsEngine()

    def test_executive_pack_generation(self):
        sample_projects = [
            {"risk_score": 18.0, "compliance_score": 96.0, "status": "Completed"},
            {"risk_score": 45.0, "compliance_score": 90.0, "status": "In Progress"},
            {"risk_score": 75.0, "compliance_score": 82.0, "status": "Pending Review"}
        ]
        pack = self.engine.generate_executive_pack(sample_projects)
        self.assertIsNotNone(pack.kpis)
        self.assertIsNotNone(pack.trends)
        self.assertEqual(pack.ceo_dashboard.role_name, "CEO Dashboard")
        self.assertEqual(pack.partner_dashboard.role_name, "Audit Partner Dashboard")

    def test_role_dashboards(self):
        ceo = ExecutiveDashboardEngine.get_ceo_dashboard()
        partner = ExecutiveDashboardEngine.get_partner_dashboard()
        senior = ExecutiveDashboardEngine.get_senior_auditor_dashboard()
        junior = ExecutiveDashboardEngine.get_junior_auditor_dashboard()

        self.assertEqual(ceo.role_name, "CEO Dashboard")
        self.assertEqual(partner.role_name, "Audit Partner Dashboard")
        self.assertEqual(senior.role_name, "Senior Auditor Dashboard")
        self.assertEqual(junior.role_name, "Junior Auditor Dashboard")

    def test_chart_series_data(self):
        funnel = AnalyticsChartEngine.get_audit_funnel_chart_data()
        self.assertIn("stages", funnel)
        self.assertEqual(len(funnel["stages"]), 5)

        ocr_ai = AnalyticsChartEngine.get_ai_ocr_accuracy_chart_data()
        self.assertIn("categories", ocr_ai)


if __name__ == "__main__":
    unittest.main()
