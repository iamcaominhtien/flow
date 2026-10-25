# Plugin design: from a brief to a diagram

Status: **proposal, for review.** Nothing in this page is built yet. It describes how the Flow plugin turns a sentence like "draw the order flow" into an HTML/SVG diagram and a draw.io file, using the rules in [`docs/design`](../design/README.md).

## 1. What is already decided

| Decision | Choice |
| --- | --- |
| Distribution | This repository is the marketplace; it holds one plugin, `flow`, with one skill per diagram type |
| Outputs | HTML/SVG first (animated, viewable anywhere), then draw.io (`.drawio`, editable). The draw.io plugin is optional |
| One source for both | One description, one layout, two renderers, so the outputs cannot drift apart |
| Language | Python, standard library only (the plugin install runs no `pip install`) |
| Lint | ruff, with a Claude Code hook (already in the repo) |

## 2. The idea in one picture

```
 brief (words)
     │  Claude, guided by the type's skill
     ▼
 SPEC  ── JSON: nodes, edges, groups, style; no coordinates needed
     │  scripts/flow.py build
     ▼
 LAYOUT ── puts every node and edge on a grid, using the spacing rules
     ▼
 SCENE ─── plain geometry: boxes, routed lines, labels, in pixels
     ├──► render_html  → diagram.html (SVG + CSS animation)
     ├──► render_drawio → diagram.drawio (mxfile XML)
     └──► check ──────→ report: overlaps, clipped text, crossings, tight gaps
                          │
                          └─ Claude reads the report, edits the spec, builds again
```

**Claude writes the meaning; Python does the geometry.** Claude decides what the nodes and edges are and writes them as a spec. Python decides where they go, how lines run and what colour they get. Reasons:

- Sizes, gaps, colours and icons come from the rules, so two diagrams of the same content look the same. Asking a model to place 40 boxes by hand gives different results each run.
- A model that has to write coordinates or XML also has to get them right. A model that writes a short spec only has to get the content right.
- The check can run on the scene and tell Claude exactly what to fix.

The spec may carry **hints** (`"lane"`, `"rank"`, `"side"`, or an exact `"at": [x, y]`) when Claude or the user wants to override the layout.

## 3. The spec

One format for all types, with a small common core and a `type` that selects the rest. Example, a flowchart:

```json
{
  "type": "flowchart",
  "style": "plain",
  "title": "Place an order",
  "direction": "down",
  "nodes": [
    {"id": "start", "kind": "terminator", "text": "Customer opens the app"},
    {"id": "pay",   "kind": "process",    "text": "Pay by card", "icon": "card", "tone": "amber"},
    {"id": "ok",    "kind": "decision",   "text": "Payment accepted?"},
    {"id": "done",  "kind": "terminator", "text": "Order confirmed"},
    {"id": "fail",  "kind": "fail",       "text": "Show error"}
  ],
  "edges": [
    {"from": "start", "to": "pay", "role": "main"},
    {"from": "pay",   "to": "ok"},
    {"from": "ok",    "to": "done", "role": "yes", "label": "Yes"},
    {"from": "ok",    "to": "fail", "role": "no",  "label": "No"},
    {"from": "fail",  "to": "pay",  "role": "back", "label": "Retry"}
  ]
}
```

Common core: `type`, `style` (`plain` or `illustrated`), `title`, `nodes[]` (`id`, `kind`, `text`, optional `icon`, `tone`, `group`, `desc`), `edges[]` (`from`, `to`, `role`, optional `label`), `groups[]` (lanes, zones, frames). The `kind` values, `role` values and extra fields per type are exactly the vocabulary in each type's *What a plugin can rely on* section, so the spec schema is written from the design pages, not invented. The script **validates** the spec against a schema before building and returns readable errors ("edge 3 points to `payy`; did you mean `pay`?").

Types that are not node-and-edge graphs (sequence, ER, Gantt, wireframe) use the same envelope with their own bodies: `participants[]` and `messages[]`, `tables[]` and `relations[]`, `tasks[]`, `screens[]`.

## 4. Layout

Layout is the hard part, and it is the same work for both outputs. One engine per **family**, not per type:

| Family | Types | Method |
| --- | --- | --- |
| Layered graph | Flowchart, screen flow, BPMN, DFD, architecture, C4, UML state | Rank by longest path, place the main path straight, branches to the side, return arrows outside the flow (the flowchart rule, §4 of its page) |
| Lanes / grids | Swimlane, cloud zones, planning boards | Fixed rows and columns; nodes snap to a cell |
| Timeline | Sequence, Gantt | Time or order on one axis, participants or tasks on the other; arithmetic, no search |
| Tables | ER | Tables on a grid; relations routed between sides |
| Tree | Org chart, mind map, hierarchy | Tidy-tree layout |

