# Changelog

## 0.11.4 (2026-10-28)

Screen text check and L0 cards. Found by the fourth `screen-C-01` run, at L0 (`benchmarks/results/2026-10-28-screen-C-01-l0-sonnet.md`): 0 errors, 9 warnings.

- The check of cut-off words in a screen now covers L0 cards too; 0.11.3 left them out, and two cut names went unreported.
- Words in a screen are measured with the widths of Inter's characters (`glyph_widths.py`, `inter_widths.json`), measured in Chromium at weights 500 and 700. The character-count estimate was off by up to 10% either way for one bold line. Compared with Chromium on 51 L0 cards (17 names on a phone, a mini phone and a desktop), 28 frames (14 names on a phone and a mini phone) and the ten screen flow examples: every name cut by more than 2 px is reported; two cut by exactly 2 px are reported too.
- Author skill: what an L0 card shows and its size, that every screen needs a `code` (S and W with two digits), and how many characters fit a phone, mini and desktop card. Screen flow skill: the card's size and name length.
- Not done: the other gaps of the run (chips on other lines, the 20-character limit in the author kit, a legend sample for trigger chips, entry pills far from their screens).

## 0.11.3 (2026-10-28)

Author kit and check: fixes from the third `screen-C-01` run, a Sonnet agent with the author kit (`benchmarks/results/2026-10-28-screen-C-01-author-sonnet.md`): 0 errors, 7 warnings.

- Words beside a vertical line choose their side when `is_left` is not given: left of a line that runs down the left half of the screen it leaves or enters, else right. A back-and-forth pair at `0.3` and `0.7` carries its words outside the pair without settings.
- Check: a title or an element name that a device frame cuts off warns `text-may-not-fit`. The estimate was compared with the widths Chromium draws for 14 titles on a mini phone and a phone; it flags every one cut by 3 px or more, and one of the two cut by 1 px. The ride example (three mini phone titles) and the overlay example (two modal buttons on a mini phone) now warn; both were already cut and are not changed.
- Check messages: `crosses-border` says "the chip of" a line when its chip is on the border, not the line; `label-covers` on a node says no clear place exists and gives the chip's width.
- Author skill: how `via` corners turn, the side of the words, the length of a screen title, the entry pill's detail and its left column, one zone per group, how to assign screens to groups when a brief lists only connections, and the gap a chip needs between two zones.
- Screen flow skill: the title length; the benchmark's numbers are taken out, since a blind run reads the skill. Benchmarks README: a blind agent is told not to open `examples/` (the ride example is a solution of `screen-C-01`).
- The ruff hook only touches files of this repository and keeps the `docs/` exclude, so it no longer rewrites a scratch script in a temporary folder.
- Not done: zones other than rectangles; a check for very long lines; a way to stack modal buttons that do not fit. The changes were not tried by a new blind run.

## 0.11.2 (2026-10-27)

Author kit: screen flows by hand. Found by the second `screen-C-01` benchmark run (`benchmarks/results/2026-10-27-screen-C-01-author.md`).

- `Canvas.node` takes a screen (`NodeOptions(screen=ScreenView(...))` with `Shape.SCREEN`), sized by the device table.
- `Route(words=EdgeWords(trigger, system_icon, guard, effect, is_failure, ...))` builds user and system trigger chips, green and rose guards, and effects, with the same functions the automatic screen flow uses.
- `place_labels` moves a chip and its extras together, sliding along the line in small steps first; screen id chips are obstacles.
- The check looks at extra chips and reports `label-covers` only when a chip cannot be slid clear.
- Author skill: a "Screen flows by hand" section with a runnable example and advice on lanes and channels for long returns.
- Benchmarks: the `screen-C-01` brief and two run records (automatic layout and author kit).
- Not done: a chip across two zone borders still warns `crosses-border`; the hand-laid benchmark script is only about 12% shorter (650 against 736 lines after formatting); real draw.io editor not used.

## 0.11.1 (2026-10-27)

Screen flow: large flows. Found by the `screen-C-01` benchmark (52 screens, 77 arrows): 27 errors with 0.11.0, 0 errors now.

