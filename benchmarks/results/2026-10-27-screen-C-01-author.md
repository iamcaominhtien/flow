# screen-C-01: second run, author kit (hand-laid), plugin 0.11.1

Same brief as `2026-10-27-screen-C-01.md`. One fresh agent, `flow:author`, a `make.py` of about 550 lines written with `flowlib/author.py`.

## Result

- Six build and look rounds. Final check: **0 errors, 18 warnings** (17 `lines-cross`, 1 `label-too-long`).
- Page 2850 x 3950 px (the skill targets 2500 high). The automatic layout of 0.11.1 on the same brief: 0 errors, 41 warnings, about 3830 x 5740 px.
- Read by the lead (`r6.png`): seven zones in rows (Onboarding in one row, Booking, Trip beside Account, Payments, Web Portal below), phone frames with id chips (S101...), desktop frames with traffic-light dots for the web screens, amber diamonds, green entry pills, dark user chips and slate system chips with icons, green and rose guards, blue animated main path, a legend. No line runs through a screen. Zones read left to right.
- Weak spots: four long returns run the whole page (Delete confirm to Splash, Sign out confirm to Welcome, Cancel ride to HomeMap, Home tab); a few chips sit away from their vertical lines; two identical "tap Confirm" chips on the long returns; screens are bare hatched blocks (no `elements`); four trigger texts were shortened.
- Items: 57 nodes (46 screens, 3 diamonds, 3 entry pills, 5 legend text nodes) and 77 connections, all drawn as the agent counted them.

## Kit and skill gaps the agent hit (bug reports)

1. `Canvas.node` cannot take a screen, and `Canvas.edge` cannot set a trigger or guard chip: the agent replaced the node with `dataclasses.replace(node, screen=ScreenView(...))` and built `EdgeLabel`s and `extras` by hand.
2. `place_labels` moves only the main label, not `extras`, so a moved guard landed on the line.
3. The author skill documents none of the screen-flow pieces (`ScreenView`, `LabelKind.USER`, `SYSTEM`, `GUARD_OK`, `GUARD_FAIL`, `ChipPlace`).
4. The check flagged `label-covers` for chips wider than their gap and `crosses-border` for a chip across two zone borders (fixed by moving nodes).

## Comparison

For this size the hand-laid version is cleaner and smaller than the automatic one (18 against 41 warnings, 2850 against 3830 px wide), but it needed a 550-line script and workarounds for the kit gaps above. The automatic one needs no script and has no errors.

Files (scratchpad, not in the repo): `run2/make.py`, `ride.html`, `ride.drawio`, `r6.png`, `dv.png`.
