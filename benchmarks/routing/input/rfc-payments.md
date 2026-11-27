# RFC 14: Retrying failed card charges

Today a failed charge fails the checkout. Proposal:

1. A charge that fails with a retryable error (timeout, 5xx, rate limit) is put on the queue with a delay of 60 s.
2. The worker retries up to 5 times with backoff 10 s, 20 s, 40 s, 80 s, 160 s, always with the same idempotency key,
   so the provider never charges twice.
3. A non-retryable error (card declined, insufficient funds, fraud) fails at once and the customer is asked for another card.
4. After the 5th failure the job goes to the dead-letter queue, the order is set to `payment_failed`, and support is paged
   if the amount is above 200 EUR.
5. While a retry is pending, the customer sees "We're confirming your payment" and gets an email when it settles.

Out of scope: partial captures, 3-D Secure challenges (handled by the provider's page).
