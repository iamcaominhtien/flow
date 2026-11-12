# Gantt blind test report

1. Path: quick only. No author attempt (skill allows one for large charts; I stopped after the 3 fix rounds). R1 exit 1: 4 invalid-spec messages (Target architecture, Data model mapping, Security design, System integration test start before their predecessor ends). R2 exit 2: 15 line-through-node errors, 5 warnings. R3 (rows reordered within phases) exit 2: final check = 10 errors line-through-node; 5 warnings: gantt-too-many-rows 1, lines-cross 1, lines-overlap 3.
2. Counts. Brief: 41 tasks, 6 milestones, 1 today line, 1 shaded band, 1 critical path, about 24 dependency links. Spec: 41 tasks, 6 milestones, today, 20 links, no band, no explicit critical. Drawn: 41 bars, 6 diamonds, 6 phase bands, 53 rows, today line; links drawn as in spec.
3. Problems (diagrams/top.png, mid.png, right.png, full.png 5004x3133):
 - 4 brief dependencies contradict the brief's dates; the build refuses them, so I removed Target architecture after Current-state, Data model mapping after Current-state, Security design after Target architecture, and SIT after Integration layer build. Also not drawn: Integration layer build after Integration inventory (I dropped it by mistake in my edit, not a tool limit).
 - 10 arrows run through unrelated bars: Vendor selection to Contract signature crosses Team onboarding and Programme governance (top.png); Core configuration to SIT crosses four Build bars; arrows into Go/No-go, Final migration, Go-live and from Test exit cross Legacy decommission planning. Milestones are in their own row at the end of each phase, far from their predecessors.
 - Page 5004 x 3133 px: unreadable as a whole, needs crops.
 - Hypercare has two owners; one owner field, I used Vendor.
 - Today line at start of W11 and progress fills render (top.png). Milestone Contract signature is at end of W8.
 - Critical path: no element with a critical class found in the HTML (grep); I did not open that region, so unverified. I did not set critical:true.
4. Not expressible: change freeze shaded band W46-49 (omitted); two owners; "weekend" note on Final migration; dependencies that overlap in time.
5. Plugin bugs: no crash. Files are written with exit 2. Command: python3 flow.py build diagrams/core.spec.json.
6. Skill text: not stated that `at` plus `after` on a milestone may be combined (it was accepted). "Fix errors by changing the spec" gives no way to clear line-through-node on a large chart except row order. Skill says one Gantt per phase, but the brief wants one chart with cross-phase links. Weeks mode: not stated that "end of W8" is `at: 8`; I inferred it from "3 is between W3 and W4".
Verified: .drawio parses as XML (mxfile, 286 mxCell); not rendered in draw.io (cannot here). Not verified: the right half of the page, critical path styling, other themes, author skill.
