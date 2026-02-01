"""
Tests for menu service validation.
Tests product creation, update, and deletion with comprehensive validation.
"""

from decimal import Decimal, InvalidOperation
from http import HTTPStatus

import pytest

from shared.db import get_session
from shared.models import MenuItem
from shared.services.menu_service import create_menu_item, delete_menu_item, update_menu_item
from shared.services.menu_validation import MenuValidationError, MenuValidator


class TestMenuValidator:
    """Test the MenuValidator class directly."""

    def test_validate_create_required_fields(self):
        """Test validation fails when required fields are missing."""
        validator = MenuValidator()

        # Missing all required fields
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({})

        assert "obligatorio" in str(exc.value)

        # Missing name
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"price": 10.99, "category": "Main"})

        assert "name" in str(exc.value).lower()

    def test_validate_name(self):
        """Test name validation."""
        validator = MenuValidator()

        # Empty name
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "", "price": 10.99, "category": "Main"})

        assert "vacío" in str(exc.value).lower()

        # Name with only spaces
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "   ", "price": 10.99, "category": "Main"})

        assert "vacío" in str(exc.value).lower()

        # Name too short
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "A", "price": 10.99, "category": "Main"})

        assert "2 caracteres" in str(exc.value)

        # Name too long
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "A" * 101, "price": 10.99, "category": "Main"})

        assert "100 caracteres" in str(exc.value)

        # Valid name
        try:
            validator.validate_create(
                {"name": "Hamburguesa Doble", "price": 10.99, "category": "Main"}
            )
        except MenuValidationError:
            pytest.fail("Valid name should not raise exception")

    def test_validate_price(self):
        """Test price validation."""
        validator = MenuValidator()

        # Price is zero
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "Test", "price": 0, "category": "Main"})

        assert "mayor a" in str(exc.value)

        # Price is negative
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "Test", "price": -10.99, "category": "Main"})

        assert "mayor a" in str(exc.value)

        # Price too many decimals
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "Test", "price": 10.999, "category": "Main"})

        assert "decimales" in str(exc.value)

        # Price too large
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "Test", "price": 1000000, "category": "Main"})

        assert "no puede exceder" in str(exc.value)

        # Invalid price type
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create({"name": "Test", "price": "invalid", "category": "Main"})

        assert "número válido" in str(exc.value)

        # Valid price
        try:
            validator.validate_create({"name": "Test", "price": 10.99, "category": "Main"})
        except MenuValidationError:
            pytest.fail("Valid price should not raise exception")

    def test_validate_preparation_time(self):
        """Test preparation time validation."""
        validator = MenuValidator()

        # Preparation time negative
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "preparation_time_minutes": -5}
            )

        assert "negativo" in str(exc.value)

        # Preparation time too large
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create(
                {
                    "name": "Test",
                    "price": 10.99,
                    "category": "Main",
                    "preparation_time_minutes": 500,
                }
            )

        assert "300 minutos" in str(exc.value)

        # Invalid preparation time
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create(
                {
                    "name": "Test",
                    "price": 10.99,
                    "category": "Main",
                    "preparation_time_minutes": "invalid",
                }
            )

        assert "número entero válido" in str(exc.value)

        # Valid preparation time
        try:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "preparation_time_minutes": 15}
            )
        except MenuValidationError:
            pytest.fail("Valid preparation time should not raise exception")

    def test_validate_description(self):
        """Test description validation."""
        validator = MenuValidator()

        # Description too long
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "description": "A" * 501}
            )

        assert "500 caracteres" in str(exc.value)

        # Valid description (empty is allowed)
        try:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "description": ""}
            )
        except MenuValidationError:
            pytest.fail("Empty description should not raise exception")

        # Valid description (normal)
        try:
            validator.validate_create(
                {
                    "name": "Test",
                    "price": 10.99,
                    "category": "Main",
                    "description": "Deliciosa hamburguesa con queso",
                }
            )
        except MenuValidationError:
            pytest.fail("Valid description should not raise exception")

    def test_validate_image_path(self):
        """Test image path validation."""
        validator = MenuValidator()

        # Image path too long
        with pytest.raises(MenuValidationError) as exc:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "image_path": "A" * 256}
            )

        assert "255 caracteres" in str(exc.value)

        # Valid image path (empty is allowed)
        try:
            validator.validate_create(
                {"name": "Test", "price": 10.99, "category": "Main", "image_path": ""}
            )
        except MenuValidationError:
            pytest.fail("Empty image path should not raise exception")

        # Valid image path (normal)
        try:
            validator.validate_create(
                {
                    "name": "Test",
                    "price": 10.99,
                    "category": "Main",
                    "image_path": "/assets/menu/hamburguesa.jpg",
                }
            )
        except MenuValidationError:
            pytest.fail("Valid image path should not raise exception")


