"""Refunds."""

import datetime

import payments
import store
from models import OrderState

REFUND_WINDOW_DAYS = 30
MANUAL_REVIEW_CENTS = 20000


def request_refund(order_id: int, reason: str, today: datetime.date) -> str:
    order = store.load_order(order_id)
    if order.state not in (OrderState.DELIVERED, OrderState.CANCELLED):
        return "rejected: not delivered"
    if (today - store.delivered_on(order)).days > REFUND_WINDOW_DAYS:
        return "rejected: window passed"
    if order.paid_cents >= MANUAL_REVIEW_CENTS or reason == "damaged":
        store.add_review_task(order, reason)
        return "pending: manual review"
    refund = payments.refund(order.customer, order.paid_cents)
    if not refund.ok:
        store.add_review_task(order, "refund failed: " + refund.reason)
        return "pending: refund failed"
    order.state = OrderState.REFUNDED
    store.save(order)
    return "refunded"
