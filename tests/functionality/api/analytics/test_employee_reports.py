"""
Analytics API Tests - Employee Reports

Tests for employee analytics endpoints:
- /api/reports/waiter-performance
- /api/reports/waiter-tips
"""

import pytest
from datetime import date, timedelta


class TestEmployeeReports:
    """Test suite for employee analytics reports."""

    @pytest.fixture
    def date_range(self):
        """Provide a standard date range for tests."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    def test_waiter_performance_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/waiter-performance endpoint."""
        response = authenticated_client.get(
            "/api/reports/waiter-performance",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "waiters" in data["data"]
        
        waiters = data["data"]["waiters"]
        assert isinstance(waiters, list)
        
        if waiters:
            waiter = waiters[0]
            assert "waiter_id" in waiter
            assert "waiter_name" in waiter
            assert "order_count" in waiter
            assert "total_sales" in waiter
            assert "avg_order_value" in waiter
            assert "total_tips" in waiter
            assert "avg_tip" in waiter
            assert "tip_percentage" in waiter
            
            # Validate data types
            assert isinstance(waiter["order_count"], int)
            assert isinstance(waiter["total_sales"], (int, float))
            assert isinstance(waiter["tip_percentage"], (int, float))
            
            # Validate ranges
            assert waiter["order_count"] >= 0
            assert waiter["total_sales"] >= 0
            assert waiter["tip_percentage"] >= 0

    def test_waiter_tips_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/waiter-tips endpoint."""
        response = authenticated_client.get(
            "/api/reports/waiter-tips",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "tips" in data["data"]
        assert "summary" in data["data"]
        
        tips = data["data"]["tips"]
        summary = data["data"]["summary"]
        
        assert isinstance(tips, list)
        assert isinstance(summary, dict)
        
        if tips:
            tip_data = tips[0]
            assert "waiter_id" in tip_data
            assert "waiter_name" in tip_data
            assert "order_count" in tip_data
            assert "total_tips" in tip_data
            assert "avg_tip" in tip_data
            assert "total_sales" in tip_data
            assert "tip_percentage" in tip_data
        
        # Validate summary
        assert "total_tips" in summary
        assert "waiter_count" in summary
        assert isinstance(summary["total_tips"], (int, float))
        assert isinstance(summary["waiter_count"], int)

    def test_waiter_performance_sorting(self, authenticated_client, date_range):
        """Test that waiter performance is sorted by total sales."""
        response = authenticated_client.get(
            "/api/reports/waiter-performance",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        waiters = data["data"]["waiters"]
        
        if len(waiters) > 1:
            # Verify descending order by total_sales
            for i in range(len(waiters) - 1):
                assert waiters[i]["total_sales"] >= waiters[i + 1]["total_sales"]

    def test_waiter_tips_sorting(self, authenticated_client, date_range):
        """Test that waiter tips are sorted by total tips."""
        response = authenticated_client.get(
            "/api/reports/waiter-tips",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        tips = data["data"]["tips"]
        
        if len(tips) > 1:
            # Verify descending order by total_tips
            for i in range(len(tips) - 1):
                assert tips[i]["total_tips"] >= tips[i + 1]["total_tips"]

    def test_employee_reports_without_auth(self, client, date_range):
        """Test that employee reports require authentication."""
        endpoints = [
            "/api/reports/waiter-performance",
            "/api/reports/waiter-tips"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, query_string=date_range)
            assert response.status_code == 401

    def test_waiter_performance_with_no_data(self, authenticated_client):
        """Test waiter performance with date range that has no data."""
        future_start = (date.today() + timedelta(days=30)).isoformat()
        future_end = (date.today() + timedelta(days=60)).isoformat()
        
        response = authenticated_client.get(
            "/api/reports/waiter-performance",
            query_string={"start": future_start, "end": future_end}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty list
        assert data["data"]["waiters"] == []