class TestMenuServiceCreate:
    """Test menu item creation with validation."""

    def test_create_menu_item_success(self):
        """Test successful menu item creation."""
        payload = {
            "name": "Hamburguesa Doble",
            "price": 12.99,
            "category": "Principal",
            "description": "Deliciosa hamburguesa doble con queso",
            "preparation_time_minutes": 20,
            "is_available": True,
            "is_quick_serve": False,
        }

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.CREATED
        assert "id" in result
        assert result["name"] == "Hamburguesa Doble"
        assert result["price"] == 12.99

    def test_create_menu_item_missing_required_field(self):
        """Test creation fails with missing required field."""
        payload = {
            "name": "Hamburguesa Doble",
            # Missing price
            "category": "Principal",
        }

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result
        assert "obligatorio" in result["error"].lower()

    def test_create_menu_item_invalid_price(self):
        """Test creation fails with invalid price."""
        payload = {"name": "Hamburguesa Doble", "price": -5.99, "category": "Principal"}

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result

    def test_create_menu_item_invalid_price_type(self):
        """Test creation fails with invalid price type."""
        payload = {"name": "Hamburguesa Doble", "price": "invalid", "category": "Principal"}

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result

    def test_create_menu_item_name_too_short(self):
        """Test creation fails with name too short."""
        payload = {"name": "A", "price": 10.99, "category": "Principal"}

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result

    def test_create_menu_item_name_too_long(self):
        """Test creation fails with name too long."""
        payload = {"name": "A" * 101, "price": 10.99, "category": "Principal"}

        result, status = create_menu_item(payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result


class TestMenuServiceUpdate:
    """Test menu item update with validation."""

    def test_update_menu_item_success(self):
        """Test successful menu item update."""
        # First create an item
        create_result, create_status = create_menu_item(
            {"name": "Original Name", "price": 10.00, "category": "Principal"}
        )
        assert create_status == HTTPStatus.CREATED

        item_id = create_result["id"]

        # Now update it
        payload = {"name": "Updated Name", "price": 15.99, "description": "Updated description"}

        result, status = update_menu_item(item_id, payload)

        assert status == HTTPStatus.OK
        assert result["id"] == item_id
        assert result["name"] == "Updated Name"
        assert result["price"] == 15.99

    def test_update_menu_item_not_found(self):
        """Test update fails with non-existent item."""
        payload = {"name": "Updated Name", "price": 15.99}

        result, status = update_menu_item(99999, payload)

        assert status == HTTPStatus.NOT_FOUND
        assert "error" in result
        assert "no encontrado" in result["error"].lower()

    def test_update_menu_item_invalid_price(self):
        """Test update fails with invalid price."""
        # First create an item
        create_result, create_status = create_menu_item(
            {"name": "Test Item", "price": 10.00, "category": "Principal"}
        )
        assert create_status == HTTPStatus.CREATED

        item_id = create_result["id"]

        # Try to update with invalid price
        payload = {"price": -5.99}

        result, status = update_menu_item(item_id, payload)

        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in result


class TestMenuServiceDelete:
    """Test menu item deletion with validation."""

    def test_delete_menu_item_success(self):
        """Test successful menu item deletion."""
        # First create an item
        create_result, create_status = create_menu_item(
            {"name": "To Delete", "price": 10.00, "category": "Principal"}
        )
        assert create_status == HTTPStatus.CREATED

        item_id = create_result["id"]

        # Now delete it
        result, status = delete_menu_item(item_id)

        assert status == HTTPStatus.OK
        assert result["deleted"] == item_id

    def test_delete_menu_item_not_found(self):
        """Test deletion fails with non-existent item."""
        result, status = delete_menu_item(99999)

        assert status == HTTPStatus.NOT_FOUND
        assert "error" in result
        assert "no encontrado" in result["error"].lower()

    def test_delete_menu_item_with_orders(self, db_session):
        """Test deletion fails when item has associated orders."""
        from shared.db import get_session
        from shared.models import OrderItem

        # Create a menu item
        with get_session() as session:
            item = MenuItem(name="Test Item", price=Decimal("10.00"), is_available=True)
            session.add(item)
            session.flush()
            item_id = item.id

            # Create a fake order item reference
            order_item = OrderItem(
                menu_item_id=item_id,
                quantity=1,
                unit_price=Decimal("10.00"),
                total_price=Decimal("10.00"),
            )
            session.add(order_item)
            session.commit()

        # Try to delete the item
        result, status = delete_menu_item(item_id)

        assert status == HTTPStatus.CONFLICT
        assert "error" in result
        assert "órdenes asociadas" in result["error"].lower()
