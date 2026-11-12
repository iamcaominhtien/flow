# Hard set, second run: every brief done by the session's own model, mostly with the author kit (plugin 0.17.0)

Date: 2026-11-12. Briefs: [`../briefs/hard.md`](../briefs/hard.md). First run (one blind Sonnet agent per type): [`2026-11-12-hard-set-sonnet.md`](2026-11-12-hard-set-sonnet.md).

**This run was not blind.** The same session wrote the briefs, read the 21 agent reports and knew the `Must show` lists. For 9 types the content (names, columns, card texts, arrow words) was taken from the first run's spec and only the layout is new: er, mind-map, class, dfd, kanban, screen-flow, and partly architecture, usecase, concept. The scripts and pictures are not committed (the scripts do not follow the repository's Python rules); they were handed to the user as a zip.

## What was checked

Every final page was rendered and looked at once, at reduced size (kanban, explainer and wireframe also in a crop). Text-level faults (a clipped word, a chip on a line) were not checked one by one beyond what the check reports. No `.drawio` file was rendered.

## Results

All 21 final builds have 0 errors. "First run" is the best result of the Sonnet agent for that type.

| Type | Path | Warnings | Page (px) | First run | What is still weak |
| --- | --- | --- | --- | --- | --- |
| flowchart | author | 2 lines-cross | 3264 x 1758 | 2 errors quick; 0 errors author with lines over boxes | The "Có" return of the reassessment crosses two lines |
| sequence | quick | 0 | 2384 x 3200 | 0 errors after changing a call to async | After the 3-D Secure branch no bar is open, so the last answers have no activation; a note says so |
| er | author | 15 lines-cross | 3258 x 1628 | 55 lines-cross, lines merged | The gap between Catalogue and Orders carries six lines |
| architecture | author | 22 lines-cross | 2704 x 1700 | 92 quick; 16 errors author | The strip between the services and the stores is busy |
| bpmn | quick, every element pinned to a column | 18 | 4612 x 1808 | 17 errors | 57 elements on one page; the below-excess rejection sends no message to the policyholder |
| state | author | 2 lines-cross | 2584 x 1528 | 0 errors author, lines short of the final rings | Final states are pills, the start is a ring; no parallel-region notation, two frames stand for it |
| org-chart | author | 6 lines-cross, 15 lines-overlap | 3420 x 1468 | 11548 px wide, no dotted lines | The overlaps are the shared trunks of the tree; cards are plain boxes, not person cards |
| gantt | quick, two-week columns | 5 | 2716 x 3185 | 10 errors, 5004 px wide | Milestones have no arrows; the critical path is drawn only where a dependency exists; the freeze is a rose bar, not a band |
| mind-map | quick | 8 (long phrases) | 2649 x 1924 | lopsided 5 to 2 | The three link arcs still run over leaves |
| class | quick, own grid | 21 | 2802 x 2988 | 4110 x 3124 | Rows are tall; one dashed line touches the edge of a wide box |
| layers | author | 3 lines-cross | 2264 x 1530 | no arrows, no bands | The band words are plain text lines |
| usecase | author | 9 lines-cross, 24 lines-overlap | 2424 x 1299 | 5 errors, actors moved | The overlaps are each actor's shared trunk |
| wireframe | quick, 4 specs | 1 | up to 5724 wide | content out of the frames | Four pages, not one; the desktop page is two screens (top, scrolled); charts are bars and rows |
| roadmap | author | 1 lines-cross | 2454 x 1693 | 1 of 7 dependencies, no status | Milestones and today are marks above the axis, not lines; two dependency routes take a detour |
| explainer | quick, 6 sections | 3 | 1884 x 5929 | wrong step numbers, 2 columns | Very long page; the journey is two sections; the three-way comparison is 15 cards |
| c4 | author | 38 lines-cross | 3079 x 1916 | quick refused; 44 errors author | The strip above the services row is busy; backoffice calls are one line with a label, not one per service |
| dfd | author | 19 lines-cross | 4064 x 1658 | 4 errors quick | 4064 px wide; eight entities and stores are drawn twice and marked (copy) |
| cloud | author | 6 lines-cross, 54 crosses-border | 3524 x 1518 | 18084 px quick; author with 28 of 35 links | The border warnings are lines entering nested frames; several regional services have no line |
| kanban | author | 0 | 2396 x 2098 | no lanes, titles over tags | Cards are plain boxes; urgent cards are not counted in the WIP limit, which the brief leaves open |
| concept | author | 11 lines-cross | 2754 x 1428 | 10 parts, no links | A grid, not a ring: spokes and links are right-angled |
| screen-flow | author | 18 lines-cross | 3624 x 4184 | 98 lines-cross, 6986 px tall | The tab bar is four arrows from Home; dialogs and sheets differ only by their chip and a grey tint |

## What made the difference

- **Hubs as wide bands.** An API gateway, a database, Kafka or a load balancer drawn as one wide box takes its lines straight, side by side.
- **A channel per bundle.** Lines that run the same way get their own row in a gap, nested so that the farthest one is outermost.
- **Copies in a DFD**, and **one trunk per actor** in a use case diagram.
- **Columns pinned by hand** in the quick BPMN path, so that every message flow is vertical.
- **A wider time unit** in the quick Gantt path: `periods` of two weeks with fractional `start` and `length` halves the width. The skill does not say that fractions are allowed.
- **The plugin's own route search.** `flowlib.pathfind.find_route` can be called from an author script to route a line around every box. The author skill does not mention it. It was used for the roadmap dependencies and for ten lines of the cloud diagram.

## More findings about the plugin

- The author kit sizes only the shapes in the theme's `min_sizes`. `Shape.USE_CASE`, `Shape.INITIAL`, `Shape.FINAL`, `Shape.PERSON_CARD` and `Shape.PLAN_BAR` raise `KeyError` in `Canvas.node`. `ELLIPSE`, `C4_BOX`, `C4_PERSON`, `DFD_PROCESS`, `DFD_STORE` and `ENTITY` work, and none of them is in the skill's list of shapes.
- A C4 box needs `technology` and `dashed` on its node; `NodeOptions` has no field for them. The script replaced the node after `Canvas.node`.
- Explainer, `tree` shape: five long `inside` chips run out of the left side of their card and over the lines. The check reported nothing.
- Wireframe: a block without `rows` makes its whole grid row as tall as itself, so a tall panel in row 2 pushes every later row down. In a responsive set the desktop frame is drawn small; a dense desktop page does not fit there.
- Sequence: a message that crosses an open activation bar is an error, so a long-open call forbids every message across it. The skill does not say so.
- A tiny `Shape.CONNECTOR` (10 x 10) works as an anchor on the border of a frame, for a transition that leaves a composite state. The kit has no such thing of its own.
