"""
Analytics API Tests - Product & Customer Reports

Tests for product and customer analytics endpoints:
- /api/reports/top-products
- /api/reports/category-performance
- /api/reports/customer-segments
"""

import pytest
from datetime import date, timedelta


class TestProductReports:
    """Test suite for product analytics reports."""

    @pytest.fixture
    def date_range(self):
        """Provide a standard date range for tests."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    def test_top_products_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/top-products endpoint."""
        response = authenticated_client.get(
            "/api/reports/top-products",
            query_string={**date_range, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "products" in data["data"]
        
        products = data["data"]["products"]
        assert isinstance(products, list)
        assert len(products) <= 10
        
        if products:
            product = products[0]
            assert "id" in product
            assert "name" in product
            assert "total_quantity" in product
            assert "order_count" in product
            assert "total_revenue" in product
            
            # Validate data types
            assert isinstance(product["total_quantity"], int)
            assert isinstance(product["order_count"], int)
            assert isinstance(product["total_revenue"], (int, float))

    def test_top_products_limit(self, authenticated_client, date_range):
        """Test top products with different limits."""
        limits = [5, 10, 20]
        
        for limit in limits:
            response = authenticated_client.get(
                "/api/reports/top-products",
                query_string={**date_range, "limit": limit}
            )
            
            assert response.status_code == 200
            data = response.json()
            products = data["data"]["products"]
            assert len(products) <= limit

    def test_category_performance_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/category-performance endpoint."""
        response = authenticated_client.get(
            "/api/reports/category-performance",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "categories" in data["data"]
        
        categories = data["data"]["categories"]
        assert isinstance(categories, list)
        
        if categories:
            category = categories[0]
            assert "category_id" in category
            assert "category_name" in category
            assert "total_quantity" in category
            assert "order_count" in category
            assert "total_revenue" in category
            assert "avg_item_price" in category
            assert "revenue_percentage" in category
            
            # Validate revenue percentage
            assert 0 <= category["revenue_percentage"] <= 100

    def test_category_revenue_percentages(self, authenticated_client, date_range):
        """Test that category revenue percentages sum to ~100%."""
        response = authenticated_client.get(
            "/api/reports/category-performance",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        categories = data["data"]["categories"]
        
        if categories:
            total_percentage = sum(c["revenue_percentage"] for c in categories)
            # Allow small floating point errors
            assert 99 <= total_percentage <= 101


class TestCustomerReports:
    """Test suite for customer analytics reports."""

    @pytest.fixture
    def date_range(self):
        """Provide a standard date range for tests."""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    def test_customer_segments_endpoint(self, authenticated_client, date_range):
        """Test /api/reports/customer-segments endpoint."""
        response = authenticated_client.get(
            "/api/reports/customer-segments",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "customers" in data["data"]
        
        customers = data["data"]["customers"]
        assert isinstance(customers, list)
        
        if customers:
            customer = customers[0]
            assert "customer_id" in customer
            assert "customer_name" in customer
            assert "customer_email" in customer
            assert "order_count" in customer
            assert "total_spent" in customer
            assert "avg_order_value" in customer
            assert "segment" in customer
            assert "frequency" in customer
            
            # Validate segment values
            assert customer["segment"] in ["high_value", "medium_value", "low_value"]
            assert customer["frequency"] in ["high", "medium", "low"]

    def test_customer_segmentation_logic(self, authenticated_client, date_range):
        """Test that customer segmentation logic is correct."""
        response = authenticated_client.get(
            "/api/reports/customer-segments",
            query_string=date_range
        )
        
        assert response.status_code == 200
        data = response.json()
        
        customers = data["data"]["customers"]
        
        for customer in customers:
            total_spent = customer["total_spent"]
            order_count = customer["order_count"]
            
            # Validate value segment
            if total_spent >= 1000:
                assert customer["segment"] == "high_value"
            elif total_spent >= 500:
                assert customer["segment"] == "medium_value"
            else:
                assert customer["segment"] == "low_value"
            
            # Validate frequency segment
            if order_count >= 10:
                assert customer["frequency"] == "high"
            elif order_count >= 5:
                assert customer["frequency"] == "medium"
            else:
                assert customer["frequency"] == "low"

    def test_product_customer_reports_without_auth(self, client, date_range):
        """Test that reports require authentication."""
        endpoints = [
            "/api/reports/top-products",
            "/api/reports/category-performance",
            "/api/reports/customer-segments"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, query_string=date_range)
            assert response.status_code == 401
