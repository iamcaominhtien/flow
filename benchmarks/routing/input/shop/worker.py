"""Background jobs, pulled from the Redis queue."""

import email_client
import payments
import queue_client
import store
import warehouse

MAX_ATTEMPTS = 5


def run_forever():
    while True:
        job = queue_client.pop(timeout_s=30)
        if job is None:
            continue
        try:
            HANDLERS[job.kind](job.order_id)
        except Exception:
            if job.attempts + 1 >= MAX_ATTEMPTS:
                queue_client.dead_letter(job)
            else:
                queue_client.enqueue(
                    job.kind, job.order_id, delay_s=2**job.attempts * 10, attempts=job.attempts + 1
                )


def send_receipt(order_id):
    email_client.send(store.load_order(order_id).customer.email, "receipt", order_id)


def reserve_stock(order_id):
    warehouse.reserve(store.load_order(order_id).lines)


def retry_charge(order_id):
    order = store.load_order(order_id)
    payments.charge(order.customer, order.paid_cents, idempotency_key=f"order-{order.id}")


def refund(order_id):
    order = store.load_order(order_id)
    payments.refund(order.customer, order.paid_cents)


HANDLERS = {
    "send_receipt": send_receipt,
    "reserve_stock": reserve_stock,
    "retry_charge": retry_charge,
    "refund": refund,
}
