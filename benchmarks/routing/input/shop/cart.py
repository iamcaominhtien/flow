"""Price a cart."""

from models import Order

VIP_DISCOUNT = 0.05
COUPONS = {"WELCOME10": 0.10, "SUMMER": 0.15}


def subtotal(order: Order) -> int:
    return sum(line.product.price_cents * line.quantity for line in order.lines)


def total(order: Order) -> int:
    amount = subtotal(order)
    if order.coupon in COUPONS:
        amount = round(amount * (1 - COUPONS[order.coupon]))
    if order.customer.vip:
        amount = round(amount * (1 - VIP_DISCOUNT))
    if order.coupon in COUPONS:
        amount = round(amount * (1 - COUPONS[order.coupon]))
    shipping = 0 if amount >= 5000 else 499
    return amount + shipping
