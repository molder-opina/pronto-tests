"""
Integration tests for Split Bill feature.
"""
import json
import pytest
from datetime import datetime, timezone
from pronto_shared.models import DiningSession, Customer, Table, Order, OrderItem, MenuItem
from pronto_shared.constants import SessionStatus, OrderStatus

@pytest.mark.integration
class TestSplitBill:
    """Tests for split bill API endpoints."""

    @pytest.fixture
    def active_session(self, db_session, sample_employee):
        """Create an active session with orders."""
        # Create a table
        table = Table(table_number="99", capacity=4, is_active=True, zone_id=1)
        db_session.add(table)
        db_session.flush()

        # Create session
        session = DiningSession(
            table_id=table.id,
            table_number=table.table_number,
            status=SessionStatus.OPEN.value,
            opened_at=datetime.now(timezone.utc),
            employee_id=sample_employee.id,
            total_amount=100.0,
            subtotal=90.0,
            tax_amount=10.0
        )
        db_session.add(session)
        db_session.flush()

        # Create an order
        menu_item = MenuItem(name="Pizza", price=100.0, active=True, category_id=1)
        db_session.add(menu_item)
        db_session.flush()

        order = Order(
            session_id=session.id,
            workflow_status=OrderStatus.DELIVERED.value,
            total_amount=100.0
        )
        db_session.add(order)
        db_session.flush()

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            price=100.0,
            quantity=1
        )
        db_session.add(order_item)
        db_session.commit()
        
        return session

    def test_split_bill_flow_equal(self, employee_client, sample_employee, active_session):
        """Test creating an equal split and paying it out."""
        # Login
        employee_client.post(
            "/api/auth/login",
            data=json.dumps({"email": sample_employee.email, "password": "Test123!"}),
            content_type="application/json",
        )

        # 1. Create Split
        resp = employee_client.post(
            f"/api/split-bills/sessions/{active_session.id}/create",
            data=json.dumps({"split_type": "equal", "number_of_people": 2}),
            content_type="application/json"
        )
        assert resp.status_code == 201, f"Error: {resp.data}"
        split_data = json.loads(resp.data)["data"]
        assert split_data["split_type"] == "equal"
        assert len(split_data["people"]) == 2
        
        people = split_data["people"]
        p1 = people[0]
        p2 = people[1]
        
        assert p1["total_amount"] == 50.0
        assert p2["total_amount"] == 50.0

        # 2. Pay Person 1
        resp = employee_client.post(
            f"/api/split-bills/people/{p1['id']}/pay",
            data=json.dumps({"payment_method": "cash"}),
            content_type="application/json"
        )
        assert resp.status_code == 200
        pay_data = json.loads(resp.data)["data"]
        assert pay_data["status"] == "paid"
        assert pay_data["split_completed"] == False

        # 3. Pay Person 2
        resp = employee_client.post(
            f"/api/split-bills/people/{p2['id']}/pay",
            data=json.dumps({"payment_method": "card"}),
            content_type="application/json"
        )
        assert resp.status_code == 200
        pay_data = json.loads(resp.data)["data"]
        assert pay_data["status"] == "paid"
        assert pay_data["split_completed"] == True

        # 4. Verify Session is Closed
        resp = employee_client.get(f"/api/sessions/{active_session.id}")
        assert resp.status_code == 200
        session_data = json.loads(resp.data)["data"]
        assert session_data["status"] == "paid"
