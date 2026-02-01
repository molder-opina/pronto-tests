"""
Integration tests for menu recommendations API endpoints.
"""
from __future__ import annotations

import json

import pytest


@pytest.mark.integration
class TestRecommendationsAPI:
    """Tests for recommendations endpoints."""

    def test_get_recommendations_success(self, employee_client, _authenticated_session):
        """Test retrieving recommendations list."""
        response = employee_client.get("/api/menu-items/recommendations")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "categories" in data["data"]
        assert isinstance(data["data"]["categories"], list)

    def test_get_recommendations_returns_products(
        self, employee_client, _authenticated_session, _sample_menu_items
    ):
        """Test that recommendations endpoint returns products with recommendation flags."""
        response = employee_client.get("/api/menu-items/recommendations")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify structure
        categories = data["data"]["categories"]
        if len(categories) > 0:
            category = categories[0]
            assert "id" in category
            assert "name" in category
            assert "items" in category

            if len(category["items"]) > 0:
                item = category["items"][0]
                assert "id" in item
                assert "name" in item
                assert "price" in item
                assert "recommendation_periods" in item
                assert isinstance(item["recommendation_periods"], list)

    def test_update_recommendation_add(
        self, employee_client, _authenticated_session, sample_menu_item
    ):
        """Test adding a product to recommendations."""
        item_id = sample_menu_item.id

        response = employee_client.patch(
            f"/api/menu-items/{item_id}/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": True}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "breakfast" in data["data"]["item"]["recommendation_periods"]

    def test_update_recommendation_remove(
        self, employee_client, _authenticated_session, sample_menu_item
    ):
        """Test removing a product from recommendations."""
        item_id = sample_menu_item.id

        # First add it
        employee_client.patch(
            f"/api/menu-items/{item_id}/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": True}),
            content_type="application/json",
        )

        # Then remove it
        response = employee_client.patch(
            f"/api/menu-items/{item_id}/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": False}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "breakfast" not in data["data"]["item"]["recommendation_periods"]

    def test_update_recommendation_invalid_item(self, employee_client, _authenticated_session):
        """Test updating recommendations for non-existent item."""
        response = employee_client.patch(
            "/api/menu-items/99999/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": True}),
            content_type="application/json",
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_update_recommendation_requires_auth(self, employee_client):
        """Test that updating recommendations requires authentication."""
        response = employee_client.patch(
            "/api/menu-items/1/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": True}),
            content_type="application/json",
        )

        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_recommendations_flow(self, employee_client, _authenticated_session, sample_menu_item):
        """
        Integration test for the complete flow:
        1. Get recommendations list (should be empty)
        2. Add product to recommendations
        3. Get recommendations list (should contain product)
        4. Remove product from recommendations
        5. Get recommendations list (should be empty again)
        """
        item_id = sample_menu_item.id

        # Step 1: Get initial recommendations
        response = employee_client.get("/api/menu-items/recommendations")
        assert response.status_code == 200
        json.loads(response.data)

        # Step 2: Add product to breakfast recommendations
        response = employee_client.patch(
            f"/api/menu-items/{item_id}/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": True}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Step 3: Verify product appears in recommendations
        response = employee_client.get("/api/menu-items/recommendations")
        assert response.status_code == 200
        data = json.loads(response.data)

        # Find the item in the response
        found = False
        for category in data["data"]["categories"]:
            for item in category["items"]:
                if item["id"] == item_id:
                    assert "breakfast" in item["recommendation_periods"]
                    found = True
                    break
            if found:
                break
        assert found, "Product should be in recommendations after adding"

        # Step 4: Remove product from recommendations
        response = employee_client.patch(
            f"/api/menu-items/{item_id}/recommendations",
            data=json.dumps({"period_key": "breakfast", "enabled": False}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Step 5: Verify product no longer in breakfast recommendations
        response = employee_client.get("/api/menu-items/recommendations")
        assert response.status_code == 200
        data = json.loads(response.data)

        for category in data["data"]["categories"]:
            for item in category["items"]:
                if item["id"] == item_id:
                    assert "breakfast" not in item["recommendation_periods"]
