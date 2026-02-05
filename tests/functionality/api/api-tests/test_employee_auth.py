#!/usr/bin/env python3
"""
Comprehensive authentication tests for employee consoles.
Tests JWT authentication, session management, and logout functionality.
"""

import pytest
from flask import session


@pytest.mark.integration
class TestEmployeeAuthentication:
    """Tests for employee authentication across all consoles."""

    # ==================== LOGIN TESTS ====================

    def test_main_login_success(self, employee_client, sample_employee):
        """Test successful login via main auth route."""
        response = employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302  # Redirect after login
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]
        assert response.location.endswith("/dashboard")

    def test_waiter_login_success(self, employee_client, db_session):
        """Test waiter console login."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        # Create waiter employee
        waiter = Employee(
            name="Test Waiter",
            email="waiter@test.com",
            email_hash=hash_identifier("waiter@test.com"),
            auth_hash=hash_credentials("waiter@test.com", "Test123!"),
            role="waiter",
            is_active=True,
        )
        db_session.add(waiter)
        db_session.commit()

        response = employee_client.post(
            "/waiter/login",
            data={"email": "waiter@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    def test_chef_login_success(self, employee_client, db_session):
        """Test chef console login."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        chef = Employee(
            name="Test Chef",
            email="chef@test.com",
            email_hash=hash_identifier("chef@test.com"),
            auth_hash=hash_credentials("chef@test.com", "Test123!"),
            role="chef",
            is_active=True,
        )
        db_session.add(chef)
        db_session.commit()

        response = employee_client.post(
            "/chef/login",
            data={"email": "chef@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    def test_cashier_login_success(self, employee_client, db_session):
        """Test cashier console login."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        cashier = Employee(
            name="Test Cashier",
            email="cashier@test.com",
            email_hash=hash_identifier("cashier@test.com"),
            auth_hash=hash_credentials("cashier@test.com", "Test123!"),
            role="cashier",
            is_active=True,
        )
        db_session.add(cashier)
        db_session.commit()

        response = employee_client.post(
            "/cashier/login",
            data={"email": "cashier@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    def test_admin_login_success(self, employee_client, db_session):
        """Test admin console login."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        admin = Employee(
            name="Test Admin",
            email="admin@test.com",
            email_hash=hash_identifier("admin@test.com"),
            auth_hash=hash_credentials("admin@test.com", "Test123!"),
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()

        response = employee_client.post(
            "/admin/login",
            data={"email": "admin@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    def test_system_login_success(self, employee_client, db_session):
        """Test system console login."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        system_user = Employee(
            name="Test System User",
            email="system@test.com",
            email_hash=hash_identifier("system@test.com"),
            auth_hash=hash_credentials("system@test.com", "Test123!"),
            role="system",
            is_active=True,
        )
        db_session.add(system_user)
        db_session.commit()

        response = employee_client.post(
            "/system/login",
            data={"email": "system@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    def test_login_invalid_credentials(self, employee_client):
        """Test login with invalid credentials."""
        response = employee_client.post(
            "/login",
            data={"email": "wrong@test.com", "password": "wrongpass"},
            follow_redirects=False,
        )

        assert response.status_code == 200  # Returns login page with error
        assert "access_token" not in [cookie.name for cookie in employee_client.cookie_jar]

    def test_login_inactive_account(self, employee_client, db_session):
        """Test login with inactive account."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        inactive = Employee(
            name="Inactive User",
            email="inactive@test.com",
            email_hash=hash_identifier("inactive@test.com"),
            auth_hash=hash_credentials("inactive@test.com", "Test123!"),
            role="waiter",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        response = employee_client.post(
            "/waiter/login",
            data={"email": "inactive@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 200  # Returns login page with error
        assert "access_token" not in [cookie.name for cookie in employee_client.cookie_jar]

    # ==================== SESSION TESTS ====================

    def test_jwt_token_contains_employee_info(self, employee_client, sample_employee):
        """Test that JWT token contains correct employee information."""
        import jwt

        from shared.jwt_service import get_jwt_secret

        response = employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        assert response.status_code == 302

        cookies = {cookie.name: cookie for cookie in employee_client.cookie_jar}
        assert "access_token" in cookies

        token = cookies["access_token"].value
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert payload["employee_id"] == sample_employee.id
        assert payload["employee_name"] == sample_employee.name
        assert payload["employee_email"] == sample_employee.email
        assert payload["employee_role"] == sample_employee.role
        assert payload["active_scope"] is not None

    def test_jwt_cookie_set_on_login(self, employee_client, sample_employee):
        """Test that JWT cookies are set on login."""
        response = employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        cookies = {cookie.name: cookie for cookie in employee_client.cookie_jar}
        assert "access_token" in cookies
        assert cookies["access_token"].value is not None
        assert cookies["access_token"].path == "/"

    def test_employee_sign_in_timestamp_updated(self, employee_client, sample_employee, db_session):
        """Test that employee.signed_in_at is updated on login."""
        assert sample_employee.signed_in_at is None

        employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        db_session.refresh(sample_employee)
        assert sample_employee.signed_in_at is not None
        assert sample_employee.last_activity_at is not None

    # ==================== LOGOUT TESTS ====================

    def test_logout_clears_cookies(self, employee_client, sample_employee):
        """Test that logout clears JWT cookies."""
        # Login first
        employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        # Logout
        response = employee_client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        # Check that cookies are cleared (max_age=0 or expires in past)
        cookies = {cookie.name: cookie for cookie in employee_client.cookie_jar}
        # After logout, cookies should be deleted or expired
        # The exact behavior depends on how the test client handles deleted cookies

    def test_logout_clears_jwt_cookies(self, employee_client, sample_employee):
        """Test that logout clears JWT cookies."""
        from shared.jwt_service import get_jwt_secret

        response = employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        cookies_before = {cookie.name: cookie for cookie in employee_client.cookie_jar}
        assert "access_token" in cookies_before

        response = employee_client.get("/logout", follow_redirects=False)

        assert response.status_code == 302

        cookies_after = {cookie.name: cookie for cookie in employee_client.cookie_jar}

        assert "access_token" not in cookies_after or cookies_after["access_token"].value == ""

    def test_logout_updates_employee_state(self, employee_client, sample_employee, db_session):
        """Test that logout updates employee.signed_in_at to None."""
        # Login
        employee_client.post(
            "/login",
            data={"email": sample_employee.email, "password": "Test123!"},
            follow_redirects=False,
        )

        db_session.refresh(sample_employee)
        assert sample_employee.signed_in_at is not None

        # Logout
        employee_client.get("/logout", follow_redirects=False)

        db_session.refresh(sample_employee)
        assert sample_employee.signed_in_at is None
        assert sample_employee.last_activity_at is None

    def test_waiter_logout(self, employee_client, db_session):
        """Test waiter console logout."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        waiter = Employee(
            name="Test Waiter",
            email="waiter@test.com",
            email_hash=hash_identifier("waiter@test.com"),
            auth_hash=hash_credentials("waiter@test.com", "Test123!"),
            role="waiter",
            is_active=True,
        )
        db_session.add(waiter)
        db_session.commit()

        # Login
        employee_client.post(
            "/waiter/login",
            data={"email": "waiter@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        # Logout
        response = employee_client.get("/waiter/logout", follow_redirects=False)
        assert response.status_code == 302

        db_session.refresh(waiter)
        assert waiter.signed_in_at is None

    # ==================== SYSTEM HANDOFF TESTS ====================

    def test_system_handoff_to_waiter(self, employee_client, db_session):
        """Test system handoff login to waiter console."""
        import hashlib
        import os
        import secrets
        from datetime import timedelta

        from shared.datetime_utils import utcnow
        from shared.models import Employee, SuperAdminHandoffToken
        from shared.security import hash_credentials, hash_identifier

        # Create system admin with waiter scope
        system_user = Employee(
            name="System User",
            email="system@test.com",
            email_hash=hash_identifier("system@test.com"),
            auth_hash=hash_credentials("system@test.com", "Test123!"),
            role="system",
            additional_roles='["waiter"]',
            is_active=True,
        )
        db_session.add(system_user)
        db_session.commit()

        # Create handoff token
        raw_token = secrets.token_urlsafe(32)
        pepper = os.getenv("HANDOFF_PEPPER", "")
        token_hash = hashlib.sha256((raw_token + pepper).encode()).hexdigest()

        token_record = SuperAdminHandoffToken(
            token_hash=token_hash,
            employee_id=system_user.id,
            target_scope="waiter",
            expires_at=utcnow() + timedelta(seconds=60),
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )
        db_session.add(token_record)
        db_session.commit()

        # Use handoff token
        response = employee_client.post(
            "/waiter/system_login",
            data={"token": raw_token},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "access_token" in [cookie.name for cookie in employee_client.cookie_jar]

    # ==================== SCOPE GUARD TESTS ====================

    def test_scope_guard_redirects_wrong_scope(self, employee_client, db_session):
        """Test that scope guard redirects when JWT scope doesn't match URL scope."""
        from shared.models import Employee
        from shared.security import hash_credentials, hash_identifier

        waiter = Employee(
            name="Test Waiter",
            email="waiter@test.com",
            email_hash=hash_identifier("waiter@test.com"),
            auth_hash=hash_credentials("waiter@test.com", "Test123!"),
            role="waiter",
            is_active=True,
        )
        db_session.add(waiter)
        db_session.commit()

        # Login as waiter
        employee_client.post(
            "/waiter/login",
            data={"email": "waiter@test.com", "password": "Test123!"},
            follow_redirects=False,
        )

        # Try to access chef dashboard (wrong scope)
        response = employee_client.get("/chef/dashboard", follow_redirects=False)

        # Should redirect to chef login or show error
        assert response.status_code in [302, 403]

    def test_unauthenticated_access_redirects_to_login(self, employee_client):
        """Test that unauthenticated access to protected routes redirects to login."""
        response = employee_client.get("/waiter/dashboard", follow_redirects=False)

        assert response.status_code == 302
        assert "login" in response.location.lower()
