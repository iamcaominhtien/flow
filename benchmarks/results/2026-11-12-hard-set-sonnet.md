# Hard set, one blind Sonnet agent per diagram type (plugin 0.17.0)

Date: 2026-11-12. Briefs: [`../briefs/hard.md`](../briefs/hard.md), 21 briefs, one per type. One Sonnet agent per brief, each with only the `Brief` text and the skill of its type. The agents' own reports and their specs are in [`2026-11-12-hard/`](2026-11-12-hard/) (`<type>.report.md`, `<type>.<name>.spec.json`). The HTML, draw.io files and screenshots were not committed.

## How it was run

- The agent followed the type's skill (the quick path), at most the rounds the skill allows, then took a screenshot of the HTML and read it.
- It was told to try the `author` skill once, only when the type's skill points there **and** the quick picture had errors or was hard to read. This rule was too narrow: concept, layers, roadmap, kanban, org-chart, er and screen-flow built without errors, so those agents did not switch, although content was missing or the picture was hard to read. bpmn and gantt ended with errors and did not switch either.
- It could not open `benchmarks/`, `examples/`, `docs/`, `tests/`, the changelog or the git history.
- 20 agents ran at once and the 21st after the first finished.

## What was checked by the reviewer, and what was not

- Checked: one reduced full-page screenshot of every final page was opened. Each matches its agent's report at that size (page shape, missing parts, bundles of lines). Text-level claims (clipped words, a label on a line) were not checked one by one.
- Checked: three plugin faults were reproduced (see below). One was not.
- Not checked: the element and line counts in the table are the agents' counts. No `.drawio` file was rendered; the agents only parsed them as XML. No animation was looked at.

## Results

"Quick" is the type's skill; "author" is the `author` skill. Errors and warnings are from the last build's check report.

| Type | Path | Last build | Page (px) | Main finding |
| --- | --- | --- | --- | --- |
| flowchart | quick | exit 2: 2 errors, 18 warnings | 2795 x 2073 | The five lanes are drawn twice, one set under the other, and the fork bar runs from one set into the next |
| flowchart | author | exit 0: 0 errors, 3 warnings | 3223 x 1718 | Lines attach along the fork and join bars and run over two boxes |
| sequence | quick | exit 0 after 3 rounds | 2394 x 3247 | The errors went away only when a synchronous call was changed to asynchronous; activation bars stop early |
| er | quick | exit 0: 0 errors, 77 warnings | 3283 x 1676 | 27 tables and 44 relations drawn; the `tenants` lines merge into one bar and lines cross other domains |
| architecture | quick | exit 0: 0 errors, 92 warnings | 6488 x 1723 | 11 services on one row; the main route is in pieces |
| architecture | author | 16 errors, 50 warnings | 2584 x 1994 | Much more compact; lines to Postgres run through six services |
| bpmn | quick | exit 2: 17 errors, 32 warnings | 3696 x 1978 | Message flows run through tasks of the Insurer lanes |
| state | quick | exit 0: 0 errors, 35 warnings | 2950 x 1477 | The InProgress frame is not drawn; its two regions are separate frames |
| state | author | exit 0: 0 errors, 3 warnings | 2704 x 1528 | Clearly better; lines to the small final-state rings stop short |
| org-chart | quick | exit 0: 0 errors, 50 warnings | 11548 x 1390 | The 5 dotted reports cannot be drawn (links across levels are refused); staff sit with the directors |
| gantt | quick | exit 2: 10 errors, 5 warnings | 5004 x 3133 | Arrows run through bars; no shaded band; critical path not marked |
| mind-map | quick | exit 0: 0 errors, 11 warnings | 2901 x 2708 | 83 nodes and 3 links drawn; the links run as one bundle down the right margin |
| class | quick | exit 0 after 3 rounds, 14 warnings | 4110 x 3124 | Needed a hand-written `at` grid; the automatic layout gave 28 errors |
| class | author | 53 errors, 39 warnings | not recorded | Worse: boxes overlap |
| layers | quick | exit 0, no problems | 1600 x 1224 | 41 items in 7 layers; none of about 28 item arrows and neither vertical band can be expressed |
| usecase | quick | exit 2: 28 errors, 9 warnings | 1764 x 3281 | One frame, not two; actor lines fan through the ovals |
| usecase | author | exit 2: 5 errors, 86 warnings | 2512 x 1624 | Two frames; six actors moved between the frames, against the brief; pills, not ovals |
| wireframe | quick, 3 specs | exit 0: 6 warnings in all | 1704 x 1173 (part 1) | Table and feed run out of the desktop and tablet frames and cover notes 7 to 9 |
| roadmap | quick | exit 0: 0 errors, 1 warning | 4373 x 3235 | 1 of 7 dependencies; no milestones, today marker or status; every card says "Committed" |
| explainer | quick | exit 0: 0 errors, 1 warning | 1884 x 3894 | Steps are numbered 1 to 13 in reading order, not as in the brief; two columns only in the comparison |
| c4 | quick | exit 1, nothing written | none | "18 boxes is too many (at most 15)" |
| c4 | author | 44 errors, 252 warnings | 3074 x 2060 | Lines to the external systems merge into one bar; no C4 shapes in the kit |
| dfd | quick | exit 2: 4 errors, 100 warnings | 4848 x 2810 | 29 elements and 56 flows drawn; long lines wrap round the page |
| dfd | author | 54 errors, 131 warnings | 2659 x 1951 | Worse; default routes, no waypoints |
| cloud | quick | exit 0: 0 errors, 121 warnings | 18084 x 2121 | Unreadable at that width |
| cloud | author | exit 0: 0 errors, 6 warnings | 3104 x 1978 | Readable nesting; 28 of about 35 links; lines run through the zone pills |
| kanban | quick | exit 0: 0 errors, 41 warnings | 2828 x 1821 | 48 cards; no horizontal lanes; three long titles overlap their tag and points |
| concept | quick | exit 0, no problems | 1600 x 1529 | At most 10 parts (12 asked); no satellites, no links between parts |
| screen-flow | quick | exit 0: 0 errors, 119 warnings | 3634 x 6986 | 75 items drawn; arrows cross whole zones; the transfer route zigzags |

