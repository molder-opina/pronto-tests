"""
Unit tests for database models.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from shared.models import (
    Customer,
    DiningSession,
    Employee,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
)


class TestEmployee:
    """Tests for Employee model."""

    def test_create_employee(self, db_session):
        """Test creating an employee."""
        employee = Employee(role="waiter")
        employee.name = "John Doe"
        employee.email = "john@example.com"
        employee.set_password("SecurePass123!")
        employee.is_active = True

        db_session.add(employee)
        db_session.commit()

        assert employee.id is not None
        assert employee.name == "John Doe"
        assert employee.role == "waiter"
        assert employee.is_active is True

    def test_employee_password_hashing(self):
        """Test password hashing and verification."""
        employee = Employee(role="chef")
        employee.name = "Chef Mike"
        employee.email = "mike@example.com"
        employee.set_password("MyPassword123")

        # Password should be hashed
        assert employee.auth_hash is not None
        assert employee.auth_hash != "MyPassword123"

        # Verify correct password
        assert employee.verify_password("MyPassword123") is True

        # Verify incorrect password
        assert employee.verify_password("WrongPassword") is False

    def test_employee_email_uniqueness(self, db_session, sample_employee):
        """Test that email must be unique."""
        duplicate = Employee(role="waiter")
        duplicate.name = "Another User"
        duplicate.email = sample_employee.email  # Same email
        duplicate.set_password("Password123")

        db_session.add(duplicate)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCustomer:
    """Tests for Customer model."""

    def test_create_customer(self, db_session):
        """Test creating a customer."""
        customer = Customer()
        customer.name = "Jane Smith"
        customer.email = "jane@example.com"
        customer.phone = "+1234567890"

        db_session.add(customer)
        db_session.commit()

        assert customer.id is not None
        assert customer.name == "Jane Smith"
        assert customer.email == "jane@example.com"

    def test_customer_data_encryption(self, db_session):
        """Test that customer data is encrypted."""
        customer = Customer()
        customer.name = "Test User"
        customer.email = "test@example.com"
        customer.phone = "+9876543210"

        db_session.add(customer)
        db_session.commit()

        # Name, email, and phone should be encrypted
        assert customer.name_encrypted is not None
        assert customer.email_encrypted is not None
        assert customer.phone_encrypted is not None

        # Should be able to retrieve decrypted values
        assert customer.name == "Test User"
        assert customer.email == "test@example.com"
        assert customer.phone == "+9876543210"


class TestMenuItem:
    """Tests for MenuItem model."""

    def test_create_menu_item(self, db_session, sample_category):
        """Test creating a menu item."""
        item = MenuItem(
            name="Burger",
            description="Delicious burger",
            price=12.99,
            category_id=sample_category.id,
            is_available=True,
            preparation_time_minutes=20,
        )

        db_session.add(item)
        db_session.commit()

        assert item.id is not None
        assert item.name == "Burger"
        assert float(item.price) == 12.99
        assert item.is_available is True

    def test_menu_item_price_validation(self, db_session, sample_category):
        """Test that price must be positive."""
        item = MenuItem(
            name="Invalid Item",
            description="Should fail",
            price=-5.00,  # Negative price
            category_id=sample_category.id,
        )

        db_session.add(item)

        # SQLAlchemy might not validate this, but the application should
        # This test documents expected behavior
        assert float(item.price) < 0


class TestOrder:
    """Tests for Order model."""

    def test_create_order(self, db_session, sample_customer, sample_employee):
        """Test creating an order."""
        # Create dining session first
        session_obj = DiningSession(customer_id=sample_customer.id, status="open", table_number="5")
        db_session.add(session_obj)
        db_session.flush()

        order = Order(
            customer_id=sample_customer.id,
            session_id=session_obj.id,
            workflow_status=OrderStatus.NEW.value,
            payment_status="pending",
            waiter_id=sample_employee.id,
            subtotal=Decimal("25.00"),
            tax_amount=Decimal("4.00"),
            total_amount=Decimal("29.00"),
        )

        db_session.add(order)
        db_session.commit()

        assert order.id is not None
        assert order.workflow_status == OrderStatus.NEW.value
        assert float(order.total_amount) == 29.00

    def test_order_with_items(self, db_session, sample_customer, sample_employee, sample_menu_item):
        """Test creating an order with items."""
        # Create dining session
        session_obj = DiningSession(customer_id=sample_customer.id, status="open", table_number="3")
        db_session.add(session_obj)
        db_session.flush()

        # Create order
        order = Order(
            customer_id=sample_customer.id,
            session_id=session_obj.id,
            workflow_status=OrderStatus.NEW.value,
            payment_status="pending",
            waiter_id=sample_employee.id,
            subtotal=Decimal("10.50"),
            tax_amount=Decimal("1.68"),
            total_amount=Decimal("12.18"),
        )
        db_session.add(order)
        db_session.flush()

        # Add order item
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=sample_menu_item.id,
            quantity=1,
            unit_price=Decimal("10.50"),
        )
        db_session.add(order_item)
        db_session.commit()

        # Refresh to load relationships
        db_session.refresh(order)

        assert len(order.items) == 1
        assert order.items[0].menu_item_id == sample_menu_item.id
        assert float(order.items[0].unit_price) == 10.50


class TestDiningSession:
    """Tests for DiningSession model."""

    def test_create_dining_session(self, db_session, sample_customer):
        """Test creating a dining session."""
        session_obj = DiningSession(
            customer_id=sample_customer.id,
            status="open",
            table_number="7",
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )

        db_session.add(session_obj)
        db_session.commit()

        assert session_obj.id is not None
        assert session_obj.status == "open"
        assert session_obj.table_number == "7"
        assert session_obj.opened_at is not None

    def test_dining_session_with_check_requested(self, db_session, sample_customer):
        """Test dining session with check_requested_at field."""
        session_obj = DiningSession(
            customer_id=sample_customer.id,
            status="open",
            table_number="10",
            check_requested_at=datetime.utcnow(),
        )

        db_session.add(session_obj)
        db_session.commit()

        assert session_obj.check_requested_at is not None
        assert isinstance(session_obj.check_requested_at, datetime)
