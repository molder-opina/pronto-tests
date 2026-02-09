"""
Pytest configuration and fixtures for analytics tests.

Provides common fixtures for authentication and test clients.
"""

import pytest
import requests
from datetime import date, timedelta


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for the API."""
    return "http://localhost:6082"


@pytest.fixture(scope="session")
def admin_credentials():
    """Admin user credentials for testing."""
    return {
        "email": "admin@pronto.test",
        "password": "admin123"
    }


@pytest.fixture(scope="session")
def auth_token(api_base_url, admin_credentials):
    """
    Get authentication token for admin user.
    
    This fixture logs in once per test session and reuses the token.
    """
    response = requests.post(
        f"{api_base_url}/api/employees/auth/login",
        json=admin_credentials
    )
    
    if response.status_code != 200:
        pytest.fail(f"Authentication failed: {response.text}")
    
    # Extract token from cookies or response
    cookies = response.cookies
    return cookies


@pytest.fixture
def client(api_base_url):
    """Unauthenticated HTTP client."""
    class TestClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
        
        def get(self, path, params=None, **kwargs):
            return self.session.get(
                f"{self.base_url}{path}",
                params=params,
                **kwargs
            )
        
        def post(self, path, json=None, **kwargs):
            return self.session.post(
                f"{self.base_url}{path}",
                json=json,
                **kwargs
            )
    
    return TestClient(api_base_url)


@pytest.fixture
def authenticated_client(api_base_url, auth_token):
    """Authenticated HTTP client with admin credentials."""
    class AuthenticatedClient:
        def __init__(self, base_url, cookies):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.cookies.update(cookies)
        
        def get(self, path, params=None, **kwargs):
            return self.session.get(
                f"{self.base_url}{path}",
                params=params,
                **kwargs
            )
        
        def post(self, path, json=None, **kwargs):
            return self.session.post(
                f"{self.base_url}{path}",
                json=json,
                **kwargs
            )
        
        def put(self, path, json=None, **kwargs):
            return self.session.put(
                f"{self.base_url}{path}",
                json=json,
                **kwargs
            )
        
        def delete(self, path, **kwargs):
            return self.session.delete(
                f"{self.base_url}{path}",
                **kwargs
            )
    
    return AuthenticatedClient(api_base_url, auth_token)


@pytest.fixture
def sample_date_range():
    """Provide a sample date range for tests."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    return {
        "start": start_date.isoformat(),
        "end": end_date.isoformat()
    }
