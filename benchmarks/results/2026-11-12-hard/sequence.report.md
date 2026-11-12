# Sequence test report (10-participant web checkout)

1. Path: quick only (the final build had no errors, so the author skill was not tried). Rounds: 3.
 - R1: exit 2, 2 line-through-node errors (m34 "Send email", m43 "Tell shopper: failed" cross bar-1, the Browser SPA bar), 0 warnings.
 - R2 (both spa->gw calls made async): exit 2, same 2 errors; bar-1 came from "Click Pay" (sync, answered by the last "Show result").
 - R3 (Click Pay made async): exit 0, "no problems found". This changed the meaning of a message; it is not a real fix.

2. Counts. Brief: 10 participants, about 44 messages, 5 fragments (opt, par, alt, loop, alt). Spec: 10, 46 messages (5 self), 5 fragments. Drawn: 10 headers, 46 message edges, 5 frames, 11 bars. I viewed the whole page in three crops.

3. Picture problems (diagrams/full.png top, c1000.png middle, c2000.png bottom):
 - Activation incomplete (full.png, c1000.png): the Order Service bar stops at the 3-D Secure redirect and the Gateway bar at the 401. Mark PAID, publish, release, void and the final 201/402 have no bar. Payment and Inventory bars are tiny. The brief asked to show when each service is active; only partly met.
 - "Send email" and "Tell shopper: failed" (c2000.png) run across 9 lifelines; "POST result to ACS" spans 5 (c1000.png). The brief's participant order causes this.
 - Click Pay (async after R3) has its answer as a dashed return "Show result" with no matching sync call.
 - Page is 2394 x 3247 px; the header row is not visible in lower parts.
 - Blue main arrows are dashed like returns (full.png: Click Pay, POST /checkout), easy to confuse with returns.
 - Loop shows one Capture and one reply; the retry on timeout is only in the guard text and "Captured / timeout".
 - Not verified: animation, any browser other than the screenshot tool, .drawio rendering (cannot render here). The .drawio parses as XML (440 elements).

4. Not expressible: a timeout branch inside the retry loop (only guard text); activation for async-only chains (Broker, Notification have no bars).

5. Plugin bugs: no traceback. Questionable: bar-1 is correct per the pairing rule, yet any long-open call turns every crossing message into an error. Command: build diagrams/checkout.spec.json with Click Pay as sync.

6. Skill text: it does not say that a long-open sync call makes a bar that crossing messages hit as an error, or that the fix is to make the call async. Overrides are only referenced through the flowchart skill, which I may not read. It says about six participants fit; the brief has ten, and I did not split.
