# Architecture blind test (ride-hailing)

1. Path: both. Quick path, 2 rounds. Round 1: exit 1 (unknown icon 'api'), then exit 2: 3 line-through-node errors (WebSocket Gateway to Kafka through Registry, Flink, DLQ), 107 warnings. Round 2 (Kafka moved last in its row): exit 0, 0 errors, 92 warnings (73 lines-cross, 19 crosses-many). Author attempt (one build, my make.py): 16 errors (14 line-through-node, 2 label-covers), 50 warnings (38 lines-cross, 9 crosses-many, 3 lines-overlap); not fixed, one attempt only.

2. Counts: the brief says 34 components; its lists add up to 38. Asked: 38 parts, 7 zones, about 43 links. Spec: 38, 7, 43. Drawn: 38, 7, 43 in both versions (I did not check each line by eye). Missing: "every producer checks the Schema Registry" is one line from Kafka only. Platform has no lines, as asked.

3. Problems, quick (diagrams/ride.png, crop1.png, crop2.png):
- Page 6488 x 1723: the 11 core services are one row; unreadable without crops.
- 92 crossings; API Gateway to Identity crosses 15 lines.
- Very long lines: Driver profile to KYC runs along the bottom edge of Platform; Push provider to Driver app runs round the top and right of the page.
- Main route is in pieces; CDN to WAF loops under CDN.
- Kafka detail text crowds its icon.
Author (diagrams/author/ride.png, 2584 x 1994): much more compact, main path easier to follow. Wrong: Trip to Postgres and Payments to Postgres run along row 1 through six services (my waypoints); Identity to Redis and Support to Elasticsearch cross the Kafka bar; Kafka name overlaps its bar; "nightly load" label covers both nodes; Registry to Redis line crosses the Registry box.

4. Not expressible: a main route that is not a chain (it drew as one loop with Push to Driver app running round the page); a fan-in "every producer" without 5 lines; "Platform supports all" (only no line).

5. Bugs: no traceback. The quick layout fixes crossings only by part order; I fixed the Kafka errors by guessing an order.

6. Skill text:
- Icon names fail silently-late: `api` is refused, `api-gateway` passes; valid names are split between two lists.
- "Eight to twelve parts is a good size" and "more than about 15 use author" do not say whether 38 parts should go to author at once.
- Author skill does not give Box attributes (left, width); I computed `along` by hand.

Not verified: .drawio exists and parses as XML (ElementTree ok) but I could not render it; animation; other themes; each of the 43 lines.