Every engine takes its numbers from one `theme` file (gaps of 56/70 px for flowcharts, 240 px between boxes joined by a labelled line, box sizes), so the rules live in one place.

**Lines** are routed as orthogonal polylines with explicit waypoints, and labels get a fixed position on the line (middle of the longest segment, with room for the 90 px label rule). Crossings are minimised by node order within a rank, not guaranteed zero; the check reports the count.

**Text size** cannot be measured without a font. The layout uses a width table per character class (a small table for Inter and JetBrains Mono, with a safety margin for wide Vietnamese characters), wraps text to the node width and grows the node height. This is an approximation, and the check flags text that probably does not fit.

**If layout fails** (cycles, too many nodes in one rank) it still produces a scene, marks the problem in the report and does not crash.

## 5. The scene

A scene is plain geometry in pixels, independent of HTML and draw.io. `x` and `y` are the top-left corner of a node or frame; an edge carries its own routed points and the position of its label:

```json
{
  "size": [1400, 900],
  "title": "Place an order",
  "frames": [{"id": "lane1", "x": 0, "y": 80, "width": 1400, "height": 220, "label": "Customer", "tone": "blue"}],
  "nodes":  [{"id": "pay", "shape": "process", "x": 540, "y": 120, "width": 280, "height": 92,
              "text": ["Pay by card"], "tone": "amber", "icon": "card", "number": "2"}],
  "edges":  [{"id": "e1", "from": "start", "to": "pay", "role": "main",
              "points": [[680, 60], [680, 120]],
              "label": {"text": "Pay", "at": [700, 90], "kind": "plain"}, "arrow": "end"}]
}
```

`shape`, `role`, `tone`, `icon` and label `kind` are checked against `theme.json` and `icons.json`; `scene.validate` returns every problem at once.

The scene is also the thing the **check** reads and the thing tests compare against (§8). A user can keep or edit it: it is the "intermediate file" that makes editing existing diagrams possible later.

## 6. The two renderers

### HTML / SVG

- A single self-contained `.html`: absolutely positioned boxes and inline SVG for shapes, icons and lines. No JavaScript is needed.
- The two animation tiers are CSS (`stroke-dashoffset` keyframes): main path blue 4 px fast, event stream violet 2 px slow. This is what the canvas already does.
- The three themes of the foundation page (Pastel infographic, Technical clean, Midnight) become sets of CSS variables, so a diagram can switch theme without a new layout.
- The existing generators in [`docs/design/source/generators`](../design/source/generators) are the starting point: they already contain the shape SVGs, tones and icons. What changes is that they read a scene instead of hand-written coordinates.

### draw.io

Built in `flowlib/render_drawio.py`. The file is an uncompressed `mxfile`, written by a script and never by Claude.

- **Nodes** are vertices with the draw.io shape closest to the HTML one (`rounded` with `arcSize`, `rhombus`, `parallelogram`, `hexagon`, `process`, `document`, `ellipse`), with the same fill, stroke (2 px) and font as the page. Text keeps the line breaks the layout chose.
- **Edges** keep the routed points of the scene as waypoints, with no `edgeStyle`, so the line is drawn exactly as routed. Each edge names its source and target nodes and fixes the exit and entry points (`exitX`, `entryX`...), so it stays attached when a node is moved (the waypoints do not follow). An edge also carries its end points, so a hand-written scene without node names still draws.
- **Labels** are edge labels placed at their position along the line, with an offset for labels beside a vertical line. They are plain text on a coloured background: draw.io has no rounded chip for an edge label.
- **Icons** are small image cells inside their node, as SVG data URIs, so they move with it. The URI has no `;base64`, because draw.io splits styles at semicolons.
- **Line weights** are the same as the page: 2 px for ordinary lines, 4 px for the main path. Dash patterns are converted to multiples of the line width, which is how draw.io reads them.
- **Animation** uses `flowAnimation=1`. draw.io spends `flowAnimationDuration` ms per 16 px of dash cycle, so the duration is computed from the page's speed (one cycle in 0.7 s for the main path, 1.8 s for events) and the two outputs move at the same speed.

Checked by loading the files in draw.io's own viewer script (`viewer-static.min.js`, the same rendering code as the editor) in Chromium: shapes, waypoints, labels, icons, arrowheads and the dash patterns match the page, and the animated edges carry the computed animation style. Not checked: opening the file in the draw.io editor or desktop app, PNG/PDF export (which cannot animate), and what happens when the fonts Inter and JetBrains Mono are missing.

### 6a. Icons: library first, drawn on demand

A real subject (a bank, a hospital, a game) will need icons the library does not have. Drawing one is not hard for Claude: the plain icons are about 150 characters of SVG on a 24 px grid, and the detailed ones about 800 characters on a 64 px grid (the design already has 73). So the rule is:

