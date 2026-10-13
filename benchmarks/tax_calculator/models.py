"""Order and item models."""
from dataclasses import dataclass
from typing import List


@dataclass
class CartItem:
    sku: str
    price: float
    quantity: int


@dataclass
class Order:
    order_id: str
    region: str
    items: List[CartItem]
    shipping_fee: float = 15.0

    @property
    def subtotal(self) -> float:
        return sum(item.price * item.quantity for item in self.items)
