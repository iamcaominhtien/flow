# Level C briefs, drawn by agents: the build path against the author path

Date: 2026-10-26. Each row is one blind run: a fresh agent given only the text under `Brief`
and the skill named. One run per row, so this shows what is possible, not an average.
Counts were checked against `Structure` by script where the agent kept the brief's ids.

| Brief | Path | Page (px) | Steps / lines | Check | Notes |
| --- | --- | --- | --- | --- | --- |
| flowchart-C-01 (BGP) | `build`, plain | 9930 x 980 | 43 / 51, all match | 0 errors, 14 warnings | One long row; a bundle of near-parallel lines into one node |
| flowchart-C-01 | `build`, illustrated | about 10000 wide | 43 / 51, all match | 0 errors, 9 warnings | 6 cards; looks like the plain one |
| flowchart-C-01 | `build`, plain, after folding | 3219 x 2580 | same | 0 errors, 21 warnings | Shorter, but long vertical lines between bands and empty lanes |
| flowchart-C-01 | author, free (no design rules given) | 3000 x 2150 | 43 / 51, all match | no problems | Compact, but Title Case, cylinders, bar nodes: off the design |
| flowchart-C-01 | author, plain | 2534 x 2074 | 43 / 51 (ids renamed, not matched one by one) | 0 errors, 4 warnings | In the design's style; the hub node still bunches its lines |
| flowchart-C-01 | author, illustrated | 2864 x 2334 | 43 / 51 | no problems | 5 cards; the first run showed a kit bug (card sized as a plain node), fixed |
| bpmn-C-02 (order fulfilment) | author, illustrated | 4384 x 2112 | 46 / 55 | 0 errors, 5 warnings | Standard BPMN shapes; wide because time runs left to right; events were ellipses (kit bug, fixed) |

## What the runs showed

- The automatic layout, not the agent, set the quality on the build path: the agent could only change the spec.
- With freedom to place nodes and routes and to look at the picture, agents got compact pages in three to five rounds.
- Without the design rules in the skill the agent invented shapes and wrote Title Case; with them it followed the design.
- The checks missed what only a look found: ellipse events, a card whose pill sat outside its box, near-parallel line bundles, wasted space. Each was fixed in the kit or the skill, and the check now covers overlapping lines and covered captions.

## Not verified

- Domain correctness of the briefs; the draw.io files in the editor; other models; the other diagram types; averages over several runs.
- The author runs renamed steps, so the line counts there are the agent's, checked by count only.
