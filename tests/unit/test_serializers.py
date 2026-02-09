"""
Tests for serializers module.
"""

import pytest

from pronto_shared.serializers import serialize_customer
from pronto_shared.utils import mask_email, mask_phone


class TestMaskEmail:
    """Test email masking function."""

    def test_mask_email_basic(self):
        """Test basic email masking."""
        assert mask_email("juan.perez@empresa.com") == "j***@empresa.com"
        assert mask_email("test@example.com") == "t***@example.com"

    def test_mask_email_short_user(self):
        """Test email masking with short username."""
        assert mask_email("a@example.com") == "a***@example.com"

    def test_mask_email_invalid(self):
        """Test email masking with invalid email."""
        assert mask_email(None) is None
        assert mask_email("") == ""
        assert mask_email("invalid_email") == "invalid_email"


class TestMaskPhone:
    """Test phone masking function."""

    def test_mask_phone_international(self):
        """Test phone masking for international numbers."""
        assert mask_phone("+56912345678") == "+569******78"
        assert mask_phone("+1-555-123-4567") == "+1-***4567"

    def test_mask_phone_national(self):
        """Test phone masking for national numbers."""
        assert mask_phone("912345678") == "912***678"
        assert mask_phone("1234567") == "****567"

    def test_mask_phone_invalid(self):
        """Test phone masking with invalid phone."""
        assert mask_phone(None) is None
        assert mask_phone("") == ""
        assert mask_phone("123") == "****"


class TestSerializeCustomer:
    """Test serialize_customer function."""

    def test_serialize_customer_masks_pii_by_default(self):
        """Verify that email and phone are masked by default."""
        from pronto_shared.models import Customer

        customer = Customer(
            id="cust_123",
            email="test@example.com",
            phone="+56912345678",
            name="Test Customer",
        )

        result = serialize_customer(customer)

        # PII should be masked
        assert result["email"] == "t***@example.com"
        assert result["phone"] == "+569******78"

        # Non-PII fields should be intact
        assert result["id"] == "cust_123"
        assert result["name"] == "Test Customer"

    def test_serialize_customer_no_masking(self):
        """Verify that PII is NOT masked when mask_pii=False."""
        from pronto_shared.models import Customer

        customer = Customer(
            id="cust_123",
            email="test@example.com",
            phone="+56912345678",
            name="Test Customer",
        )

        result = serialize_customer(customer, mask_pii=False)

        # PII should NOT be masked
        assert result["email"] == "test@example.com"
        assert result["phone"] == "+56912345678"

    def test_serialize_customer_anonymous_user(self):
        """Verify that anonymous users are handled correctly."""
        from pronto_shared.models import Customer

        customer = Customer(
            id="cust_123",
            email="anonimo+random@empresa.com",
            phone="+56912345678",
            name="Test Customer",
        )

        result = serialize_customer(customer)

        # Email should be None for anonymous users
        assert result["email"] is None
        # Phone should still be masked
        assert result["phone"] == "+569******78"

    def test_serialize_customer_none(self):
        """Verify that None customer returns None."""
        result = serialize_customer(None)
        assert result is None

    def test_serialize_customer_missing_phone(self):
        """Verify that customers without phone work correctly."""
        from pronto_shared.models import Customer

        customer = Customer(
            id="cust_123", email="test@example.com", phone=None, name="Test Customer"
        )

        result = serialize_customer(customer)

        # Email should be masked
        assert result["email"] == "t***@example.com"
        # Phone should be None
        assert result["phone"] is None


class TestSerializeOrder:
    """Test serialize_order function."""

    def test_serialize_order_masks_customer_pii(self):
        """Verify that serialize_order masks customer PII."""
        from pronto_shared.models import (
            Customer,
            Order,
            OrderItem,
            MenuItem,
            DiningSession,
            Employee,
        )

        # Create test data
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            phone="+56912345678",
            name="Test Customer",
        )

        session = DiningSession(
            id="session_123", table_number=1, status="open", customer=customer
        )

        employee = Employee(
            id="emp_123", name="Test Employee", email="emp@example.com", role="waiter"
        )

        order = Order(
            id="order_123",
            session=session,
            waiter=employee,
            workflow_status="pending",
            payment_status="unpaid",
            subtotal=100.0,
            tax_amount=16.0,
            tip_amount=10.0,
            total_amount=126.0,
        )

        from pronto_shared.serializers import serialize_order

        result = serialize_order(order)

        # Verify customer PII is masked
        assert result["customer"]["email"] == "t***@example.com"
        assert result["customer"]["phone"] == "+569******78"


class TestSerializeDiningSession:
    """Test serialize_dining_session function."""

    def test_serialize_dining_session_masks_customer_pii(self):
        """Verify that serialize_dining_session masks customer PII."""
        from pronto_shared.models import Customer, DiningSession

        # Create test data
        customer = Customer(
            id="cust_123",
            email="test@example.com",
            phone="+56912345678",
            name="Test Customer",
        )

        session = DiningSession(
            id="session_123", table_number=1, status="open", customer=customer
        )

        from pronto_shared.serializers import serialize_dining_session

        result = serialize_dining_session(session)

        # Verify customer PII is masked
        assert result["customer"]["email"] == "t***@example.com"
        assert result["customer"]["phone"] == "+569******78"

    def test_dining_session_email_encrypted(self):
        """Verify that DiningSession encrypts and decrypts email correctly."""
        from pronto_shared.models import DiningSession

        session = DiningSession(
            id="session_123", table_number=1, status="open", customer_id=1
        )

        # Set email - should encrypt automatically
        session.email = "test@example.com"

        # Verify encrypted value is set
        assert session.email_encrypted is not None
        assert session.email_hash is not None

        # Verify email_hash is SHA256 format (64 hex chars)
        assert len(session.email_hash) == 64

        # Verify email can be decrypted
        decrypted = session.email
        assert decrypted == "test@example.com"

        # Verify original email is not stored in plaintext
        assert (
            "test@example.com" not in str(session.__dict__)
            or session.email_encrypted == "test@example.com"
        )

    def test_dining_session_email_none(self):
        """Verify that DiningSession handles None email correctly."""
        from pronto_shared.models import DiningSession

        session = DiningSession(
            id="session_123", table_number=1, status="open", customer_id=1
        )

        # Set email to None
        session.email = None

        # Verify encrypted value is None
        assert session.email_encrypted is None
        assert session.email_hash is None

        # Verify email property returns None
        assert session.email is None
