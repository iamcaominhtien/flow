# shop

A small web shop. `api.py` takes HTTP requests, `cart.py` prices a cart, `models.py` holds the data
classes, `refunds.py` handles refunds and `worker.py` sends emails and syncs stock in the background.

Orders are stored in Postgres; jobs go through a Redis queue; card payments go to the payment provider.