- Arrows that would cross a frame (returns, far targets, entries) run in free lanes between rows and columns, each in a slot of its own, so parallel returns never overlap. The old outside loop is replaced by the lane router.
- Chips, guards and effects sit on a free stretch of their line, off frames, id chips, zone labels and borders, and other words.
- Screens with no `at` are arranged by zone, in flow order, wrapping in whole rows from the left, on shelves; web zones go below.
- The skill says what the automatic layout handles and suggests splitting by zone with flags, or `/flow:author`, above about 25 screens.
- Example `ride-screen-flow` (52 screens, 6 zones, 77 arrows); tests `test_screen_lanes.py`.
- Not done: the benchmark still builds with 41 warnings (33 `lines-cross`, mostly long cross-zone arrows), and the page is about 3800 by 5700 px; chips on long vertical runs sit beside the line; real draw.io editor not used.

## 0.11.0 (2026-10-27)

Wireframe rebuilt from `docs/design/10-wireframe.md`. Last phase of the design-gap plan (`docs/plugin/design-gaps.md` has the final status table).

- 25 grey blocks on a 12-column grid (navbar, sidebar, card, panel, list item, form field, buttons, image, tab bar, bottom nav, search bar, table, chart, figure, modal, sheet, toast, loading, empty, error, success, chips, stepper, rows, checklist) with phone (330x680), tablet and desktop (1320x760 with browser bar) frames; blue only for the primary action and the selection.
- Annotated screens: numbered badges on corners or named parts, notes in columns below, the red tap dot (`"tap": true`), captions as `id · name`.
- State set (`set: states`, exactly four states) and responsive set (`set: responsive`, desktop, tablet and phone at the same height).
- Checks: two primary buttons on one screen is an error; warnings for a badge over text, overlap, a screen taller than its device, stand-in words, notes over two lines, and the state-set rules.
- Screen flow: an L3 screen takes the same `blocks`, drawn smaller (example `shop-wireframe-screen-flow`).
- The old `header`, `text`, `input`, `button`, `image`, `list` kinds still build. Examples `wireframe-mobile`, `-desktop`, `-states`, `-responsive`.
- Not done: free coordinates, an illustrated style and live data in tables and charts (dropped on purpose); phones drawn 1:1, not 0.8; text width is estimated; spacings off by 2 to 8 px in places; real draw.io editor not used.

## 0.10.0 (2026-10-27)

Explainer, from `docs/design/07-explainer.md`.

- New `explainer` type and skill (`/flow:explainer`): layers, tree, comparison and concept shapes, or several on one page with `sections`; always illustrated. `layers` and `concept` still build as before.
- Cards 260x200 and row cards 700x92, bands 248 px high with pill labels and one tint each, numbered badges with letters (3a, 6b), spoken labels, a bold closing line, title 40 px and subtitle 16 px with 64 px margin. Sizes live in `theme.json` under `explainer` (`standard` and `compact` profiles).
- Blue animated path (off for reduced motion; `flowAnimation` in draw.io); step, return, yes and no lines with at most two bends.
- Warnings: more than 8 cards per shape or section, more than 14 words on a card, a protocol name on a line, no title.
- New shapes `explain_card`, `row_card`, `cell`, `pill_label`, `remark`, `section_head`, frame variant `strip`, node fields `chips` and `mono`; the draw.io importer reads explainer files back; midnight theme entries.
- Examples `explainer-layers`, `-tree`, `-compare`, `-concept`, `-payment`.
- Not done: concept facts are numbered left to right, top to bottom (the design text says clockwise); a card that links to a detail page (undecided in the design); a band with two rows of full cards; the "title is a question" rule is not checked; small pixel offsets; real draw.io editor and SVG export not tested.

## 0.9.0 (2026-10-27)

Planning part 2: Kanban and roadmap brought up to `docs/design/08-planning.md`.

