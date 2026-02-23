"""
Central conftest.py for the pronto-tests project.

Provides common fixtures for API integration and employee-facing application tests.
"""

import os
import sys
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch
import psycopg2
import requests

from datetime import date, timedelta


# --- Path Setup for Module Discovery ---
# Add src directories to path for package discovery as early as possible
# pronto_libs_src_path is no longer needed here as pronto-libs is installed in editable mode
pronto_client_src_path = Path(__file__).parent.parent.parent / "pronto-client" / "src"
# pronto_api_src_path is no longer needed here as pronto-api is installed in editable mode

for p in [pronto_client_src_path]:  # Only pronto_client_src_path remains
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
# --- End Path Setup ---


# Import from pronto_shared after adding to path
from pronto_shared.db import get_session, validate_schema
from pronto_shared.models import Base, Employee, SuperAdminHandoffToken
from pronto_shared.security import hash_credentials, hash_identifier
from pronto_shared.jwt_service import create_access_token, create_refresh_token
from pronto_shared.config import load_config
from pronto_shared.extensions import csrf


@pytest.fixture(scope="session", autouse=True)
def mock_validate_schema():
    """
    Mocks pronto_shared.db.validate_schema to prevent SystemExit during tests.
    """
    with patch("pronto_shared.db.validate_schema") as mock:
        yield mock


