"""
Analytics API Tests - Revenue Reports

Tests for revenue analytics endpoints:
- /api/reports/kpis
- /api/reports/sales
- /api/reports/peak-hours
"""

import pytest
from datetime import date, timedelta


class TestRevenueReports:
    """Test suite for revenue analytics reports."""

    @pytest.fixture
    def date_range(self):
        """Provide a standard date range for tests."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    def test_kpis_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/kpis endpoint."""
        response = authenticated_client.get(
            "/api/reports/kpis",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "kpis" in data["data"]
        
        kpis = data["data"]["kpis"]
        assert "total_orders" in kpis
        assert "total_revenue" in kpis
        assert "avg_order_value" in kpis
        assert "total_customers" in kpis
        assert "repeat_customers" in kpis
        assert "repeat_customer_rate" in kpis
        assert "total_tips" in kpis
        
        # Validate data types
        assert isinstance(kpis["total_orders"], int)
        assert isinstance(kpis["total_revenue"], (int, float))
        assert isinstance(kpis["avg_order_value"], (int, float))
        assert isinstance(kpis["repeat_customer_rate"], (int, float))
        
        # Validate ranges
        assert kpis["total_orders"] >= 0
        assert kpis["total_revenue"] >= 0
        assert 0 <= kpis["repeat_customer_rate"] <= 100

    def test_sales_report_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/sales endpoint."""
        response = authenticated_client.get(
            "/api/reports/sales",
            query_string={**date_range, "granularity": "day"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "kpis" in data["data"]
        assert "trends" in data["data"]
        assert "granularity" in data["data"]
        
        trends = data["data"]["trends"]
        assert isinstance(trends, list)
        
        if trends:
            trend = trends[0]
            assert "time_period" in trend
            assert "order_count" in trend
            assert "total_revenue" in trend
            assert "avg_order_value" in trend
            assert "total_tips" in trend

    def test_sales_report_granularities(self, authenticated_client, date_range):
        """Test sales report with different granularities."""
        granularities = ["day", "week", "month"]
        
        for granularity in granularities:
            response = authenticated_client.get(
                "/api/reports/sales",
                query_string={**date_range, "granularity": granularity}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["granularity"] == granularity

    def test_peak_hours_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/peak-hours endpoint."""
        response = authenticated_client.get(
            "/api/reports/peak-hours",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "hours" in data["data"]
        
        hours = data["data"]["hours"]
        assert isinstance(hours, list)
        
        if hours:
            hour_data = hours[0]
            assert "hour" in hour_data
            assert "hour_label" in hour_data
            assert "order_count" in hour_data
            assert "total_sales" in hour_data
            assert "avg_order_value" in hour_data
            
            # Validate hour range
            assert 0 <= hour_data["hour"] <= 23
        
        # Check peak_hour if data exists
        if "peak_hour" in data["data"] and data["data"]["peak_hour"]:
            peak = data["data"]["peak_hour"]
            assert "hour" in peak
            assert "order_count" in peak

    def test_reports_without_auth(self, client, date_range):
        """Test that reports require authentication."""
        endpoints = [
            "/api/reports/kpis",
            "/api/reports/sales",
            "/api/reports/peak-hours"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, query_string=date_range)
            assert response.status_code == 401

    def test_reports_with_invalid_dates(self, authenticated_client):
        """Test reports with invalid date ranges."""
        response = authenticated_client.get(
            "/api/reports/kpis",
            query_string={"start": "invalid", "end": "invalid"}
        )
        
        # Should handle gracefully (either 400 or use defaults)
        assert response.status_code in [200, 400]

    def test_reports_with_future_dates(self, authenticated_client):
        """Test reports with future date range."""
        future_start = (date.today() + timedelta(days=30)).isoformat()
        future_end = (date.today() + timedelta(days=60)).isoformat()
        
        response = authenticated_client.get(
            "/api/reports/kpis",
            query_string={"start": future_start, "end": future_end}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Future dates should return zero/empty data
        kpis = data["data"]["kpis"]
        assert kpis["total_orders"] == 0
        assert kpis["total_revenue"] == 0
