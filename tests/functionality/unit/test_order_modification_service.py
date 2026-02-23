from unittest.mock import MagicMock, patch
from decimal import Decimal
import pytest
from pronto_shared.services.order_modification_service import (
    create_modification,
    approve_modification,
    reject_modification,
    can_customer_modify_order
)
from pronto_shared.constants import ModificationInitiator, ModificationStatus, OrderStatus
from pronto_shared.models import Order, MenuItem, OrderItem, OrderModification

class TestOrderModificationService:
    @pytest.fixture
    def mock_session(self):
        with patch("pronto_shared.services.order_modification_service.get_session") as mock:
            session = MagicMock()
            mock.return_value.__enter__.return_value = session
            yield session

    @pytest.fixture
    def mock_order(self):
        order = MagicMock()
        order.id = 1
        order.session_id = 100
        order.workflow_status = OrderStatus.NEW.value
        order.customer_id = 50
        order.items = []
        return order

    def test_can_customer_modify_order(self, mock_order):
        # NEW order -> Can modify
        assert can_customer_modify_order(mock_order) is True
        
        # QUEUED -> Cannot modify
        mock_order.workflow_status = OrderStatus.QUEUED.value
        assert can_customer_modify_order(mock_order) is False

    def test_create_modification_customer_success(self, mock_session, mock_order):
        def get_side_effect(model, id):
            if model == Order and id == 1: return mock_order
            if model == MenuItem and id == 10:
                item = MagicMock()
                item.is_available = True
                item.price = 10.0
                return item
            return None
        
        mock_session.get.side_effect = get_side_effect
        
        # Mock _apply_modification to return success
        with patch("pronto_shared.services.order_modification_service._apply_modification", return_value={"success": True}) as mock_apply:
            changes = {"items_to_add": [{"menu_item_id": 10, "quantity": 1}]}
            response, status = create_modification(
                order_id=1,
                changes_data=changes,
                initiated_by_role=ModificationInitiator.CUSTOMER.value,
                customer_id=50
            )

            assert status == 201  # CREATED
            assert response["data"]["status"] == ModificationStatus.APPLIED.value
            assert response["data"]["auto_applied"] is True
            mock_session.add.assert_called() # Modification added
            mock_apply.assert_called()

    def test_create_modification_waiter_pending(self, mock_session, mock_order):
        def get_side_effect(model, id):
            if model == Order and id == 1: return mock_order
            if model == OrderItem and id == 20:
                item = MagicMock()
                item.order_id = 1
                return item
            return None

        mock_session.get.side_effect = get_side_effect
        
        changes = {"items_to_remove": [20]}
        response, status = create_modification(
            order_id=1,
            changes_data=changes,
            initiated_by_role=ModificationInitiator.WAITER.value,
            employee_id=99
        )

        assert status == 200 # OK (Created pending)
        assert response["data"]["status"] == ModificationStatus.PENDING.value
        assert response["data"]["auto_applied"] is False
        mock_session.add.assert_called()

    def test_approve_modification_success(self, mock_session, mock_order):
        # Setup modification
        mod = MagicMock()
        mod.id = 999
        mod.order_id = 1
        mod.status = ModificationStatus.PENDING.value
        mod.initiated_by_role = ModificationInitiator.WAITER.value

        def get_side_effect(model, id):
            if model == OrderModification and id == 999: return mod
            if model == Order and id == 1: return mock_order
            return None
        
        mock_session.get.side_effect = get_side_effect

        with patch("pronto_shared.services.order_modification_service._apply_modification", return_value={"success": True}):
            response, status = approve_modification(modification_id=999, customer_id=50)
            
            assert status == 200
            assert response["data"]["status"] == "applied"
            assert mod.status == ModificationStatus.APPLIED.value
            assert mod.reviewed_by_customer_id == 50

    def test_approve_modification_forbidden(self, mock_session, mock_order):
        mod = MagicMock()
        mod.id = 999
        mod.order_id = 1
        mod.status = ModificationStatus.PENDING.value
        mod.initiated_by_role = ModificationInitiator.WAITER.value
        
        # Order belongs to customer 50, but approving as 51
        def get_side_effect(model, id):
            if model == OrderModification and id == 999: return mod
            if model == Order and id == 1: return mock_order
            return None

        mock_session.get.side_effect = get_side_effect

        response, status = approve_modification(modification_id=999, customer_id=51)
        
        assert status == 403
