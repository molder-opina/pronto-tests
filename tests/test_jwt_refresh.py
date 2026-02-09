
import pytest
from datetime import datetime, timedelta, timezone
from pronto_shared.jwt_service import create_refresh_token, decode_token
from api_app.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    # Ensure secret key is set for JWT
    app.config["SECRET_KEY"] = "testing-secret-key"
    with app.test_client() as client:
        yield client

def test_refresh_token_success(client):
    """
    Test that a valid refresh token generates a new access token and new refresh token.
    """
    # Create valid refresh token manually
    # We assume 'employees' scope and id=1 for test
    refresh_token = create_refresh_token(employee_id=1, expires_days=1)
    
    # Set cookie
    client.set_cookie("localhost", "refresh_token", refresh_token)
    
    # Mock employee retrieval in service layer? 
    # Since this is integration test, we need DB to return employee 1.
    # Without DB, this test might fail if employee 1 doesn't exist.
    # We can mock get_employee in auth.py if we patch it.
    
    # Assuming employee 1 exists or using mocking:
    from unittest.mock import patch
    with patch("api_app.routes.employees.auth.get_employee") as mock_get_employee:
        mock_get_employee.return_value = {
            "id": 1,
            "name": "Test Employee",
            "email": "test@example.com",
            "role": "waiter"
        }
        
        response = client.post("/api/employees/auth/refresh")
        
        # Expect success
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        
        # Verify Cookies
        cookies = {c.name: c.value for c in client.cookie_jar}
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        
        # Verify rotation (new token != old token)
        assert cookies["refresh_token"] != refresh_token

def test_refresh_token_missing(client):
    """Test missing refresh token returns 401."""
    response = client.post("/api/employees/auth/refresh")
    assert response.status_code == 401
    assert "No refresh token provided" in response.get_json()["error"]

def test_refresh_token_revoked(client):
    """Test revoked (blacklisted) token returns 401."""
    refresh_token = create_refresh_token(employee_id=1, expires_days=1)
    client.set_cookie("localhost", "refresh_token", refresh_token)
    
    # Revoke it first
    client.post("/api/employees/auth/revoke")
    
    # Try refresh
    response = client.post("/api/employees/auth/refresh")
    assert response.status_code == 401
    assert "Token revoked" in response.get_json()["error"]
