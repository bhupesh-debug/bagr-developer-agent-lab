"""Pricing and tax calculation engine."""
from config import REGIONAL_RATES, LUXURY_THRESHOLD, LUXURY_SURCHARGE
from models import Order


def get_base_tax_rate(region: str) -> float:
    """Returns regional base tax rate."""
    return REGIONAL_RATES.get(region.upper(), 0.05)


def calculate_order_tax(order: Order) -> float:
    """Calculates tax for an order including applicable regional rates and surcharges."""
    base_rate = get_base_tax_rate(order.region)
    subtotal = order.subtotal

    # Logic Bug: Subtracts surcharge instead of adding surcharge when exceeding luxury threshold
    if subtotal > LUXURY_THRESHOLD:
        effective_rate = base_rate - LUXURY_SURCHARGE
    else:
        effective_rate = base_rate

    return round(subtotal * effective_rate, 2)


def calculate_grand_total(order: Order) -> float:
    """Calculates final payable order total."""
    tax = calculate_order_tax(order)
    return round(order.subtotal + tax + order.shipping_fee, 2)
