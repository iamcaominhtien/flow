# Changelog

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
