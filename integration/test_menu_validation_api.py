"""
Integration tests for menu API validation.
Tests create, update, and delete operations with comprehensive validation.
"""

from decimal import Decimal
from http import HTTPStatus

import pytest


class TestMenuCreateValidation:
    """Tests for menu item creation validation."""

    def test_create_missing_required_fields(self, admin_token, client):
        """Test creating product without required fields."""
        response = client.post(
            "/api/menu-items", json={}, headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "obligatorio" in data["error"].lower()

    def test_create_missing_name(self, admin_token, client):
        """Test creating product without name."""
        response = client.post(
            "/api/menu-items",
            json={"price": 9.99, "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "nombre" in data["error"].lower()

    def test_create_missing_price(self, admin_token, client):
        """Test creating product without price."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa", "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "precio" in data["error"].lower()

    def test_create_missing_category(self, admin_token, client):
        """Test creating product without category."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa", "price": 9.99},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "categor" in data["error"].lower()

    def test_create_name_too_short(self, admin_token, client):
        """Test creating product with name too short."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "H",  # Only 1 character (minimum is 2)
                "price": 9.99,
                "category": "Main Dishes",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "caracteres" in data["error"]

    def test_create_name_too_long(self, admin_token, client):
        """Test creating product with name too long."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "A" * 101,  # 101 characters (maximum is 100)
                "price": 9.99,
                "category": "Main Dishes",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "exceder" in data["error"]
        assert "100" in data["error"]

    def test_create_name_empty(self, admin_token, client):
        """Test creating product with empty name."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "   ",  # Only spaces
                "price": 9.99,
                "category": "Main Dishes",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "vac" in data["error"]

    def test_create_name_xss_attempt(self, admin_token, client):
        """Test creating product with XSS attempt in name."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "<script>alert('xss')</script>",
                "price": 9.99,
                "category": "Main Dishes",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_create_price_negative(self, admin_token, client):
        """Test creating product with negative price."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa", "price": -9.99, "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "precio" in data["error"].lower()

    def test_create_price_zero(self, admin_token, client):
        """Test creating product with zero price."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa", "price": 0, "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "precio" in data["error"].lower()

    def test_create_price_invalid_string(self, admin_token, client):
        """Test creating product with invalid price string."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa", "price": "not a number", "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "precio" in data["error"].lower()

    def test_create_price_too_many_decimals(self, admin_token, client):
        """Test creating product with too many decimal places."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa",
                "price": 9.999,  # More than 2 decimal places
                "category": "Main Dishes",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_create_price_too_high(self, admin_token, client):
        """Test creating product with price too high (> 100,000)."""
        response = client.post(
            "/api/menu-items",
            json={"name": "Hamburguesa Premium", "price": 100001.00, "category": "Main Dishes"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "exceder" in data["error"]

    def test_create_description_too_long(self, admin_token, client):
        """Test creating product with description too long."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa",
                "price": 9.99,
                "category": "Main Dishes",
                "description": "A" * 501,  # 501 characters (maximum is 500)
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "descripcin" in data["error"].lower()

    def test_create_description_xss_attempt(self, admin_token, client):
        """Test creating product with XSS attempt in description."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa",
                "price": 9.99,
                "category": "Main Dishes",
                "description": "<script>alert('xss')</script>",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_create_preparation_time_negative(self, admin_token, client):
        """Test creating product with negative preparation time."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa",
                "price": 9.99,
                "category": "Main Dishes",
                "preparation_time_minutes": -10,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "preparacin" in data["error"].lower()

    def test_create_preparation_time_too_high(self, admin_token, client):
        """Test creating product with preparation time too high (> 300 min)."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa Lenta",
                "price": 9.99,
                "category": "Main Dishes",
                "preparation_time_minutes": 301,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "exceder" in data["error"]

    def test_create_category_too_long(self, admin_token, client):
        """Test creating product with category too long."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa",
                "price": 9.99,
                "category": "A" * 101,  # 101 characters (maximum is 100)
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "categor" in data["error"].lower()

    def test_create_valid_product(self, admin_token, client):
        """Test creating a valid product."""
        response = client.post(
            "/api/menu-items",
            json={
                "name": "Hamburguesa de Prueba",
                "price": 9.99,
                "category": "Main Dishes",
                "description": "Deliciosa hamburguesa de prueba",
                "preparation_time_minutes": 15,
                "is_available": True,
                "is_quick_serve": False,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == "Hamburguesa de Prueba"
        assert data["price"] == 9.99


class TestMenuUpdateValidation:
    """Tests for menu item update validation."""

    def test_update_nonexistent_product(self, admin_token, client):
        """Test updating a product that doesn't exist."""
        response = client.put(
            "/api/menu-items/999999",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        data = response.json()
        assert "error" in data
        assert "encontrado" in data["error"]

    def test_update_name_too_short(self, admin_token, client, sample_menu_item):
        """Test updating product with name too short."""
        response = client.put(
            f"/api/menu-items/{sample_menu_item.id}",
            json={"name": "H"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_update_price_negative(self, admin_token, client, sample_menu_item):
        """Test updating product with negative price."""
        response = client.put(
            f"/api/menu-items/{sample_menu_item.id}",
            json={"price": -9.99},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_update_preparation_time_invalid(self, admin_token, client, sample_menu_item):
        """Test updating product with invalid preparation time."""
        response = client.put(
            f"/api/menu-items/{sample_menu_item.id}",
            json={"preparation_time_minutes": "not a number"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        data = response.json()
        assert "error" in data

    def test_update_valid_changes(self, admin_token, client, sample_menu_item):
        """Test updating a product with valid changes."""
        response = client.put(
            f"/api/menu-items/{sample_menu_item.id}",
            json={
                "name": "Hamburguesa Actualizada",
                "price": 12.99,
                "description": "Descripción actualizada",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "id" in data
        assert data["name"] == "Hamburguesa Actualizada"
        assert data["price"] == 12.99


class TestMenuDeleteValidation:
    """Tests for menu item deletion validation."""

    def test_delete_nonexistent_product(self, admin_token, client):
        """Test deleting a product that doesn't exist."""
        response = client.delete(
            "/api/menu-items/999999", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        data = response.json()
        assert "error" in data
        assert "encontrado" in data["error"]

    def test_delete_product_with_orders(self, admin_token, client, sample_menu_item_with_orders):
        """Test deleting a product that has associated orders."""
        # Create an order with the menu item first
        # Note: This test requires the order creation flow to be tested separately

        response = client.delete(
            f"/api/menu-items/{sample_menu_item_with_orders.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        data = response.json()
        assert "error" in data
        assert "rdenes" in data["error"]

    def test_delete_valid_product(self, admin_token, client, sample_menu_item):
        """Test deleting a valid product without orders."""
        response = client.delete(
            f"/api/menu-items/{sample_menu_item.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "deleted" in data


class TestMenuCRUDIntegration:
    """Integration tests for full menu CRUD workflow."""

    def test_full_crud_workflow(self, admin_token, client):
        """Test complete create, update, delete workflow."""
        # Create
        create_response = client.post(
            "/api/menu-items",
            json={"name": "Producto CRUD Test", "price": 15.99, "category": "Test Category"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        created_data = create_response.json()
        item_id = created_data["id"]

        # Update
        update_response = client.put(
            f"/api/menu-items/{item_id}",
            json={"name": "Producto CRUD Actualizado", "price": 19.99},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert update_response.status_code == HTTPStatus.OK
        updated_data = update_response.json()
        assert updated_data["name"] == "Producto CRUD Actualizado"
        assert updated_data["price"] == 19.99

        # Delete
        delete_response = client.delete(
            f"/api/menu-items/{item_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert delete_response.status_code == HTTPStatus.OK
        delete_data = delete_response.json()
        assert delete_data["deleted"] == item_id

        # Verify deletion
        get_response = client.get(
            f"/api/menu-items/{item_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Item should not be found after deletion
        assert get_response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST]
