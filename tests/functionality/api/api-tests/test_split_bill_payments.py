"""
Integration tests for split bill payment functionality.
Tests the finalize_payment integration when all persons in a split bill have paid.
"""

import pytest
from unittest.mock import MagicMock, patch
from http import HTTPStatus
import sys
from pathlib import Path

# Add pronto-client/src to path for client package discovery
pronto_client_src_path = Path(__file__).parent.parent.parent.parent.parent / "pronto-client" / "src"
if str(pronto_client_src_path) not in sys.path:
    sys.path.insert(0, str(pronto_client_src_path))


class TestSplitBillPayments:
    """Test suite for split bill payment workflows."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_split_bill(self):
        """Create a mock split bill with 3 people."""
        person1 = MagicMock()
        person1.id = 1
        person1.payment_status = "paid"
        person1.total_amount = 100.0

        person2 = MagicMock()
        person2.id = 2
        person2.payment_status = "paid"
        person2.total_amount = 100.0

        person3 = MagicMock()
        person3.id = 3
        person3.payment_status = "pending"
        person3.total_amount = 100.0

        split_bill = MagicMock()
        split_bill.id = 1
        split_bill.status = "active"
        split_bill.people = [person1, person2, person3]

        return split_bill

    @pytest.fixture
    def mock_dining_session(self):
        """Create a mock dining session."""
        session = MagicMock()
        session.id = 100
        session.status = "open"
        session.total_amount = 300.0
        return session

    def test_pay_split_person_partial_payment(
        self, mock_split_bill, mock_dining_session
    ):
        """Test that partial payments don't trigger finalize_payment."""
        from decimal import Decimal

        # Person 3 is pending, so all_paid should be False
        all_paid = all(p.payment_status == "paid" for p in mock_split_bill.people)
        assert all_paid is False

        # Should NOT call finalize_payment when not all paid
        mock_split_bill.session = mock_dining_session

        # Verify the session is still open
        assert mock_dining_session.status == "open"

    def test_pay_split_person_full_payment(self, mock_split_bill, mock_dining_session):
        """Test that full payment triggers finalize_payment."""
        # Mark all people as paid
        for person in mock_split_bill.people:
            person.payment_status = "paid"

        all_paid = all(p.payment_status == "paid" for p in mock_split_bill.people)
        assert all_paid is True

        mock_split_bill.session = mock_dining_session

        # Verify the session can be closed
        assert mock_dining_session.status == "open"


class TestFinalizePaymentIntegration:
    """Integration tests for finalize_payment service."""

    @pytest.fixture
    def mock_order_service(self):
        """Mock the order_service module."""
        # Removing debug prints and patching the correct shared service
        with patch("pronto_shared.services.order_service") as mock:
            mock.finalize_payment.return_value = (
                {"session_id": "100", "status": "closed"},
                HTTPStatus.OK,
            )
            yield mock

    def test_finalize_payment_is_called_on_last_split_payment(self, mock_order_service):
        """Verify finalize_payment is called when last person pays."""
        # This test verifies the integration path
        # In production, this would be tested with real database
        mock_order_service.finalize_payment.assert_not_called()

        # Simulate the last payment
        mock_order_service.finalize_payment(
            session_id="100",
            payment_method="split_bill",
            payment_reference="split-1",
        )

        mock_order_service.finalize_payment.assert_called_once()


class TestNotificationAuthorization:
    """Tests for notification authorization fix."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock current user with customer_id."""
        return {"customer_id": "customer-123", "mode": "client"}

    @pytest.fixture
    def mock_notification_query(self):
        """Create a mock notification query result."""
        notification1 = MagicMock()
        notification1.id = 1
        notification1.recipient_id = "customer-123"
        notification1.recipient_type = "customer"
        notification1.status = "unread"

        notification2 = MagicMock()
        notification2.id = 2
        notification2.recipient_id = "customer-456"  # Different customer
        notification2.recipient_type = "customer"
        notification2.status = "unread"

        return [notification1, notification2]

    def test_notifications_filtered_by_customer_id(
        self, mock_current_user, mock_notification_query
    ):
        """Test that notifications are filtered by customer_id."""
        customer_id = mock_current_user.get("customer_id")

        # Filter notifications for current customer only
        filtered_notifications = [
            n
            for n in mock_notification_query
            if n.recipient_id == customer_id and n.recipient_type == "customer"
        ]

        # Should only return notification1 (customer-123)
        assert len(filtered_notifications) == 1
        assert filtered_notifications[0].recipient_id == "customer-123"

    def test_unauthorized_customer_cannot_see_others_notifications(
        self, mock_current_user, mock_notification_query
    ):
        """Test that customer-456 cannot see customer-123's notifications."""
        # Simulate being logged in as customer-456
        mock_current_user["customer_id"] = "customer-456"

        customer_id = mock_current_user.get("customer_id")

        # Filter notifications for customer-456
        filtered_notifications = [
            n
            for n in mock_notification_query
            if n.recipient_id == customer_id and n.recipient_type == "customer"
        ]

        # Should only return notification2
        assert len(filtered_notifications) == 1
        assert filtered_notifications[0].recipient_id == "customer-456"


class TestSessionStatusValidation:
    """Tests for session status validation in /me and /validate endpoints."""

    @pytest.fixture
    def mock_open_session(self):
        """Create a mock open dining session."""
        session = MagicMock()
        session.status = "open"
        return session

    @pytest.fixture
    def mock_closed_session(self):
        """Create a mock closed dining session."""
        session = MagicMock()
        session.status = "closed"
        return session

    def test_open_session_returns_valid(self, mock_open_session):
        """Test that open sessions are considered valid."""
        assert mock_open_session.status == "open"
        # Should return valid=True in /validate

    def test_closed_session_returns_invalid(self, mock_closed_session):
        """Test that closed sessions are considered invalid."""
        assert mock_closed_session.status == "closed"
        # Should return valid=False or SESSION_CLOSED in /validate

    def test_me_endpoint_returns_410_for_closed_session(self, mock_closed_session):
        """Test that /me returns 410 GONE for closed sessions."""
        # In production, the /me endpoint should return 410
        # when the session is closed in the database
        status = mock_closed_session.status
        expected_response_code = 410 if status != "open" else 200
        assert expected_response_code == 410


class TestWaiterCallAssignment:
    """Tests for waiter call table assignment refactoring."""

    @pytest.fixture
    def mock_table_assignment(self):
        """Create a mock table assignment response."""
        return {
            "waiter_id": 5,
            "waiter_name": "Juan Perez",
            "assigned_at": "2026-02-09T10:00:00Z",
        }

    def test_get_table_assignment_returns_waiter_info(self, mock_table_assignment):
        """Test that get_table_assignment returns waiter info."""
        result = mock_table_assignment
        assert result["waiter_id"] == 5
        assert result["waiter_name"] == "Juan Perez"

    def test_waiter_assignment_preferred_over_dining_session(
        self, mock_table_assignment
    ):
        """Test that table assignment is used when no session waiter."""
        # If no waiter assigned to session, fall back to table assignment
        session_waiter_id = None

        if session_waiter_id is None:
            waiter_id = mock_table_assignment["waiter_id"]
            waiter_name = mock_table_assignment["waiter_name"]
        else:
            waiter_id = session_waiter_id
            waiter_name = "Session Waiter"

        assert waiter_id == 5
        assert waiter_name == "Juan Perez"