- A node's `icon` is a **name** from the library, or an **inline SVG** that Claude wrote following the icon rules (grid, outline weight, the three tones, highlight, ground shadow).
- The script **validates** inline SVG before use: allowed elements only (no scripts, no external links, no images), the right viewBox, a size limit. This also keeps the HTML safe.
- Drawn icons are saved in `icons.local.json` beside the diagram, so the same subject keeps the same icon across diagrams and rebuilds.
- Nothing can confirm that a drawn icon looks right except looking at it. The report lists the new icons so the user can check them, and Claude can swap one for a library icon or for no icon.

Risks: icons drawn in different sessions may differ in style, and detailed icons cost more tokens than plain ones. The plain style needs only the simple icons; both styles are supported.

### When the code is not enough: three levels of fixing

Automatic layout will not always give a good result. Claude fixes a diagram at the lowest level that works:

1. **Spec hints** (`rank`, `lane`, `side`, shorter text). Both outputs stay in step, because they are rebuilt.
2. **Scene overrides**: a small `overrides` list kept beside the spec (move node `pay` to x, y; route edge `e3` through these points). It is applied after layout, so HTML and draw.io both get the fix and the diagram can still be rebuilt.
3. **Edit the HTML directly.** Always allowed as the last resort. It cannot be carried into the draw.io file or rebuilt from the spec, so the file is marked `hand-edited`, a rebuild asks before overwriting it, and the Python check does not cover it.

Python is required; there is no script-free mode.

## 7. Checks

Today the checks are Node and screenshot scripts (`lint.js`, `clipcheck.js`). The plugin cannot rely on a browser being present, so the checks are rewritten in Python and run on the **scene**, with no rendering:

| Check | Meaning |
| --- | --- |
| Overlap | Two nodes, or a node and a label, share area |
| Border label | Text or a small shape straddles a box edge (the existing `data-lint` rule) |
| Clipping | Anything outside the frame or the canvas |
| Spacing | Gaps smaller than the type's minimum |
| Crossings | Count of line crossings, listed |
| Fit | Text that probably does not fit its node |
| Balance | Type rules that can be tested on data (for a DFD: no entity-to-entity flow, every process has input and output) |

Output is a short list with the ids involved, so Claude can edit the spec (`"rank"`, `"side"`, shorter text) and rebuild. The loop stops after a few rounds and reports what is left. The browser-based screenshot check stays a **development tool** for this repo, used to compare the new renderer against the canvas.

## 8. Layout of the code

```
plugins/flow/
├── .claude-plugin/plugin.json
├── skills/                       # doctor, flowchart, sequence, er, architecture, state, import-drawio
├── scripts/
│   ├── flow.py                   # CLI: build | check | render | import
│   └── doctor.py
└── flowlib/                      # Python package, standard library only
    ├── theme.json, icons.json    # design tokens and the icon library
    ├── model.py, scene.py        # scene dataclasses; scene JSON read and write
    ├── reader.py, spec.py        # spec reading helpers; the flowchart-family spec
    ├── diagrams/                 # one module per type: flowchart, er, architecture, state, sequence
    ├── layered.py, placement.py, sizing.py, routing.py, zones.py, transpose.py
    ├── overrides.py, canvas.py, check.py, build.py
    ├── shapes.py, markup.py, render_html.py, html_nodes.py, html_lines.py
    ├── render_drawio.py, drawio_common.py, drawio_lines.py
    ├── icon_check.py             # custom icon validation
    └── import_drawio.py          # .drawio to scene
tests/                            # development only, not part of the plugin
```

Each skill is short: it tells Claude when it applies, which fields the spec has for that type (copied from the design page), then the loop *write spec → `flow.py build` → read the report → fix → show the result*. The long rules stay in the skill's reference file and are read only when needed, which keeps the context cost of an installed plugin low.

