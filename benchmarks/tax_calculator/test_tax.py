"""Unit tests for tax calculation engine."""
import pytest
from models import CartItem, Order
from pricing import calculate_order_tax, calculate_grand_total


def test_standard_tax_under_threshold():
    items = [CartItem(sku="SKU-1", price=100.0, quantity=2)]
    order = Order(order_id="ORD-101", region="TIER_A", items=items)
    # 200 * 0.05 = 10.0
    assert calculate_order_tax(order) == 10.0
    assert calculate_grand_total(order) == 225.0


def test_luxury_tax_surcharge():
    """Fails initially: luxury surcharge of 0.03 must be added to TIER_B (0.08) -> 0.11."""
    items = [CartItem(sku="LUX-01", price=1200.0, quantity=1)]
    order = Order(order_id="ORD-999", region="TIER_B", items=items)
    # Expected: 1200 * (0.08 + 0.03) = 1200 * 0.11 = 132.00
    # Bug produces 1200 * (0.08 - 0.03) = 60.00
    tax = calculate_order_tax(order)
    assert tax == 132.00
