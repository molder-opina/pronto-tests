"""
Pytest configuration and fixtures for analytics tests.

Provides common fixtures for authentication and test clients.
"""

import pytest
import requests
from datetime import date, timedelta





@pytest.fixture
def sample_date_range():
    """Provide a sample date range for tests."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    return {
        "start": start_date.isoformat(),
        "end": end_date.isoformat()
    }