- **Kanban:** work board with 360 px columns, 100 px cards, kind tags (Feature, Bug, Chore), owner circles, count and limit pills (`3 / 3`, red when full), done cards struck through. New keys: column `limit` and `done`, card `kind`, `owner` and `done`, top-level `people` and `use`. Plain only; the comparison use stays as `"use": "compare"`.
- **Roadmap:** rows with detailed lane icons, Now/Next/Later or quarter headers with dates in words, committed (solid) and idea (dashed, "Exploring") cards, owner circles, one blue animated dependency arrow (`depends_on` or `blocks`; a second is an error) and a note below the chart. Exact dates give a warning. Items use `period`; `start` still works; a `tone` on an item is now an error.
- New warnings: Kanban column over its limit, Kanban card text that does not fit, roadmap exact date.
- Owner initials come from the shared people helper (Gantt, org chart, mind map, kanban, roadmap); tint matches across diagrams when each spec pins it with `people`.
- Both types round-trip through scene.json and are read back from draw.io. Examples `delivery-kanban`, `delivery-roadmap`.
- Not done: columns end after the last card (the design leaves spare room); initials are two letters; lane icons are not read back on import; real draw.io editor not used.

## 0.8.0 (2026-10-27)

Planning part 1: Gantt, org chart and mind map brought up to `docs/design/08-planning.md`.

- **Gantt:** real ISO dates, week numbers or the old `periods` form; month header, 88 px weeks, 300 px label column, 52 px rows, phase bands, owner circles with initials, status colours with check, progress fill and blocked reason, amber milestones, finish-to-start arrows, one computed or marked critical path (blue, animated), today line with a red pill, legend, warning above about 15 rows.
- **Org chart:** bus lines, plain (210x78) and illustrated (232x110) cards, open role (dashed card), works-with line, legend, warnings above four levels and for roles written as sentences.
- **Mind map:** radial layout (three branches a side), illustrated, plain and large (four levels) forms, curved coloured lines, P1/P2, done, owner and `+N` marks, dashed violet cross-link arcs, warnings for phrases over four words and for more than four links.
- Shared: status palette, people circles with a tint stable per name or team, seven node shapes, new line roles and curved lines, in HTML, draw.io, scene.json, import and the technical and midnight themes. Examples `delivery-gantt`, `delivery-org`, `delivery-org-illustrated`, `delivery-mindmap`, `delivery-mindmap-plain`, `delivery-mindmap-large`.
- Not done: Kanban and roadmap (next); month cells follow ISO weeks, not four weeks a month; imported mind-map curves become polylines; icons are not read back on import; real draw.io editor not used.

## 0.7.0 (2026-10-27)

UML (state, use case, class) brought up to `docs/design/09-uml.md`.

- **State:** labels `event [guard] / action` (any part optional; `label` still works as `event`); `entry`/`do`/`exit` lines; composite states (`states` or `group`) as a frame with a pill; filled start dot, ringed end dots (several allowed); self loop above the box; rose failure paths; left-to-right happy path with branches below; 130 px or more between labelled states. `direction` is gone. Example `delivery-state`.
- **Use case:** system frame, stick-figure or illustrated actors, external systems on the right with the "external system" tag, 240x64 ovals tinted by the actor, include/extend dashed open arrows, hollow triangle for generalizes; one column per actor. The old `items`/`zones` form is still read. Examples `delivery-usecase`, `delivery-usecase-illustrated`.
- **Class:** boxes 280 wide, empty compartments omitted, mono members, `kind: abstract` (italic name) and `kind: interface` («interface»), multiplicities drawn at both ends, all relationship ends, parents above children. Example `delivery-class`.
- New shapes `INITIAL`, `FINAL`, `USE_CASE`, frame variant `SYSTEM`, node fields `activities`, `stereotype`, `is_italic`, `is_centered`, `Row.is_mono`, in every theme and in scene.json. The check tests slanted lines exactly (no false errors on diagonals).
- Not done: real draw.io editor and SVG export not tested; slight jogs where two lines share a box side; illustrated cards keep a pastel outline where the design has ink; illustrated actors need an `icon` (fall back to `user`).

## 0.6.0 (2026-10-26)