@pytest.fixture(scope="session")
def app_config():
    """Load configuration for the API tests."""
    # Use a dummy app name for testing config
    os.environ["PRONTO_APP_NAME"] = "pronto-api-test"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_DB"] = (
        f"pronto_test_db_{os.getpid()}"  # Set the database name for config.py
    )
    os.environ["DATABASE_URL"] = (
        f"postgresql://pronto:pronto123@localhost:5432/{os.environ['POSTGRES_DB']}"  # Use POSTGRES_DB for consistency
    )
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
    os.environ["SECRET_KEY"] = "test-flask-secret"
    os.environ["HANDOFF_PEPPER"] = "test-handoff-pepper"
    os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:6080,http://localhost:6081"
    os.environ["PRONTO_SYSTEM_VERSION"] = "test-version"
    os.environ["DEBUG_MODE"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"

    config = load_config("pronto-api-test")
    return config


@pytest.fixture(scope="session")
def create_test_database(app_config):
    """
    Create a fresh test database for the entire test session.
    Drops it after the session concludes.
    """
    db_name = app_config.db_name
    db_user = app_config.db_user
    db_password = app_config.db_password
    db_host = app_config.db_host
    db_port = app_config.db_port

    # Connect to the default 'postgres' database to create/drop the test database
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop existing test database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE);")
        # Create a new test database
        cursor.execute(f"CREATE DATABASE {db_name};")

        yield  # Yield control to tests

    except psycopg2.Error as e:
        pytest.fail(f"Database creation/setup failed: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            # Reconnect to drop the database cleanly after tests
            conn = psycopg2.connect(
                dbname="postgres",
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE);")
            cursor.close()
            conn.close()


@pytest.fixture(scope="session")
def test_db_engine(app_config, create_test_database):  # Added dependency
    """Provide a SQLAlchemy engine for a test database."""
    engine = create_engine(app_config.sqlalchemy_uri)
    # Recreate all tables for a clean test environment
    Base.metadata.drop_all(engine)  # This should now work as db exists
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Provide a transactional database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()

    # Seed some basic data required by tests
    waiter = Employee(
        name="Test Waiter",
        email="waiter@pronto.com",
        email_hash=hash_identifier("waiter@pronto.com"),
        auth_hash=hash_credentials("waiter@pronto.com", "Test123!"),
        role="waiter",
        is_active=True,
    )
    admin = Employee(
        name="Test Admin",
        email="admin@pronto.com",
        email_hash=hash_identifier("admin@pronto.com"),
        auth_hash=hash_credentials("admin@pronto.com", "Test123!"),
        role="admin",
        is_active=True,
    )
    session.add_all([waiter, admin])
    session.commit()  # Commit initial seed to ensure IDs are generated
    session.refresh(waiter)
    session.refresh(admin)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def sample_employee(db_session):
    """Provide a sample employee (waiter) for tests."""
    return db_session.query(Employee).filter_by(email="waiter@pronto.com").first()


@pytest.fixture(scope="function")
def sample_admin(db_session):
    """Provide a sample admin employee for tests."""
    return db_session.query(Employee).filter_by(email="admin@pronto.com").first()


@pytest.fixture(scope="session")
def flask_app(app_config, test_db_engine):
    """Create and configure a Flask app for testing."""
    # Ensure environment variables are loaded for the app to pick them up
    os.environ["DATABASE_URL"] = app_config.sqlalchemy_uri  # Corrected here
    os.environ["SECRET_KEY"] = app_config.secret_key
    os.environ["PRONTO_SYSTEM_VERSION"] = app_config.system_version
    os.environ["DEBUG_MODE"] = str(app_config.debug_mode).lower()
    os.environ["LOG_LEVEL"] = app_config.log_level

    # Dynamically import create_app only after paths are set
    # The current working directory should make 'api_app' discoverable as pronto-api is installed in editable mode.
    # No need for explicit sys.path manipulation here if installed editable.
    from api_app.app import create_app as create_api_app
    from pronto_shared.db import init_engine

    # Temporarily disable CSRF for testing
    with patch("pronto_shared.extensions.csrf.init_app") as mock_init_app:
        app = create_api_app()
        # Ensure init_app was called, but allow it to do nothing
        mock_init_app.assert_called_once()  # Verify that init_app was called
        app.config["TESTING"] = True
        app.config["DEBUG"] = True
        # Explicitly disable CSRF protection for testing (though mocked init_app handles it)
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["CSRF_ENABLED"] = False

        with app.app_context():
            init_engine(app_config)  # Initialize DB engine from pronto_shared
            # Any other app context setup from api_app/app.py init_runtime can go here
            yield app


@pytest.fixture(scope="function")
def employee_client(flask_app, sample_admin):
    """Provide a Flask test client authenticated as an admin."""
    client = flask_app.test_client()

    # For testing, we disable CSRF. So, no need to fetch/send CSRF token.
    # The login should directly return JWT tokens.
    login_data = {
        "email": sample_admin.email,
        "password": "Test123!",  # Assuming default password
    }

    response = client.post("/api/employees/auth/login", json=login_data)

    assert response.status_code == 200, f"Login failed: {response.json}"
    assert "access_token" in response.json["data"]

    # The Flask test client automatically handles cookies, so JWTs in cookies
    # should be preserved for subsequent requests.

    return client


# Fixtures from tests/functionality/api/analytics/conftest.py
@pytest.fixture(scope="session")
def admin_credentials():
    """Admin user credentials for testing."""
    return {"email": "admin@pronto.com", "password": "Test123!"}


@pytest.fixture(scope="session")
def auth_token(flask_app, admin_credentials):
    """
    Get authentication token for admin user using Flask test client.
    """
    client = flask_app.test_client()
    login_data = admin_credentials

    # No need to fetch CSRF token explicitly with test_client,
    # or it should be bypassed by app.config["WTF_CSRF_ENABLED"] = False
    response = client.post("/api/employees/auth/login", json=login_data)

    assert response.status_code == 200, f"Login failed: {response.json}"
    assert "access_token" in response.json["data"]

    # The Flask test client automatically handles cookies/headers, so JWTs
    # are managed across requests.
    return response.json["data"]["access_token"]  # Return just the token


@pytest.fixture
def client(flask_app):
    """Unauthenticated Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def authenticated_client(client, auth_token):
    """Authenticated Flask test client with admin credentials."""
    # Add Authorization header for subsequent requests
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {auth_token}"
    return client


@pytest.fixture
def sample_category(db_session):
    """Provide a sample menu category for tests."""
    from pronto_shared.models import Category

    category = Category(name="Bebidas", description="Bebidas del menú", display_order=1)
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def sample_table(db_session):
    """Provide a sample table for tests."""
    from pronto_shared.models import Table, Area

    area = Area(name="Principal", display_order=1)
    db_session.add(area)
    db_session.flush()
    table = Table(table_number="TEST1", capacity=4, is_active=True, area_id=area.id)
    db_session.add(table)
    db_session.commit()
    return table


@pytest.fixture
def sample_customer(db_session):
    """Provide a sample customer for tests."""
    from pronto_shared.models import Customer

    customer = Customer(
        email="testcustomer@pronto.com",
        first_name="Test",
        last_name="Customer",
        phone="+1234567890",
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def client_api(flask_app):
    """Unauthenticated API client for client-facing tests."""
    return flask_app.test_client()