Command line, for example: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/name.spec.json` (writes the scene, the HTML and the draw.io file next to the spec). The skills pre-approve exactly that command pattern, so users are not asked for permission on every run.

## 9. Testing

- **Golden files:** for each design example, a spec plus the expected scene. A test builds the scene and compares it. Layout changes show up as diffs a person reviews.
- **Against the design:** for each canvas example, build the same content from a spec, render HTML, screenshot it (development machine only) and compare with the design image by eye. The aim is "the same look", not pixel equality.
- **draw.io:** open each generated `.drawio` in the draw.io viewer (as in the earlier animation test) and check it loads with no errors.
- Unit tests for the validator and the checks. `pytest` is a development dependency only.

## 10. Risks and open questions

1. **Layout quality is the project.** A home-made layered layout will not match a good hand layout on large graphs. Mitigation: start with small and medium graphs, expose hints, report honestly when the result is poor. Not planned: calling Graphviz, because it is not guaranteed to be installed.
2. **Python is a requirement.** Claude Code does not ship it. `doctor` checks and says what to install if it is missing. (Not verified: on Windows the command may be `python` or `py`.)
3. **Text measurement** is an approximation; wide scripts and long labels will sometimes overflow.
4. **Line weights:** the same numbers in both outputs (§6); confirmed by eye in the draw.io viewer.
5. **Icons in draw.io** (inline SVG images) draw in the viewer; editing them in the editor and exporting to PNG/PDF are untested.
6. **Claude.ai and Cowork:** skills run there, but whether the scripts can run is not verified. If they cannot, the plugin is for Claude Code only until that changes.
7. **Icons for any subject.** The plugin ships the sets drawn for the design (simple line icons and 73 detailed ones). For anything else Claude draws the icon itself; see §6a.
8. **Editing existing `.drawio` files:** a first version reads a file into a scene (`flow.py import`). It is best effort: icons, free text and automatically routed bends are lost, and nothing changes the original file. Changing the result goes through the overrides file. Editing a file in place is not designed.
9. **Cross-type links** (a node on a C4 diagram that points to a flowchart) have no scheme yet.

## 11. Build order

| Step | What | State |
| --- | --- | --- |
| A | `theme.json`, `icons.json`, scene format, HTML renderer for hand-written scenes | Done |
| B | Spec, validator, layered layout, `flow.py build`, check; the `flowchart` skill; swimlanes, left to right, overrides, back-edge routing | Done |
| C | draw.io renderer | Done; checked in the draw.io viewer, not in the editor |
| D | Second family: sequence diagram | Done; the scene and renderers needed new frame, bar and symbol-head support but no rewrite |
| E | Remaining types, family by family | Done in a simplified form: ER, architecture, cloud, C4, state, BPMN, use case, class, DFD, screen flow (all on the layered engine), org chart and mind map (tidy tree), Gantt and roadmap (timeline), Kanban, layers and wireframe (boards). Not built: per-type illustrated notation and the concept explainer. A first illustrated style exists: `style: illustrated` turns boxes with an icon into cards (see decision 11) |
| F | Editing existing files, publishing | Import done (best effort). Editing in place and publishing to a directory: not done |

Types that fit the layered engine are declared as data in `diagrams/catalog.py` (words, kinds and line styles) and read by `diagrams/graph.py`. Trees use `tidy.py`, because the layered engine merges the buses of different parents. Gantt and roadmap are in `diagrams/timeline.py`, and Kanban, layers and wireframe in `diagrams/boards.py`; both build the scene directly.

## 12. Decisions taken

1. **Flowchart first** proves the pipeline (step B).
2. **Python is required.** Fixing a diagram has three levels, the last being a direct HTML edit (§6).
3. **Line weights:** the same in both outputs (2, 4, 2), checked in draw.io later.
4. **Both styles are supported.** Plain works for any subject; illustrated uses library icons and icons Claude draws (§6a). Plain ships first, illustrated follows once the flowchart works.
5. **Files kept:** the spec, the overrides and the scene sit beside the outputs (`diagram.spec.json`, `diagram.scene.json`, `diagram.html`, `diagram.drawio`) so a diagram can be rebuilt.
6. **Custom icons are names, not inline SVG.** `icons.local.json` beside the spec maps a name to the inner markup of a 24 px line icon; the build checks it (allow-listed elements and attributes, numbers inside the grid, size limits) and refuses anything else. The detailed 64 px style is not supported yet. The built-in library has 40 icons.
7. **One engine for the graph family.** Flowchart, ER, architecture and state share ranking, placement, routing and zones. Each type is a parser in `flowlib/diagrams/` plus a skill.
8. **Marks keep their own size.** Start, end, connector and actor nodes are not stretched to the width of their column; a stretched circle would be an ellipse in draw.io.
9. **Graph types are data.** A new type of the graph family is a `GraphType` value (words, kinds, line styles), not a new parser. Unknown kinds and styles are refused with the list of valid ones.
10. **Dates are not read.** A timeline names its own periods (`W1`, `Q2`) and bars use whole periods.
11. **Illustrated style is a spec switch, not a second renderer.** `style: illustrated` marks each box that has an icon as a `card` node; the sizing step gives it a card size and both renderers draw a disc, a pill and a detail line. A card uses the detailed 64 px icon when the name has one (97 drawings taken from the design source, repaired where their attributes were duplicated), else the flat icon enlarged on a tinted disc. A detailed-only name used in a plain diagram is drawn small in its detailed form. Custom icons are still flat 24 px.
