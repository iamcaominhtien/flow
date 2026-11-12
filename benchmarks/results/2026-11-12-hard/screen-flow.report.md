# screen-flow blind test: digital bank brief

1. Path: quick only, 1 build round, no fix round. Final exit code 0. Check: 0 errors, 119 warnings: lines-cross 98, crosses-many 19, label-on-line 1, text-may-not-fit 1, lines-overlap 1 (review>over and over>auth run on top of each other). The skill points to the author skill for more than 25 screens, but the build had no errors, so I did not try it (step 3 not met). Spec: diagrams/bank.spec.json (made by diagrams/gen.py), no `at` keys (auto layout). Page 3634 x 6986 px.

2. Counts. Brief: 4 entry points, about 66 screens and dialogs, 4 decisions, 5 tabs, about 90 arrows (one per sentence, some with "then" chains). Spec: 75 items (4 entries, 62 screens including 6 overlay screens, 4 decisions, 5 tabs), 87 taps plus one bus. Drawn: all 75 items visible, all arrows drawn. Not counted arrow by arrow in the picture.

3. Picture problems (diagrams/full.png, diagrams/crop_transfers.png):
- Long arrows run across whole zones and are hard to follow: Push to Transaction detail (through the Onboarding zone), Sign out confirm to Welcome (down the right edge and across), Authenticate to Reveal PIN (down the page into Cards), tab Pay to Pay hub and tab Savings to Savings goals. See full.png.
- Transfers zone: the flow is not read left to right. Pay hub, Choose recipient and Add recipient sit in the bottom row; the main route (blue) zigzags up and down through the zone. In crop_transfers.png, Processing to Success/Failed, Step-up OTP to Authenticate and the Try again return run through the same space.
- Words are detached from their lines: the guards [accepted], [under limit], [code correct], [success] float far from the arrow they belong to. Two chips ("tap Continue anyway", "name check returns") sit side by side and it is unclear which line each names.
- The tab bar draws 5 tabs plus a bus; the Home tab arrow loops back to Home. The Home screen is not marked as holding the bar (only said in desc).
- Authenticate and the sheets are drawn as full phone frames, much taller than the L0 cards, so rows are uneven.
- "Authenticate (customer phone)" is cut off on its card (warned).
- Zone placement: Teller zone is far from the rest, which is fine; entry column is tall and the Deep link/QR scan entries are far from Splash.

4. Not expressible: "Authenticate" shared between the transfer flow and Card detail is one node, so two flows meet there (nearest thing: one screen, long arrow to Reveal PIN). "Dispute submitted (a bottom sheet over Transaction detail)" is drawn as its own sheet screen, not on Transaction detail. "Then" chains (Show PIN, then Authenticate, then Reveal PIN) became separate arrows. Phone push to another device (Teller to customer phone) is only a system "phone" chip. Delivery of arrows with no words (many chains) has no label.

5. Plugin bugs: none seen (no traceback). Warning text for crosses-many suggests jump routes; I did not apply them.

6. Skill text: "give each an `at`" for up to 12 screens, and no guidance for 60+ screens beyond splitting; the brief says one diagram, so I used auto layout. The skill says warnings may stay, but with 119 warnings the picture is hard to read; no rule says when to stop. Tab bar pattern does not say how to mark which screen shows the bar.

Not verified: the .drawio file parses as XML (520 mxCell elements) but was not rendered. I looked at the full screenshot and one crop (Transfers); the other zones only at the reduced full view. The dark mode and the HTML animation were not checked.
