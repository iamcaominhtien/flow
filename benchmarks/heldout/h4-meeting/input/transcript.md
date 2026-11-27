# Ops sync, refunds over the limit (transcript, lightly edited)

Attendees: Mai (support lead), Duc (finance), Linh (risk), Tom (engineering)

Mai: So the problem is refunds above 200 euros. Today agents just ping Duc on chat and things get lost. Can we agree how it should go?

Duc: Sure. Under 200 the agent refunds directly in the admin tool, that stays as it is. Above 200 the agent opens a refund request in the tool instead, with the order number and the reason.

Linh: Before finance sees it, risk wants a look if the customer had more than two refunds in the last ninety days. The tool can flag that automatically, Tom?

Tom: Yes, the tool can count refunds per customer and set a "repeat" flag on the request.

Linh: Then flagged requests come to my queue first. I either clear them, and they go on to finance, or I reject them. If I reject, the agent has to tell the customer, and we add a note on the account.

Mai: And unflagged ones go straight to finance?

Duc: Yes. Finance approves or rejects. Approved ones, I issue the refund from the payment provider, not from the admin tool, because the admin tool caps at 200. Then the tool marks the request done and the agent gets a notification to close the ticket.

Mai: What if finance rejects?

Duc: Same as risk: the agent tells the customer. No account note in that case, it's a business decision, not abuse.

Tom: One more thing: the payment provider sometimes fails, a timeout or a closed card. Then finance retries once the next day; if it fails again, we offer store credit instead and the agent tells the customer.

Mai: And how long should all this take?

Duc: Finance looks at the queue every morning, so a day or two.

Linh: Risk the same day, usually.

Mai: Good. I'll write it up for the agents.
