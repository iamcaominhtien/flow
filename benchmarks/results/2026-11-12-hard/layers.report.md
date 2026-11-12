# Layers blind test report

1. Path: quick only. 1 round, no fixes needed. Final exit code 0; check: "no problems found" (0 errors, 0 warnings). Author path not used: no check errors and the picture is readable, so the step 3 condition was not met (it is, however, missing the brief's arrows; see 3).

2. Counts
- Layers: brief 7, spec 7, drawn 7.
- Items: brief 41, spec 41, drawn 41.
- Vertical bands: brief 2, spec 0 (text in desc only), drawn 0 (only a subtitle sentence).
- Arrows: brief about 28 item-to-item arrows. Spec 0. Drawn: 6 generic layer-to-layer arrows from "flow": true, which the brief did not ask for.
- draw.io: 65 mxCell elements; parses as XML.

3. Wrong or hard to read (screenshot layers/diagrams/saas.png)
- No item-level arrows. The highlighted main request path (Web app to PostgreSQL), the skip arrow Reporting to ClickHouse, the upward Object storage to CDN, PostgreSQL to Backup vault and "every service runs on Kubernetes" are absent. The six identical blue arrows between bands wrongly suggest a strict layer-by-layer downward flow.
- The two vertical bands (Security and compliance; Observability) are not drawn; the subtitle sentence wraps awkwardly ("on-/call)").
- Rows are centred, so 5-item layers are offset from 6- and 8-item layers; no column alignment, hard to see what sits above what.
- "PostgreSQL (primary + 2 replicas)" is a two-line box; replicas not shown separately.
- Experience and Infrastructure both blue (only 6 tones for 7 layers). All item boxes are the same blue whatever the layer tone.

4. Not expressible: cross-layer vertical bands; item-to-item arrows; skip or upward arrows; a highlighted path; one node under many items; an arrow inside one layer. Nearest used: bands as subtitle text; arrows dropped.

5. Plugin bugs: none seen. Command: python3 /home/user/flow/plugins/flow/scripts/flow.py build diagrams/saas.spec.json exits 0. The check cannot detect that brief content was dropped.

6. Skill text: unclear whether `flow: true` is meant as a highlighted path (it is not item-specific). Nothing says what to do when the brief needs item arrows or bands. The author pointer (more than about 15 elements) applies here (41 items) but sits at the end, after the steps that say to build. "Do not say looks good" sits oddly with a look-at-it step.

Not verified: .drawio not rendered (only parsed). Viewed one full-page 1600x1224 screenshot; no crops, animation or other themes checked.
