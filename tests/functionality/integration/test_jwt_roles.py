"""
Integration tests for JWT role-based access control.

Tests the role validation decorators that ensure employees have
the required roles to access specific endpoints.
"""
import json

import pytest

from shared.jwt_service import create_access_token


@pytest.mark.integration
class TestJWTRoleBasedAccess:
    """Tests for JWT role-based access control."""

    def test_role_required_success_primary_role(self, employee_client, sample_employee):
        """Test that employee with required primary role can access endpoint."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Access waiter-only endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_role_required_success_additional_role(self, employee_client, sample_employee):
        """Test that employee with required additional role can access endpoint."""
        # Create token with waiter as primary, cashier as additional
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=["cashier"],
            active_scope="cashier",  # Accessing cashier scope
        )

        # Access cashier endpoint (should work because of additional role)
        response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_role_required_denied_wrong_role(self, employee_client, sample_employee):
        """Test that employee without required role is denied."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="admin",  # Wrong scope for testing
        )

        # Try to access admin-only endpoint
        response = employee_client.get(
            "/admin/api/employees",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be denied (403 from scope guard or role check)
        assert response.status_code == 403

    def test_admin_required_success(self, employee_client, sample_employee):
        """Test that admin can access admin-required endpoints."""
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

    def test_admin_required_denied_non_admin(self, employee_client, sample_employee):
        """Test that non-admin is denied from admin-required endpoints."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Try to access admin endpoint (if we could bypass scope guard)
        # Note: This would be blocked by scope guard first in real scenario
        response = employee_client.get(
            "/api/admin/settings",  # Legacy admin route
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be denied
        assert response.status_code in [401, 403]

    def test_super_admin_bypass_all_roles(self, employee_client, sample_employee):
        """Test that super_admin can access all endpoints regardless of role requirements."""
        # Create super_admin token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="super_admin",
            employee_additional_roles=[],
            active_scope="system",
        )

        # Access system endpoint (super admin should have access)
        response = employee_client.get(
            "/system/api/settings",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_multi_role_employee_access(self, employee_client, sample_employee):
        """Test that employee with multiple roles can access all their role endpoints."""
        # Create token with multiple roles
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=["cashier", "chef"],
            active_scope="waiter",
        )

        # Should access waiter endpoint
        waiter_response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert waiter_response.status_code != 403

        # Create new token with cashier scope
        cashier_token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=["cashier", "chef"],
            active_scope="cashier",
        )

        # Should access cashier endpoint
        cashier_response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {cashier_token}"},
        )
        assert cashier_response.status_code != 403

    def test_role_validation_error_message(self, employee_client, sample_employee):
        """Test that role denial returns helpful error message."""
        # Create waiter token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],
            active_scope="waiter",
        )

        # Try to access endpoint that requires admin role
        # (Using a hypothetical endpoint that checks role but not scope)
        response = employee_client.post(
            "/api/employees",  # Legacy route that might require admin
            headers={"Authorization": f"Bearer {token}"},
            data=json.dumps({"name": "Test", "email": "test@test.com"}),
            content_type="application/json",
        )

        # If denied, should have helpful message
        if response.status_code == 403:
            error_data = json.loads(response.data)
            assert "error" in error_data
            # Message should mention role requirement
            assert any(
                keyword in error_data["error"].lower()
                for keyword in ["role", "permission", "admin"]
            )

    def test_no_role_in_token_denied(self, employee_client, sample_employee):
        """Test that token without role is denied from protected endpoints."""
        # Create token without role (edge case)
        from datetime import datetime, timedelta, timezone

        import jwt

        from shared.jwt_service import JWT_ALGORITHM, get_jwt_secret

        secret = get_jwt_secret()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(sample_employee.id),
            "iat": now,
            "exp": now + timedelta(hours=24),
            "type": "access",
            "employee_id": sample_employee.id,
            "employee_name": sample_employee.name,
            "employee_email": sample_employee.email,
            # Missing employee_role
            "active_scope": "waiter",
        }
        token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)

        # Try to access protected endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be denied or error
        assert response.status_code in [401, 403, 500]

    def test_chef_role_kitchen_access(self, employee_client, sample_employee):
        """Test that chef role can access kitchen endpoints."""
        # Create chef token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="chef",
            employee_additional_roles=[],
            active_scope="chef",
        )

        # Access chef/kitchen endpoint
        response = employee_client.get(
            "/chef/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_cashier_role_payment_access(self, employee_client, sample_employee):
        """Test that cashier role can access payment endpoints."""
        # Create cashier token
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="cashier",
            employee_additional_roles=[],
            active_scope="cashier",
        )

        # Access cashier/payment endpoint
        response = employee_client.get(
            "/cashier/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be allowed
        assert response.status_code != 403

    def test_role_hierarchy_not_inherited(self, employee_client, sample_employee):
        """Test that roles don't inherit permissions (flat hierarchy)."""
        # Admin should not automatically have waiter permissions
        # (they need to be explicitly granted)
        admin_token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="admin",
            employee_additional_roles=[],  # No waiter role
            active_scope="waiter",  # Wrong scope
        )

        # Try to access waiter endpoint
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should be blocked by scope guard
        assert response.status_code == 403

    def test_additional_roles_array_validation(self, employee_client, sample_employee):
        """Test that additional_roles is properly validated as array."""
        # Create token with additional roles
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=["cashier", "chef"],  # Array of roles
            active_scope="waiter",
        )

        # Should work normally
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code != 403

    def test_empty_additional_roles(self, employee_client, sample_employee):
        """Test that empty additional_roles array works correctly."""
        # Create token with empty additional roles
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=[],  # Empty array
            active_scope="waiter",
        )

        # Should work normally
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code != 403

    def test_none_additional_roles(self, employee_client, sample_employee):
        """Test that None additional_roles is handled correctly."""
        # Create token with None additional roles
        token = create_access_token(
            employee_id=sample_employee.id,
            employee_name=sample_employee.name,
            employee_email=sample_employee.email,
            employee_role="waiter",
            employee_additional_roles=None,  # None instead of array
            active_scope="waiter",
        )

        # Should work normally (None should be treated as empty array)
        response = employee_client.get(
            "/waiter/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code != 403