## Plugin faults

Reproduced by the reviewer:

1. **Unknown icon name recurses without end.** `flowlib/theme.py`: `icon_svg` calls `detailed_icon_svg` when the name is not a flat icon, and `detailed_icon_svg` calls `icon_svg` when it is not a detailed one. `theme.icon_svg("users", 24, "#000")` raises `RecursionError`. The wireframe agent met it with sidebar icons `["users", "settings"]`: the build crashed with no message.
2. **State: a composite that holds two composites loses its frame.** The scene of `2026-11-12-hard/state.ride.spec.json` has the frames Assigned, Movement and Safety, and none for InProgress. No warning is printed.
3. **Flowchart with lanes: the lane set is drawn twice.** The scene of `flowchart.cap-cuu.spec.json` has eight lane frames: all five lanes from y = 164, then four of them again from y = 1064 (no second "Điều dưỡng phân loại"). Whether this is a deliberate wrap of a long chart was not found out; the skill does not mention it.

Reported by an agent, not reproduced:

4. Cloud: `KeyError` on `rows[part.id]` when a part in a region or VPC frame is linked only to parts that have no row (the agent's ids `tgw1`, `s3a`). The agent's final spec with its extra link removed built without the error, so the exact condition is not known.

Reported by agents, not checked:

- Roadmap: the one-line note makes the page 4373 px wide for a chart of about 1650 px. (The page width is confirmed; the cause is the agent's reading.)
- Author kit: a small end or fail ring keeps its ports on a 160 px box, so lines stop short of the ring (state). `leave_along` and `arrive_along` seem ignored on a bar (flowchart).
- Check gaps: text that overflows its card is not reported for concept (Profiles) and explainer (two cards); kanban gives the same `kanban-card-full` warning for cards that fit and for the three that overflow.
- Wording: a check message repeats the name ("store 'd1' (Prescriptions) (Prescriptions)", dfd); a raw newline inside an actor label splits one message over two lines (usecase); the author legend says "Message between pools" for a C4 event stream.
- Legends and fixed words are English in a Vietnamese diagram: "Link between branches" (mind-map), "Reports to", "Open role" (org-chart). The flowchart `else` rule and the Yes/No chips know English words only, and `text-too-long` counts Vietnamese syllables as words.

## What the skills could not express

- layers: arrows between items, arrows that skip layers or go up, vertical bands across layers, a highlighted path.
- concept: more than 10 parts, satellites, links between parts.
- roadmap: status, milestones, a today marker, more than one dependency, a dependency that points back in time.
- kanban: horizontal lanes, a blocked mark, a due date, a legend, a totals row.
- org-chart: a dotted report across levels, staff positions beside the chief, a position with a title and no name.
- gantt: a shaded band, two owners on a task.
- explainer: a comparison of three things, an analogy as mapped pairs.
- usecase (quick): two system boundaries. class: static and abstract member marks. state: parallel regions, history, a transition from a composite's border. er: a pointer to any table. sequence: a branch inside a loop.
- wireframe: line and donut charts, sparklines, a floating button, an icon rail, a carousel, pagination, several sets on one page.

## Unclear parts of the skills, as several agents reported them

- The pointer to `author` is the last line of a skill, after the steps that say to build. No skill says to switch before building when the brief is clearly too large.
- `author` has no shapes or example for C4, class, DFD or use case, and no advice for many lines into one column of boxes.
- "Warnings may stay" gives no limit: screen-flow, er, architecture and cloud built with 77 to 121 warnings and no error.
- `line-through-node` has no fix in the skills beyond reordering or guessing `at` positions.
- er: `from_column` and `to_column` are called "not drawn yet" in one place and said to set where the line leaves in another.
- Icon names are split over two lists (architecture), or not listed (wireframe).

## Faults in the briefs, found by this run

Listed at the top of `../briefs/hard.md`. The brief text was left as it was run.
