"""
Unit tests for service layer.
"""

from unittest.mock import patch

import pytest

from shared.auth.service import AuthError, AuthService, Roles
from shared.services.business_info_service import BusinessInfoService


class TestAuthService:
    """Tests for AuthService."""

    def test_authenticate_valid_credentials(self, db_session, sample_employee):
        """Test authentication with valid credentials."""
        with patch("shared.auth.service.get_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session

            result = AuthService.authenticate(sample_employee.email, "Test123!")

            assert result is not None
            assert result.employee.email == sample_employee.email
            assert result.employee.role == "super_admin"

    def test_authenticate_invalid_email(self, db_session):
        """Test authentication with invalid email."""
        with patch("shared.auth.service.get_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session

            with pytest.raises(AuthError) as exc_info:
                AuthService.authenticate("nonexistent@example.com", "password")

            assert "Credenciales inválidas" in str(exc_info.value)

    def test_authenticate_invalid_password(self, db_session, sample_employee):
        """Test authentication with invalid password."""
        with patch("shared.auth.service.get_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session

            with pytest.raises(AuthError) as exc_info:
                AuthService.authenticate(sample_employee.email, "WrongPassword")

            assert "Credenciales inválidas" in str(exc_info.value)

    def test_has_role_super_admin(self):
        """Test that super_admin has all roles."""
        from shared.auth.service import EmployeeData

        admin = EmployeeData(
            id=1,
            name="Admin",
            email="admin@test.com",
            role=Roles.SUPER_ADMIN,
            additional_roles=None,
        )

        # Super admin should have access to any role
        assert AuthService.has_role(admin, Roles.WAITER) is True
        assert AuthService.has_role(admin, Roles.CHEF) is True
        assert AuthService.has_role(admin, Roles.CASHIER) is True

    def test_has_role_specific(self):
        """Test role checking for specific roles."""
        from shared.auth.service import EmployeeData

        waiter = EmployeeData(
            id=2, name="Waiter", email="waiter@test.com", role=Roles.WAITER, additional_roles=None
        )

        # Should have waiter role
        assert AuthService.has_role(waiter, Roles.WAITER) is True

        # Should not have chef role
        assert AuthService.has_role(waiter, Roles.CHEF) is False


class TestBusinessInfoService:
    """Tests for BusinessInfoService."""

    def test_get_restaurant_name_from_env(self):
        """Test reading RESTAURANT_NAME from env file."""
        name = BusinessInfoService._get_restaurant_name_from_env()

        # Should read from config/general.env
        assert name is not None
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_business_info_empty_db(self, db_session):
        """Test getting business info when database is empty."""
        with patch("shared.services.business_info_service.get_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session

            info = BusinessInfoService.get_business_info()

            # Should return info from env file
            assert info is not None
            assert "business_name" in info
            assert info["currency"] == "MXN"
            assert info["timezone"] == "America/Mexico_City"

    @patch(
        "shared.services.business_info_service.BusinessInfoService._update_restaurant_name_in_env"
    )
    def test_create_business_info(self, mock_update_env, db_session, sample_admin):
        """Test creating business information."""
        with patch("shared.services.business_info_service.get_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session

            data = {
                "business_name": "My Restaurant",
                "address": "123 Main St",
                "city": "Test City",
                "currency": "MXN",
                "timezone": "America/Mexico_City",
            }

            result = BusinessInfoService.create_or_update_business_info(
                data, employee_id=sample_admin.id
            )

            assert result["business_name"] == "My Restaurant"
            assert result["address"] == "123 Main St"

            # Should update env file when business name changes
            mock_update_env.assert_called_once_with("My Restaurant")