C4, cloud and architecture brought up to `docs/design/12-c4.md`, `13-cloud.md` and `06-architecture.md`.

- **C4:** boxes with icon, bold name, mono `[Kind: technology]` line and one sentence (280x132; the system at level 1 is 360x150); kinds person, system, external (grey dashed), container, database, component; levels 1 to 3 with `opens` (neighbours inherit from the level above, the opened box becomes a dashed frame labelled `Name [Kind]` on its bottom edge); 520x270 grid; protocol required on container lines; at most 15 boxes. Spec keys are now `technology`, `description`, `protocol`. Examples: three levels.
- **Cloud:** nine frame kinds with fixed colour and line, VPC range in the label, nesting 30 px and 40 px to parts, same subnets in every zone, managed services in the region outside the VPC, sites on the left. Refuses a database in a public subnet or DMZ and a line that skips two trust levels. Spec keys are now `frames` and `parts`. Examples: basic, delivery (two zones), network.
- **Architecture:** layers as rows (260 px plain, 240 px illustrated), `beside` third-party frames, lines to and from a frame, line kinds call, main, event, copy, 232x96 illustrated cards, the six patterns documented in the skill. Old keys `kind` on components, `style: async` and `direction` are gone. Examples: delivery (plain and illustrated), streaming (plain and illustrated).
- Shared: the DFD grid router is now `diagrams/grid_routes.py` and serves four types; new shapes `c4_box`, `c4_person`, `wide_card`; frame variants `network` and `layer`; HTML, draw.io, scene.json and import support.
- Not done: C4 frame pill colour (design draws it dark) and a pill that can sit on a line; cloud 40 px grid and 90 px label room check; architecture entry side and two lines between one pair; frame-edge lines end mid-side; Streaming warns `lines-cross` twice and `crosses-border` once; real draw.io editor not used.

## 0.5.0 (2026-10-26)

DFD and BPMN brought up to `docs/design/14-dfd.md` and `11-bpmn.md`.

- **DFD:** Gane-Sarson shapes (numbered header strip, store open on the right with an id cell, square-cornered entity); auto-numbered ids (E1, D1, 1.0, 4.1) never reused; illustrated cards at all three levels; 640x400 grid with two-way flows 60 px apart; `opens` draws a dashed frame around the opened process and checks that flows balance between levels. Refuses entity to entity, store to store, entity to store, black holes and miracle processes; warns on process counts per level and one-way stores. Examples `delivery-dfd-*` replace `order-dfd`.
- **BPMN:** pools and lanes (band 38 px, lanes >= 200 px), black-box pools, message flows with open circle and hollow head that run straight, boundary events (dashed = non-interrupting), event markers, task types, multi-instance, loop and sub-process marks, gateway marks, data stores with dotted association. New spec keys `trigger`, `repeat`, `attached_to`, `interrupting`, `column`, `row`, `failure`; `at`, `illustrated` and `icon` are no longer accepted. Examples `delivery-bpmn`, `order-bpmn`, `refund-advanced-bpmn`.
- **Checks:** BPMN element count, route bends, main path in one pool, message inside one pool and sequence flow between pools are refused.
- draw.io import reads back DFD shapes, BPMN marks, pool frames and boundary hosts; scene JSON gains `markers`, `host`, `caption_above`.
- Not done: numbered legend and callout badge of the Advanced board; expanded sub-processes, data objects, conditional/link/compensation events; a few `lines-cross` warnings; `order-bpmn` marks a main path in more than one pool and warns; real draw.io editor not used.

## 0.4.0 (2026-10-26)

Flowchart and sequence brought up to `docs/design/03-flowchart.md` and `04-sequence.md`.

