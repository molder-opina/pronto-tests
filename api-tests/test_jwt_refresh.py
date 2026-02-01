"""
Integration tests for JWT refresh token flow.

Tests the complete lifecycle of refresh tokens including:
- Successful token refresh
- Expired refresh tokens
- Invalid refresh tokens
- Missing refresh tokens
"""
import json
import time
from unittest.mock import patch

import pytest

from shared.jwt_service import create_access_token, create_refresh_token


@pytest.mark.integration
class TestJWTRefreshToken:
    """Tests for JWT refresh token endpoints."""

    def test_refresh_token_success(self, employee_client, sample_employee):
        """Test successful refresh token flow."""
        # First, login to get tokens
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        assert "refresh_token" in login_data["data"]

        refresh_token = login_data["data"]["refresh_token"]

        # Now use refresh token to get new access token
        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        assert refresh_data["data"]["success"] is True
        assert "access_token" in refresh_data["data"]

        # Verify new access token is different from original
        new_access_token = refresh_data["data"]["access_token"]
        original_access_token = login_data["data"]["access_token"]
        assert new_access_token != original_access_token

        # Verify new access token works
        me_response = employee_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response.status_code == 200

    def test_refresh_token_from_cookie(self, employee_client, sample_employee):
        """Test refresh token flow using cookie instead of body."""
        # Login to set refresh token cookie
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200

        # Refresh without sending token in body (should use cookie)
        refresh_response = employee_client.post("/api/auth/refresh")

        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        assert refresh_data["data"]["success"] is True
        assert "access_token" in refresh_data["data"]

    def test_refresh_token_expired(self, employee_client, sample_employee):
        """Test refresh with expired token."""
        # Create an expired refresh token (expires in -1 days)
        expired_token = create_refresh_token(
            employee_id=sample_employee.id,
            expires_days=-1,  # Already expired
        )

        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": expired_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 401
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data
        assert "expired" in error_data["error"].lower()

    def test_refresh_token_invalid(self, employee_client):
        """Test refresh with invalid token."""
        invalid_token = "invalid.jwt.token"

        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": invalid_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 401
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data
        assert "invalid" in error_data["error"].lower()

    def test_refresh_token_missing(self, employee_client):
        """Test refresh without providing token."""
        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 400
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data
        assert "required" in error_data["error"].lower()

    def test_refresh_token_wrong_type(self, employee_client, sample_employee):
        """Test refresh with access token instead of refresh token."""
        # Create an access token
        access_token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role=sample_employee.role,
            employee_additional_roles=sample_employee.additional_roles,
        )

        # Try to use access token for refresh
        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": access_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 401
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data

    def test_refresh_token_inactive_employee(self, employee_client, sample_employee, db_session):
        """Test refresh token with inactive employee."""
        # Login first
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        refresh_token = login_data["data"]["refresh_token"]

        # Deactivate employee
        sample_employee.is_active = False
        db_session.commit()

        # Try to refresh with inactive employee
        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 401
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data
        assert "inactive" in error_data["error"].lower()

    def test_refresh_token_deleted_employee(self, employee_client, sample_employee, db_session):
        """Test refresh token with deleted employee."""
        # Login first
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        refresh_token = login_data["data"]["refresh_token"]

        # Delete employee
        employee_id = sample_employee.id
        db_session.delete(sample_employee)
        db_session.commit()

        # Try to refresh with deleted employee
        refresh_response = employee_client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        assert refresh_response.status_code == 401
        error_data = json.loads(refresh_response.data)
        assert "error" in error_data

    def test_refresh_token_updates_cookie(self, employee_client, sample_employee):
        """Test that refresh token updates the access_token cookie."""
        # Login
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200

        # Refresh (using cookie)
        refresh_response = employee_client.post("/api/auth/refresh")

        assert refresh_response.status_code == 200

        # Check that Set-Cookie header is present for access_token
        set_cookie_headers = [
            header[1] for header in refresh_response.headers if header[0] == "Set-Cookie"
        ]
        assert any("access_token=" in cookie for cookie in set_cookie_headers)

    def test_refresh_token_preserves_employee_data(self, employee_client, sample_employee):
        """Test that refresh token preserves employee data in new access token."""
        # Login
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200

        # Refresh
        refresh_response = employee_client.post("/api/auth/refresh")

        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        new_access_token = refresh_data["data"]["access_token"]

        # Verify employee data in new token
        me_response = employee_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

        assert me_response.status_code == 200
        me_data = json.loads(me_response.data)
        assert me_data["employee"]["id"] == sample_employee.id
        assert me_data["employee"]["email"] == sample_employee.email
        assert me_data["employee"]["role"] == sample_employee.role

    def test_refresh_token_rate_limiting(self, employee_client, sample_employee):
        """Test that refresh endpoint has rate limiting."""
        # Login
        login_response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        refresh_token = login_data["data"]["refresh_token"]

        # Make multiple refresh requests (should be rate limited after 10)
        # Note: Rate limit is 10 requests per minute according to the endpoint
        for i in range(12):
            refresh_response = employee_client.post(
                "/api/auth/refresh",
                data=json.dumps({"refresh_token": refresh_token}),
                content_type="application/json",
            )

            if i < 10:
                # First 10 should succeed
                assert refresh_response.status_code == 200
            else:
                # 11th and 12th should be rate limited
                assert refresh_response.status_code == 429
