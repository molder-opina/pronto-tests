"""
Analytics API Tests - Operational Reports

Tests for operational analytics endpoints:
- /api/reports/operational-metrics
"""

import pytest
from datetime import date, timedelta


class TestOperationalReports:
    """Test suite for operational analytics reports."""

    @pytest.fixture
    def date_range(self):
        """Provide a standard date range for tests."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    def test_operational_metrics_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/operational-metrics endpoint."""
        response = authenticated_client.get(
            "/api/reports/operational-metrics",
            params=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "metrics" in data["data"]
        
        metrics = data["data"]["metrics"]
        
        # Check all required metric categories
        assert "preparation_time" in metrics
        assert "delivery_time" in metrics
        assert "waiter_acceptance_time" in metrics
        assert "chef_acceptance_time" in metrics
        assert "delivery_rate" in metrics

    def test_operational_metrics_structure(self, authenticated_client, date_range):
        """Test operational metrics data structure."""
        response = authenticated_client.get(
            "/api/reports/operational-metrics",
            params=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        metrics = data["data"]["metrics"]
        
        # Check time metrics structure
        time_metrics = [
            "preparation_time",
            "delivery_time",
            "waiter_acceptance_time",
            "chef_acceptance_time"
        ]
        
        for metric_name in time_metrics:
            metric = metrics[metric_name]
            assert isinstance(metric, dict)
            
            # Each time metric should have avg, min, max
            # Values can be None if no data
            if metric.get("avg_seconds") is not None:
                assert isinstance(metric["avg_seconds"], (int, float))
                assert metric["avg_seconds"] >= 0
            
            if metric.get("min_seconds") is not None:
                assert isinstance(metric["min_seconds"], (int, float))
                assert metric["min_seconds"] >= 0
            
            if metric.get("max_seconds") is not None:
                assert isinstance(metric["max_seconds"], (int, float))
                assert metric["max_seconds"] >= 0
            
            # Min should be <= avg <= max (when all are present)
            if all(metric.get(k) is not None for k in ["min_seconds", "avg_seconds", "max_seconds"]):
                assert metric["min_seconds"] <= metric["avg_seconds"] <= metric["max_seconds"]

    def test_delivery_rate_structure(self, authenticated_client, date_range):
        """Test delivery rate metric structure."""
        response = authenticated_client.get(
            "/api/reports/operational-metrics",
            params=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        delivery_rate = data["data"]["metrics"]["delivery_rate"]
        
        assert "total_orders" in delivery_rate
        assert "delivered_orders" in delivery_rate
        assert "percentage" in delivery_rate
        
        assert isinstance(delivery_rate["total_orders"], int)
        assert isinstance(delivery_rate["delivered_orders"], int)
        assert isinstance(delivery_rate["percentage"], (int, float))
        
        # Validate ranges
        assert delivery_rate["total_orders"] >= 0
        assert delivery_rate["delivered_orders"] >= 0
        assert delivery_rate["delivered_orders"] <= delivery_rate["total_orders"]
        assert 0 <= delivery_rate["percentage"] <= 100

    def test_operational_metrics_without_auth(self, client, date_range):
        """Test that operational metrics require authentication."""
        response = client.get(
            "/api/reports/operational-metrics",
            params=date_range
        )
        
        assert response.status_code == 401

    def test_operational_metrics_with_no_data(self, authenticated_client):
        """Test operational metrics with date range that has no data."""
        future_start = (date.today() + timedelta(days=30)).isoformat()
        future_end = (date.today() + timedelta(days=60)).isoformat()
        
        response = authenticated_client.get(
            "/api/reports/operational-metrics",
            params={"start": future_start, "end": future_end}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        metrics = data["data"]["metrics"]
        
        # All time metrics should be None or have None values
        for metric_name in ["preparation_time", "delivery_time", 
                           "waiter_acceptance_time", "chef_acceptance_time"]:
            metric = metrics[metric_name]
            # At least avg should be None
            assert metric.get("avg_seconds") is None
        
        # Delivery rate should show 0 orders
        assert metrics["delivery_rate"]["total_orders"] == 0