- **Flowchart:** `fork` / `join` bars for parallel work (HTML, draw.io, import); multi-way decisions fan out over three sides; off-page connector note; `screen` cards; Yes/No chips keep their colour on any line; lanes 210/240 px with a straight lane change; lane charts fold later; new warnings (`text-too-long`, `decision-not-question`, `decision-few-exits`, `decision-no-else`, `chart-too-big`, `start-placement`, `end-placement`). Examples `payment-flowchart`, `delivery-flowchart`.
- **Sequence:** `"style": "illustrated"` (172x116 header cards with a 64 px icon and a name pill); header shape; 230 px pitch; 58 px under the header; frame inset 10 px and 34 px after a frame; frames coloured by kind; `ref` frames show a name; `break` keeps calls open; message `icon`; warning for labels over 24 characters. Examples `delivery-sequence`, `delivery-sequence-illustrated`.
- **Fixed:** a created participant crossing its fragment; labels on lane borders and frame borders in every type.
- Not done: a leftward failure branch in layout (Delivery routes around it); equal widths across lane rows; long activation bars of the design picture (ours come from call and return pairs); a header imported from draw.io becomes a plain box; real draw.io editor not used. Delivery flowchart still warns `chart-too-big` and one `lines-cross`.

## 0.3.0 (2026-10-26)

Screen flow rebuilt from `docs/design/02-screen-flow.md`.

- Device frames (phone, tablet, desktop with browser bar, watch, mini phone), id chips (`S01`, `W01`, `S31 · loading`, `S12 + modal`), fidelity L0 to L2 (L3 is drawn as L2), hotspots, undecided dashed cards.
- Transitions as `trigger [guard] / effect`: dark chip for the user, slate chip with icon for the system, green and rose guards, codes C1/C2 with a conditions table, kinds forward, main, failure, back, retry.
- Layout from rows, columns and zones: gap 130 or 96 px, upper and lower third for paired arrows, back arrows in a strip above, entry pills with flags, one tab-bar bus, overlays, states of one screen, web flow in its own zone.
- Scene format, draw.io output and draw.io import round trip for screens; a `red` tone; check `label-too-long`. Import now keeps line ports and reads roles back from colours for all types.
- Examples: the shop app (14 phone screens, 8 web screens) and seven pattern examples. Old plain-box screen specs still build.
- Not done: L3 as a real wireframe; orientation pairs and the tablet board; arrows enter the top of a frame where the design enters the side; a strip arrow can cross a zone pill (seen: `tap Orders` over the zone label); real draw.io editor not used.

## 0.2.0 (2026-10-26)

Foundations, from `docs/design/01-foundations.md`. First phase of closing the gaps listed in `docs/plugin/design-gaps.md`.

- **Themes:** a `theme` key on every spec (`pastel` default, `technical`, `midnight`) for HTML and draw.io, page background included; an unknown name is an error. The author kit has `Canvas.theme`.
- **draw.io line weights** come from one table; animated lines use the design recipe (main 3 at 500 ms, data 1 at 1500 ms).
- **Type scale** from the design: title 20/800, frame pill 13/700, node 12/600, edge label 10/500, nothing under 10.
- **draw.io:** frame names are pill cells, containers have a dash pattern and stroke, nodes have a shadow. The importer reads the pills back.
- **Check:** warns when a label or box straddles a frame border or sits on a divider (`crosses-border`, `on-divider`). It finds real defects in four examples, not fixed yet.
- Not done: callout tag and root node (no type draws them); a scene imported from draw.io is always pastel; the real draw.io editor was not used.

## 0.1.5 (2026-10-26)

The three ER features of the design that were missing, and two fixes found on the way.

- **Split by domain:** `flow.py split spec.json` writes an overview (a box per domain, a line per foreign key that crosses a border, named after the column) and a page per domain, in which a table of another domain appears once as a grey dashed copy with its key and a tag ("See Orders page").
- **Domain frames:** `"domain_frames": true` draws a dashed tinted frame with a name pill around the tables of each `domain`.
- **Subtype:** a relation with `"style": "subtype"` draws a hollow triangle at the parent.
- **Fix:** `scene.json` kept no key chips, so a scene written and read back lost them; it now keeps them.
- **Fix:** in the `.drawio` file the names of rows with and without chips start at the same x, as in the HTML.
- A table can be `dashed` (a reference drawn elsewhere); examples `delivery-er-domains.spec.json`.

## 0.1.4 (2026-10-26)

Checked the ER output against every rule of `docs/design/05-er.md`.

