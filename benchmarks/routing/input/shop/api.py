"""HTTP handlers."""

import cart
import payments
import queue_client
import store
from models import OrderState


def checkout(request):
    order = store.load_order(request["order_id"])
    if order.state is not OrderState.NEW:
        return {"status": 409, "error": "order is not open"}
    for line in order.lines:
        if line.product.stock < line.quantity:
            return {"status": 422, "error": f"{line.product.sku} out of stock"}
    amount = cart.total(order)
    charge = payments.charge(order.customer, amount, idempotency_key=f"order-{order.id}")
    if not charge.ok:
        if charge.retryable:
            queue_client.enqueue("retry_charge", order.id, delay_s=60)
            return {"status": 202, "pending": True}
        return {"status": 402, "error": charge.reason}
    order.paid_cents = amount
    order.state = OrderState.PAID
    store.save(order)
    queue_client.enqueue("send_receipt", order.id)
    queue_client.enqueue("reserve_stock", order.id)
    return {"status": 200, "order": order.id}


def cancel(request):
    order = store.load_order(request["order_id"])
    if order.state in (OrderState.NEW, OrderState.PAID):
        order.state = OrderState.CANCELLED
        store.save(order)
        if order.paid_cents:
            queue_client.enqueue("refund", order.id)
        return {"status": 200}
    return {"status": 409, "error": "too late to cancel"}
