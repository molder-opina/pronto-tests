"""
Integration tests for authentication API endpoints.
"""
import json

import pytest


@pytest.mark.integration
class TestAuthAPI:
    """Tests for authentication endpoints."""

    def test_login_success(self, employee_client, sample_employee):
        """Test successful login."""
        response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["success"] is True
        assert "employee" in data["data"]
        assert data["data"]["employee"]["email"] == sample_employee.email

    def test_login_invalid_credentials(self, employee_client):
        """Test login with invalid credentials."""
        response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": "nonexistent@example.com", "password": "wrongpass"}),
            content_type="application/json",
        )

        assert response.status_code in [401, 400]
        data = json.loads(response.data)
        assert data["error"] is not None

    def test_login_missing_fields(self, employee_client):
        """Test login with missing required fields."""
        response = employee_client.post(
            "/api/auth/login",
            data=json.dumps(
                {
                    "email": "test@example.com"
                    # Missing password
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"] is not None

    def test_logout(self, employee_client, sample_employee):
        """Test logout endpoint."""
        # First login
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200

        # Then logout
        logout_response = employee_client.post("/api/auth/logout")

        assert logout_response.status_code == 200
        data = json.loads(logout_response.data)
        assert data["success"] is True

    def test_get_current_employee_unauthorized(self, employee_client):
        """Test getting current employee without authentication."""
        response = employee_client.get("/api/auth/me")

        # Should require authentication
        assert response.status_code in [401, 302]
