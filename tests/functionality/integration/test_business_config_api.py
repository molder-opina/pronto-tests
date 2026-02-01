"""
Integration tests for business configuration API endpoints.
"""
import json

import pytest


@pytest.mark.integration
class TestBusinessConfigAPI:
    """Tests for business configuration endpoints."""

    def test_get_business_info(self, employee_client, sample_employee):
        """Test getting business information."""
        # Login first
        employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        response = employee_client.get("/api/business-info")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "business_name" in data["data"]

    def test_get_business_schedule(self, employee_client, sample_employee):
        """Test getting business schedule."""
        # Login first
        employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        response = employee_client.get("/api/business-schedule")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data
        assert "schedule" in data["data"]
        assert len(data["data"]["schedule"]) == 7  # 7 days of the week
