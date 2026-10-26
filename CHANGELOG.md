# Changelog

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
