"""
Integration tests for JWT scope validation (Scope Guard).

Tests the scope guard middleware that ensures JWT scope matches URL scope.
This prevents scope confusion attacks where a waiter token is used on admin routes.
"""
import json

import pytest

from shared.jwt_service import create_access_token


@pytest.mark.integration
class TestJWTScopeGuard:
    """Tests for JWT scope guard middleware."""

    def test_scope_match_allowed_waiter(self, employee_client, sample_employee):
        """Test that matching scope (waiter) is allowed."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Access waiter endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed (may return 200 or 404 depending on data, but not 403)
        assert response.status_code != 403

    def test_scope_match_allowed_chef(self, employee_client, sample_employee):
        """Test that matching scope (chef) is allowed."""
        # Create chef token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="chef",
            employee_additional_roles=[],
            active_scope="chef",
        )

        # Access chef endpoint
        response = employee_client.get(
            "/chef/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_scope_match_allowed_cashier(self, employee_client, sample_employee):
        """Test that matching scope (cashier) is allowed."""
        # Create cashier token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="cashier",
            employee_additional_roles=[],
            active_scope="cashier",
        )

        # Access cashier endpoint
        response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_scope_match_allowed_admin(self, employee_client, sample_employee):
        """Test that matching scope (admin) is allowed."""
        # Create admin token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="admin",
            employee_additional_roles=[],
            active_scope="admin",
        )

        # Access admin endpoint
        response = employee_client.get(
            "/admin/api/employees",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_scope_mismatch_blocked_waiter_on_admin(self, employee_client, sample_employee):
        """Test that waiter token is blocked on admin routes."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Try to access admin endpoint
        response = employee_client.get(
            "/admin/api/employees",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be blocked
        assert response.status_code == 403
        error_data = json.loads(response.data)
        assert "error" in error_data
        assert "scope" in error_data["error"].lower() or "SCOPE_MISMATCH" in error_data.get(
            "code", ""
        )

    def test_scope_mismatch_blocked_chef_on_cashier(self, employee_client, sample_employee):
        """Test that chef token is blocked on cashier routes."""
        # Create chef token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="chef",
            employee_additional_roles=[],
            active_scope="chef",
        )

        # Try to access cashier endpoint
        response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be blocked
        assert response.status_code == 403
        error_data = json.loads(response.data)
        assert "error" in error_data

    def test_scope_mismatch_blocked_admin_on_waiter(self, employee_client, sample_employee):
        """Test that admin token is blocked on waiter routes."""
        # Create admin token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="admin",
            employee_additional_roles=[],
            active_scope="admin",
        )

        # Try to access waiter endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be blocked
        assert response.status_code == 403

    def test_scope_missing_blocked(self, employee_client, sample_employee):
        """Test that token without scope is blocked on scoped routes."""
        # Create token without active_scope
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope=None,  # No scope
        )

        # Try to access scoped endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be blocked
        assert response.status_code in [401, 403]

    def test_scope_exempt_login_route(self, employee_client, sample_employee):
        """Test that login route is exempt from scope validation."""
        # Login should work without any token
        response = employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        # Should succeed
        assert response.status_code == 200

    def test_scope_exempt_logout_route(self, employee_client):
        """Test that logout route is exempt from scope validation."""
        # Logout should work even without token
        response = employee_client.post("/api/auth/logout")

        # Should succeed (or at least not be blocked by scope guard)
        assert response.status_code == 200

    def test_legacy_api_routes_not_validated(self, employee_client, sample_employee):
        """Test that legacy /api/* routes (without scope prefix) are not validated."""
        # Create token with any scope
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Access legacy API route (no scope prefix)
        response = employee_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should work regardless of scope
        assert response.status_code == 200

    def test_scope_validation_error_message(self, employee_client, sample_employee):
        """Test that scope mismatch returns helpful error message."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Try to access chef endpoint
        response = employee_client.get(
            "/chef/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should return helpful error
        assert response.status_code == 403
        error_data = json.loads(response.data)
        assert "error" in error_data
        assert "chef" in error_data["error"].lower() or "waiter" in error_data["error"].lower()

    def test_no_token_on_scoped_route(self, employee_client):
        """Test that scoped routes require authentication."""
        # Try to access scoped route without token
        response = employee_client.get("/waiter/api/orders")

        # Should require authentication
        assert response.status_code == 401

    def test_system_scope_isolation(self, employee_client, sample_employee):
        """Test that system scope is properly isolated."""
        # Create admin token (not system)
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="admin",
            employee_additional_roles=[],
            active_scope="admin",
        )

        # Try to access system endpoint
        response = employee_client.get(
            "/system/api/settings",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be blocked (system scope required)
        assert response.status_code == 403

    def test_multiple_scopes_not_allowed(self, employee_client, sample_employee):
        """Test that a single token can only have one active scope."""
        # Create token with waiter scope
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=["cashier"],  # Has additional role
            active_scope="waiter",  # But active scope is waiter
        )

        # Should work on waiter routes
        waiter_response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert waiter_response.status_code != 403

        # Should NOT work on cashier routes (even though employee has cashier role)
        cashier_response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert cashier_response.status_code == 403
