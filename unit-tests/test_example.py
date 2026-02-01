"""Example tests to demonstrate testing setup."""

import pytest


def test_example_basic():
    """Basic test example."""
    assert True


def test_example_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["test_user"]["id"] == 1
    assert sample_data["test_user"]["username"] == "testuser"


def test_example_parametrized():
    """Parametrized test example."""
    test_cases = [
        (1, 2, 3),
        (5, 5, 10),
        (0, 10, 10),
    ]
    for a, b, expected in test_cases:
        assert a + b == expected


@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("hello", "HELLO"),
        ("World", "WORLD"),
        ("python", "PYTHON"),
    ],
)
def test_string_uppercase(input_value, expected):
    """Test string uppercase conversion."""
    assert input_value.upper() == expected


@pytest.mark.slow
def test_slow_operation():
    """Test marked as slow (can be skipped with -m 'not slow')."""
    import time

    time.sleep(0.1)
    assert True


class TestExampleClass:
    """Example test class."""

    def test_method_one(self):
        """Test method one."""
        assert 1 + 1 == 2

    def test_method_two(self, sample_data):
        """Test method two with fixture."""
        assert "test_user" in sample_data

    @pytest.fixture(autouse=True)
    def setup_method_fixture(self):
        """Setup fixture that runs before each test method."""
        # Setup code here
        yield
        # Teardown code here


# TODO: Add real tests for your application
# Example structure:
#
# tests/
# ├── __init__.py
# ├── conftest.py
# ├── test_example.py
# ├── unit/
# │   ├── __init__.py
# │   ├── test_models.py
# │   ├── test_services.py
# │   └── test_utils.py
# └── integration/
#     ├── __init__.py
#     ├── test_api.py
#     └── test_database.py
