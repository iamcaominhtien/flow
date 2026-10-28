# screen-C-01 at L0: fourth run, author kit, a Sonnet agent, plugin 0.11.3

Same brief as `2026-10-27-screen-C-01.md`, with one sentence added in front: "Draw it at fidelity L0: names only, nothing inside the screens." One fresh Sonnet agent got the brief and the author skill, with the same folders closed as in `2026-10-28-screen-C-01-author-sonnet.md`, and also the folders of earlier runs.

## Result

- Two build and look rounds (the skill asks for three or more). Round 1: 0 errors, 12 warnings. Round 2 (final): **0 errors, 9 warnings** (8 `lines-cross`, 1 `label-too-long` for "click Request invoice").
- Page 2804 x 2760 px. `make.py` is 372 lines, about half of the L2 run's.
- Items: 46 screens as L0 cards (39 phone, 7 desktop), 3 diamonds, 3 entry pills, 77 connections, plus a legend. The agent counted them in its script; not compared with `Structure` by a person.
- Entry points are one zone, the three pills in one column at the left, as the 0.11.3 skill says. No `crosses-border` warning is left.

## Arrangement

Four bands: Onboarding; Booking; Account (left) and Trip (right); Payments (left) and the Web portal (right). The entry column runs down the left. Delete to Splash, Sign out to Welcome and Trip history to Home map run in three channels left of the entry column.

## Weak spots (the agent's own reading)

- Eight crossings, most of them entry lines from the left column crossing the lines under Home map.
- Long lines: Push to In trip, Promo link to Promo code, Trip history to Home map (about 2000 px).
- Empty space: the right half of the Onboarding band, between Payments and the Web portal, the lower right of Trip and of Account. The entry zone is a tall strip with its pills far apart.
- The words of back-and-forth pairs are small.

## Kit and skill gaps the agent hit

1. "NotificationPermission" and "DeleteAccountConfirm" were cut off in their phone cards and the check said nothing: the 0.11.3 check left L0 cards out. The agent widened the cards to 184 px.
2. The skill said only "a screen with `Fidelity.L0` is a card": not what the card shows, its size, or that it needs a `code`. The agent made up S01 and W01.
3. Chip placement does not avoid other lines, and the check does not report a chip on another line.
4. The 20-character limit is shorter than one of the brief's own phrases, and the warning's advice (`conditions: coded`) does not exist in the author kit.
5. The legend has no sample for the dark (person) and slate (system) chips.
6. "One column at the left, each pill at the height of its screen" cannot hold when the screens are far apart.

Items 1 and 2 are fixed in 0.11.4. Files of the run (scratchpad, not in the repo): `run4/make.py`, `ride.html`, `ride.drawio`, `ride_final.png`.