- A relation that names `from_column` and `to_column` now starts and ends level with those rows, as in the design (before, the columns were read but not drawn).
- A `logical` relation is a dashed slate line of its own role (`Role.LOGICAL`), not a plain ink line.
- A table that points at itself is drawn as a loop at its right side, with its label beside it (before, its label covered the table).
- Plain table header is 40 px (was 36), so the illustrated one is 24 px taller as in the design; columns are 160 px apart.
- ER skill: names, types, tones by domain, junction tables, relations, placement and size, taken from the design; it lists what is not built (split by domain, subtype mark, domain frame).
- Example names are singular and PascalCase.

## 0.1.3 (2026-10-26)

- **ER tables closer to the design:** names in the sans font (13 px, bold for a primary key), types in grey mono, thin rules between rows, a key column of the same width in every table, a name pill with a hard shadow, tables at least 240 px wide, tables in one grid row lined up at their tops, and bigger crow's feet and bars (2 px lines).
- **Example:** `examples/delivery-er-illustrated.spec.json`, the design's food delivery schema in an `at` grid.

## 0.1.2 (2026-10-26)

- **ER tables look like the design's:** key flags are chips before the column name (`PK` amber, `FK` blue, `UQ` violet), the type is on the right with `?` when the column may be empty, rows are 28 px, and `"style": "illustrated"` gives the tall tinted header with the name in a pill and a large detailed icon. Tables are spaced 150 px apart so that two marks and a label fit on a line. Both the HTML and the `.drawio` output draw the chips; `flow.py import` reads them back.
- **Author kit draws ER tables** (`NodeOptions(rows=...)`, `Shape.TABLE`, `card=True` for the illustrated header), refuses node ids that the canvas keeps for lines (`e1`, `e2`, ...), and exposes `CONTENT_TOP_PX`, the first y below the title.
- **Skills:** the ER skill explains the style, chips and the `at` grid; the author skill explains tables, the id rule, `CONTENT_TOP_PX` and the Chrome fallback for looking at the picture.

Not verified: the new tables in the draw.io editor; a chip's width in draw.io (it follows the font there).

## 0.1.1 (2026-10-26)

- **Author skill:** in the illustrated style every work step (process, subprocess, document) is now a card, tinted by its lane, with an icon chosen by the noun and one detail line, as in the design's Food delivery example. Before, the skill asked for cards on a few steps only, so illustrated charts looked like plain ones.
- **Author skill:** how to fold a long chain inside one lane, and how to order several return lines into one node (channel rows, arrival points, connectors for very long lines).

## 0.1.0 (2026-10-26)

First release.

- **Plugin** `flow` for Claude Code with 24 skills: flowchart, sequence, ER, architecture, cloud, C4, state, BPMN, use case, class, DFD, screen flow, org chart, mind map, Gantt, roadmap, Kanban, layers, wireframe, concept, import-drawio, edit-drawio, doctor, and `author`.
- **Two outputs** from one set of positions: an animated HTML page and a native `.drawio` file. Plain and illustrated styles; 40 flat and 97 detailed icons; custom icons checked before use.
- **Automatic layout** for small diagrams (layered engine, tidy trees, timelines, boards), with swimlanes drawn as in the design, a route search for blocked lines, and folding of long charts into bands.
- **Author path** (`/flow:author`, `flowlib/author.py`): for large or dense diagrams Claude lays the diagram out itself in its own script, using a kit that keeps the design, and looks at its own picture.
- **Checks:** overlaps, lines through boxes, covered labels and captions, overlapping lines, crossings, text that does not fit.
- **Editing:** `flow.py import` and `flow.py edit` for existing `.drawio` files.
- **Benchmarks:** 25 test briefs and a checker; the first blind agent runs on level C briefs (`benchmarks/results/`).
- **Install notes** in `INSTALL.md`, including an untested route for Google Antigravity (`plugins/flow/plugin.json`).

Not verified: the draw.io editor, claude.ai, Cowork, Windows and Antigravity; runs of the author path for the other types; averages over several runs.
