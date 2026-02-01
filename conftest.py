"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

# Ensure src/ is importable before importing project modules
build_path = Path(__file__).parent.parent / "build"
if str(build_path) not in sys.path:
    sys.path.insert(0, str(build_path))

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from shared.models import Base, Customer, Employee, MenuCategory, MenuItem

# Configure PostgreSQL connection for tests
# Uses the local PostgreSQL container from docker-compose
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "pronto"
os.environ["POSTGRES_PASSWORD"] = "pronto123"
os.environ["POSTGRES_DB"] = "pronto"
os.environ["DATABASE_URL"] = "postgresql://pronto:pronto123@localhost:5432/pronto"

# Required environment variables for encryption and hashing
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["PASSWORD_HASH_SALT"] = "test-salt-for-testing-only"


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine connected to PostgreSQL."""
    database_url = os.getenv("DATABASE_URL", "postgresql://pronto:pronto123@localhost:5432/pronto")
    engine = create_engine(database_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup - drop all tables after tests with CASCADE
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS pronto_order_item_modifiers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_order_items CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_order_status_history CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_order_modifications CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_orders CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_notifications CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_promotions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_discount_codes CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_business_config CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_secrets CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_employee_preferences CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_employee_route_access CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_route_permissions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_employees CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_waiter_calls CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_support_tickets CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_dining_sessions CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_menu_item_day_periods CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_menu_item_modifier_groups CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_menu_items CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_menu_categories CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_modifiers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_modifier_groups CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_day_periods CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_product_schedules CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_tables CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_areas CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_customers CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pronto_system_settings CASCADE"))
        conn.commit()
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for a test."""
    session_local = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    session = session_local()

    try:
        yield session
    finally:
        session.rollback()
        # Clear all table data between tests
        for table in reversed(Base.metadata.sorted_tables):
            try:
                session.execute(table.delete())
            except Exception:
                pass  # Table might not exist
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def employee_app():
    """Create a test Flask app for employee application."""
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

    from employees_app.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture(scope="function")
def client_app():
    """Create a test Flask app for client application."""
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

    from clients_app.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture
def employee_client(employee_app):
    """Create a test client for employee application."""
    return employee_app.test_client()


@pytest.fixture
def client_client(client_app):
    """Create a test client for client application."""
    return client_app.test_client()


@pytest.fixture
def sample_employee(db_session):
    """Create a sample employee for testing."""
    employee = Employee(role="super_admin")
    employee.name = "Test Admin"
    employee.email = "test@example.com"
    employee.set_password("Test123!")
    employee.is_active = True

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


@pytest.fixture
def sample_customer(db_session):
    """Create a sample customer for testing."""
    customer = Customer()
    customer.name = "Test Customer"
    customer.email = "customer@example.com"
    customer.phone = "+1234567890"

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    return customer


@pytest.fixture
def sample_category(db_session):
    """Create a sample menu category for testing."""
    category = MenuCategory(
        name="Test Category", description="Test category description", display_order=1
    )

    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    return category


@pytest.fixture
def sample_menu_item(db_session, sample_category):
    """Create a sample menu item for testing."""
    item = MenuItem(
        name="Test Item",
        description="Test item description",
        price=10.50,
        category_id=sample_category.id,
        is_available=True,
        preparation_time_minutes=15,
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    return item


@pytest.fixture
def sample_menu_items(db_session, sample_category):
    """Create multiple sample menu items for testing."""
    items = []
    for i in range(5):
        item = MenuItem(
            name=f"Test Item {i + 1}",
            description=f"Test item {i + 1} description",
            price=10.0 + i,
            category_id=sample_category.id,
            is_available=True,
            preparation_time_minutes=10 + i,
        )
        db_session.add(item)
        items.append(item)

    db_session.commit()
    for item in items:
        db_session.refresh(item)

    return items


@pytest.fixture
def sample_waiter(db_session):
    """Create a sample waiter employee for testing."""
    employee = Employee(role="waiter")
    employee.name = "Test Waiter"
    employee.email = "waiter@test.com"
    employee.set_password("Test123!")
    employee.is_active = True
    employee.allow_scopes = ["waiter"]

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


@pytest.fixture
def sample_chef(db_session):
    """Create a sample chef employee for testing."""
    employee = Employee(role="chef")
    employee.name = "Test Chef"
    employee.email = "chef@test.com"
    employee.set_password("Test123!")
    employee.is_active = True
    employee.allow_scopes = ["chef"]

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin employee for testing."""
    employee = Employee(role="super_admin")
    employee.name = "Test Admin"
    employee.email = "admin@test.com"
    employee.set_password("Test123!")
    employee.is_active = True
    employee.allow_scopes = ["waiter", "chef", "cashier", "admin"]

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


@pytest.fixture
def sample_cashier(db_session):
    """Create a sample cashier employee for testing."""
    employee = Employee(role="cashier")
    employee.name = "Test Cashier"
    employee.email = "cashier@test.com"
    employee.set_password("Test123!")
    employee.is_active = True
    employee.allow_scopes = ["cashier"]

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


@pytest.fixture(autouse=True)
def init_db_for_tests(test_db_engine):
    """Initialize database engine for services that require it."""
    from shared.db import init_engine

    init_engine(test_db_engine)
    yield
    # Cleanup if needed


@pytest.fixture
def authenticated_session(employee_client, sample_employee):
    """Create an authenticated session for an employee."""
    import json

    # Login the employee
    response = employee_client.post(
        "/api/auth/login",
        data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    return employee_client
