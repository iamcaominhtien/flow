# screen-C-01: third run, author kit, a Sonnet agent, plugin 0.11.2

Same brief as `2026-10-27-screen-C-01.md`. One fresh Sonnet agent got only the `Brief` text and the author skill (`skills/author/SKILL.md`), and was told not to open `benchmarks/`, `examples/`, `docs/`, `tests/`, the changelog or the git history. It read `skills/screen-flow/SKILL.md`, which named the ride example and the benchmark; it says it did not open the example.

## Result

- Seven build and look rounds; the agent read a full-page PNG and crops every round. Errors per round: 4, 1, 0, 0, 0, 0, 0.
- Final check: **0 errors, 7 warnings** (4 `lines-cross`, 2 `crosses-border` for the words of Home map to Profile tab across the gap between two zones, 1 `label-too-long` for "click Request invoice").
- Page 3144 x 2920 px. The second run (author kit, 0.11.1): 0 errors, 18 warnings, 2850 x 3950 px.
- Items: 46 screens (39 phone, 7 desktop), 3 diamonds, 3 entry pills, 77 connections, plus 5 legend texts and 4 legend lines. The agent compared the scene with its own list of the 77 pairs, typed from the brief: all present once. Not compared with `Structure` by a person.
- `make.py` is about 750 lines.
- The user, who looked at the picture: "better than I expected". No point-by-point review against `Must show` was written.

## Arrangement

Onboarding as a hook at the top left, the Web portal at the top right, Account and Booking in the middle (the Booking main path on one row, the detours under their parents), Payments and Trip at the bottom. Long returns run in lanes: Delete and Sign out up the left edge and over the top of the page, three returns to Home map between Onboarding and Booking, five lines under Booking 14 px apart.

## Weak spots (the agent's own reading)

- An empty corner of about 1000 x 850 px at the bottom left, holding only the legend; the Account and Web portal zones have open space.
- Four long lines (Delete account to Splash, Sign out to Welcome, each about 2000 px; SOS to Support help about 1600 px; Cancel ride to Home map about 1700 px). The skill suggests a pair of connectors for a return longer than half the page; the agent did not use one.
- The entry points were drawn as two frames with the same name (App icon at the top left; Push and Deep link under Booking). The brief has one group; the design puts the pills in one left column.
- Four arrowheads 20 to 25 px apart on the top of Home map, and chips close together in the lane bands.
- Not verified by the agent: the draw.io file in draw.io, and the animation.

## Kit and skill gaps the agent hit

1. Which group a screen belongs to, when the brief lists connections by group and not the members: not said. The agent placed a screen in the group whose paragraph first has it as a source.
2. `via` corners go horizontal first: not said.
3. On a vertical back-and-forth pair the default put both chips between the two lines; the agent set `is_left` on one of each pair by hand.
4. A mini phone cut off "Notification permission" and "Location permission", and the check said nothing; the agent set `width=150`.
5. An entry pill's detail repeated its name at first.
6. Zones are rectangles only.
7. `crosses-border` on Home map to Profile tab read as if the line crossed the border; it was the chip.
8. The repo's ruff hook rewrote the agent's scratch script in the temporary folder.

What 0.11.3 changes for these is in the changelog. Files of the run (scratchpad, not in the repo): `run3/make.py`, `ride.html`, `ride.drawio`, `ride_final.png`.
