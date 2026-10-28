# screen-C-01 at L0: fifth run, author kit, a Sonnet agent, plugin 0.12.0

Same brief and the same closed folders as `2026-10-28-screen-C-01-l0-sonnet.md` (the fourth run, 0.11.3), to see what 0.11.4 and 0.12.0 changed. The plugin was 0.12.0 when the run started. The 0.13.0 work (L4 screens, the HTML line layer taking no clicks) landed in the same files while the run was going; none of it changes how an L0 diagram is laid out or checked.

## Result

| | Run 4 (0.11.3) | Run 5 (0.12.0) |
| --- | --- | --- |
| Rounds | 2 | 4, and a final rebuild |
| Final check | 0 errors, 9 warnings (8 `lines-cross`, 1 `label-too-long`) | 0 errors, 9 warnings (all `lines-cross`) |
| Page | 2804 x 2760 px | 2757 x 2472 px |
| `make.py` | 372 lines | 574 lines |
| Time | about 23 minutes | about 26 minutes |

- Items: 46 L0 cards (39 phone, 7 desktop) with codes S01 to S46 and W01 to W07, 3 diamonds, 3 entry pills, 77 connections, a legend and a Conditions table. The agent counted them in its script; not compared with `Structure` by a person.
- The new pieces were used: the long web phrase is code C1 with a Conditions table (`EdgeWords(code=)`, `Canvas.conditions`), so `label-too-long` is gone. The entry pills are one column, each level with the screen it opens. Round 1 had 4 `label-on-line` warnings; the agent cleared them.
- Two long names were cut in round 1 and reported by the 0.11.4 check; the agent widened those cards.

## Weak spots (the agent's own reading)

- Nine crossings. Four are the line from Profile tab to Support and help, about 1400 px long: Support is reached from Account and from Trip.
- The chips of the lines in the lane between the two columns ("tap Help", "tap Cancel ride") sit away from the screens they leave.
- A long vertical main-path line from Driver assigned to Driver arriving; dense corridors in Payments.
- Empty space: three cells of the Account zone, the top row of the Web zone, the tall entry zone, the area under Trip.

## Kit and skill gaps the agent hit

1. How `segment=` counts stretches on a line with `via` points was not said.
2. Two L-shaped lines between diagonal neighbours, one each way, cross unless nested; not said.
3. The legend example in the skill left out `Role.NO`, which a failure line uses.
4. The entry column needs about 90 px between a pill and its zone for the chip of its line; the skill gives 140 px for chips between screens.
5. A chip far from the screen its line leaves is not reported (no check for it).

Items 1 to 3 are now in the author skill. Items 4 and 5 are open. Files of the run (scratchpad, not in the repo): `run5/make.py`, `ride.html`, `ride.drawio`, `ride_final.png`.
