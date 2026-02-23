import pytest
from decimal import Decimal
from pronto_shared.services.price_service import calculate_price_breakdown

class TestPriceService:
    """Unit tests for price calculation logic."""

    def test_calculate_price_breakdown_tax_included(self):
        """
        Scenario: Item price includes tax.
        Price: 116.00
        Tax Rate: 0.16
        Expected:
            - Base: 100.00
            - Tax: 16.00
            - Final: 116.00
        """
        result = calculate_price_breakdown(
            display_price=Decimal("116.00"),
            tax_rate=Decimal("0.16"),
            mode="tax_included"
        )
        
        assert result["price_base"] == 100.00
        assert result["tax_amount"] == 16.00
        assert result["price_final"] == 116.00
        assert result["display_price"] == 116.00

    def test_calculate_price_breakdown_tax_excluded(self):
        """
        Scenario: Item price excludes tax.
        Price: 100.00
        Tax Rate: 0.16
        Expected:
            - Base: 100.00
            - Tax: 16.00
            - Final: 116.00
        """
        result = calculate_price_breakdown(
            display_price=Decimal("100.00"),
            tax_rate=Decimal("0.16"),
            mode="tax_excluded"
        )

        assert result["price_base"] == 100.00
        assert result["tax_amount"] == 16.00
        assert result["price_final"] == 116.00
        assert result["display_price"] == 100.00

    def test_calculate_price_breakdown_rounding(self):
        """
        Scenario: Rounding logic checks.
        Price: 10.00 (tax included)
        Tax Rate: 0.16
        Base = 10 / 1.16 = 8.62068... -> 8.62
        Tax = 10 - 8.62 = 1.38
        """
        result = calculate_price_breakdown(
            display_price=Decimal("10.00"),
            tax_rate=Decimal("0.16"),
            mode="tax_included"
        )

        assert result["price_base"] == 8.62
        assert result["tax_amount"] == 1.38
        assert result["price_final"] == 10.00

    def test_calculate_price_breakdown_tax_excluded_rounding(self):
        """
        Scenario: Rounding logic tax excluded.
        Price: 10.555 (should round input?) -> Python Decimal handles input precision, 
        but function uses input as is for calculation then quantizes.
        Let's test with a clean 2 decimal input that produces 3 decimal tax.
        Price: 10.11
        Tax Rate: 0.15
        Tax = 1.5165 -> 1.52 (ROUND_HALF_UP)
        Final = 11.63
        """
        result = calculate_price_breakdown(
            display_price=Decimal("10.11"),
            tax_rate=Decimal("0.15"),
            mode="tax_excluded"
        )

        assert result["price_base"] == 10.11
        assert result["tax_amount"] == 1.52
        assert result["price_final"] == 11.63
