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

A scene is plain geometry in pixels, independent of HTML and draw.io:

```json
{
  "size": [1400, 900],
  "frames": [{"id": "lane1", "x": 0, "y": 80, "w": 1400, "h": 220, "label": "Customer", "tone": "blue"}],
  "nodes":  [{"id": "pay", "shape": "process", "x": 540, "y": 120, "w": 280, "h": 92,
              "text": ["Pay by card"], "tone": "amber", "icon": "card"}],
  "edges":  [{"id": "e1", "from": "start", "to": "pay", "role": "main",
              "points": [[680, 60], [680, 120]], "label": null, "arrow": "end"}]
}
```

The scene is also the thing the **check** reads and the thing tests compare against (§8). A user can keep or edit it: it is the "intermediate file" that makes editing existing diagrams possible later.

## 6. The two renderers

### HTML / SVG

- A single self-contained `.html`: absolutely positioned boxes and inline SVG for shapes, icons and lines. No JavaScript is needed.
- The two animation tiers are CSS (`stroke-dashoffset` keyframes): main path blue 4 px fast, event stream violet 2 px slow. This is what the canvas already does.
- The three themes of the foundation page (Pastel infographic, Technical clean, Midnight) become sets of CSS variables, so a diagram can switch theme without a new layout.
- The existing generators in [`docs/design/source/generators`](../design/source/generators) are the starting point: they already contain the shape SVGs, tones and icons. What changes is that they read a scene instead of hand-written coordinates.

### draw.io

- Each node becomes an `mxCell` with a style string from the foundation page (the "Building blocks" table already lists them); each edge becomes an `mxCell` with `edgeStyle=orthogonalEdgeStyle` and the scene's waypoints as `<Array as="points">`. Frames become containers.
- Animation uses the per-edge style from the first test: main `strokeWidth=3;flowAnimation=1;flowAnimationDuration=500`, events `strokeWidth=1;flowAnimation=1;flowAnimationDuration=1500`.
- Icons are written as `shape=image` with an inline SVG data URI built from the same icon paths. **Not tested yet**: how that looks in the editor and in PNG/PDF export.
- The output is plain XML written by a script, never by Claude, so the `.drawio` is valid by construction. If the optional draw.io plugin is installed, Claude can offer to export PNG/SVG/PDF with it.
- Line weights: the same numbers as the HTML (2 px ordinary, 4 px main path, 2 px event stream). The earlier draw.io recipe (3 and 1) is dropped unless the draw.io test shows a problem.

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
├── skills/
│   ├── flowchart/SKILL.md        # when to use, how to write the spec, the loop
│   ├── sequence/SKILL.md  ...    # one per type, started from the design pages
│   └── doctor/SKILL.md
├── scripts/
│   └── flow.py                   # CLI: build | check | schema | doctor
└── flowlib/                      # Python package, standard library only
    ├── theme.json                # tones, line roles, sizes, spacing (from the design)
    ├── icons.json                # the icon set (already in the repo)
    ├── spec.py                   # load and validate
    ├── layout/                   # layered.py, lanes.py, timeline.py, tables.py, tree.py
    ├── scene.py                  # scene + overrides
    ├── icons.py                  # library lookup, inline SVG validation
    ├── render_html.py
    ├── render_drawio.py
    ├── check.py
    └── types/                    # per-type vocabulary: kinds, roles, defaults
tests/                            # development only, not part of the plugin
```

Each skill is short: it tells Claude when it applies, which fields the spec has for that type (copied from the design page), then the loop *write spec → `flow.py build` → read the report → fix → show the result*. The long rules stay in the skill's reference file and are read only when needed, which keeps the context cost of an installed plugin low.

Command line, for example: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build spec.json --format html,drawio --out ./diagrams`. The skills pre-approve exactly that command pattern, so users are not asked for permission on every run.

## 9. Testing

- **Golden files:** for each design example, a spec plus the expected scene. A test builds the scene and compares it. Layout changes show up as diffs a person reviews.
- **Against the design:** for each canvas example, build the same content from a spec, render HTML, screenshot it (development machine only) and compare with the design image by eye. The aim is "the same look", not pixel equality.
- **draw.io:** open each generated `.drawio` in the draw.io viewer (as in the earlier animation test) and check it loads with no errors.
- Unit tests for the validator and the checks. `pytest` is a development dependency only.

## 10. Risks and open questions

1. **Layout quality is the project.** A home-made layered layout will not match a good hand layout on large graphs. Mitigation: start with small and medium graphs, expose hints, report honestly when the result is poor. Not planned: calling Graphviz, because it is not guaranteed to be installed.
2. **Python is a requirement.** Claude Code does not ship it. `doctor` checks and says what to install if it is missing. (Not verified: on Windows the command may be `python` or `py`.)
3. **Text measurement** is an approximation; wide scripts and long labels will sometimes overflow.
4. **Line weights:** the same numbers in both outputs (§6); to be confirmed when the draw.io renderer is tried.
5. **Icons in draw.io** (inline SVG images) are untested for editing and export.
6. **Claude.ai and Cowork:** skills run there, but whether the scripts can run is not verified. If they cannot, the plugin is for Claude Code only until that changes.
7. **Icons for any subject.** The plugin ships the sets drawn for the design (simple line icons and 73 detailed ones). For anything else Claude draws the icon itself; see §6a.
8. **Editing existing `.drawio` files** is not designed (deferred). The scene is the likely route: parse a file back into a scene, change it, render again.
9. **Cross-type links** (a node on a C4 diagram that points to a flowchart) have no scheme yet.

## 11. Build order

| Step | What | Done when |
| --- | --- | --- |
| A | `theme.json`, `icons.json`, scene format, HTML renderer for **hand-written scenes** | The "Place an order" scene renders like the canvas flowchart |
| B | Spec, validator, layered layout, `flow.py build`, check; the `flowchart` skill | A brief produces a flowchart HTML that passes the check, installed from the marketplace |
| C | draw.io renderer | The same scene opens in draw.io with matching positions, animation included |
| D | Second type from a different family (sequence or ER) to test that the scene and renderers are not flowchart-shaped | Two families work with no change to the renderers |
| E | Remaining types, family by family; illustrated style | Each type passes the design's own examples |
| F | Editing existing files, publishing to the plugin directory | Later |

Steps A and C are cheap because the renderers only draw geometry; B is where the real uncertainty is, so it comes with a plan to stop and review after the first working flowchart.

## 12. Decisions taken

1. **Flowchart first** proves the pipeline (step B).
2. **Python is required.** Fixing a diagram has three levels, the last being a direct HTML edit (§6).
3. **Line weights:** the same in both outputs (2, 4, 2), checked in draw.io later.
4. **Both styles are supported.** Plain works for any subject; illustrated uses library icons and icons Claude draws (§6a). Plain ships first, illustrated follows once the flowchart works.
5. **Files kept:** the spec, the overrides and the scene sit beside the outputs (`diagram.spec.json`, `diagram.scene.json`, `diagram.html`, `diagram.drawio`) so a diagram can be rebuilt.
