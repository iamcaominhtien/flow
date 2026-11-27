"""Data classes of the shop."""

from dataclasses import dataclass, field
from enum import Enum


class OrderState(Enum):
    NEW = "new"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class Customer:
    id: int
    email: str
    vip: bool = False


@dataclass
class Product:
    sku: str
    price_cents: int
    stock: int


@dataclass
class Line:
    product: Product
    quantity: int


@dataclass
class Order:
    id: int
    customer: Customer
    lines: list[Line] = field(default_factory=list)
    state: OrderState = OrderState.NEW
    coupon: str | None = None
    paid_cents: int = 0
