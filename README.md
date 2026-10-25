# Flow

**A set of AI plugins for drawing diagrams, as animated HTML/SVG or as editable [draw.io](https://www.drawio.com/) files.**

Describe a diagram in plain language and let AI draw it for you: flowcharts, sequence diagrams, architecture diagrams, ER diagrams, and more, as a web page you can view and share, or as a draw.io file you can keep editing.

> 🚧 **Status: early development.** The project has just started. APIs, structure, and features described below will change.

## Why Flow?

Drawing diagrams by hand is slow, and AI-generated diagrams are often hard to edit afterward. Flow aims to bridge the two. Every diagram is described once, laid out once, and drawn in two ways: HTML/SVG (viewable anywhere, with animation) and native draw.io (editable in the editor).

## Goals

- **Text to diagram**: generate diagrams from a natural-language description.
- **Two outputs, one layout**: HTML/SVG first, then draw.io, both drawn from the same description and positions so they do not drift apart.
- **Edit with AI**: modify existing diagrams ("add a cache between the API and the database").
- **Native output**: produce standard draw.io XML (`.drawio`) so results stay fully editable.
- **Pluggable**: a collection of focused plugins, each handling one kind of diagram or task.
- **One consistent look**: a shared theme (colours, fonts, icons, line styles) for every diagram type, in a plain and an illustrated style.

## Design system

The visual language is designed first, on a canvas of sample artboards, before any plugin code is written. The canvas currently lives outside this repository; the decisions it holds are written up in full, with pictures, in the **[design document](docs/design/README.md)**, and summarised here.

- **Foundation**: a flat pastel palette with ink outlines, Inter and JetBrains Mono, 12 px node radius, 2 px strokes.
- **Icons**: a flat set of 98 icons and a detailed set that has a twin for every one of them (shaded, with highlights and accents).
- **Line roles**: next step, yes / success, no / failure, return (dashed), one animated main path, and a slower animated data stream.
- **Two styles**: *plain* (shapes with text, optional small icon; the default) and *illustrated* (cards with a name pill, one line of explanation and a large icon, tinted by swimlane). Styles can be mixed in one diagram.
- **Per-type notation**: each diagram type gets its own rules page, patterns and complete examples, so a plugin can rely on written conventions instead of guessing.

| Diagram type | Design status |
| --- | --- |
| Screen flow | Done: rules, fidelity levels, conditions, tabs, overlays, devices, full examples |
| Flowchart | Done: rules, patterns, plain and illustrated examples, swimlane, complete delivery flow |
| Sequence | Done: rules, message kinds, fragments, basic example, complete delivery flow (plain and illustrated) |
| ER | Done: rules, notation, relationship patterns, blog example, complete delivery schema (plain and illustrated), splitting by domain |
| Architecture | Done: rules, notation, building-block patterns, web app example, complete delivery system, large streaming platform (plain and illustrated) |
| Explainer | Done: rules, four shapes (layers, tree, comparison, concept) and a complete card-payment explainer |
| Planning (Gantt, org chart, mind map, Kanban, roadmap) | Done: rules and an example of each; org chart and mind map also in an illustrated style, plus a large four-level mind map |
| UML (state machine, use case, class) | Done: rules and an example of each; use case also in an illustrated style |
| Wireframe | Done: rules, annotated phone flow, annotated desktop screen, responsive set, state set |
| BPMN | Done: rules, notation, basic example, advanced features, three-pool delivery, complex order-to-delivery case |
| C4 | Done: rules, level 1 context, level 2 containers, level 3 components (one delivery platform at three zooms) |
| Cloud | Done: rules, basic one-VPC app, delivery platform on two zones, network joining offices to the cloud |
| DFD | Done: rules, notation with forbidden connections, levels 0, 1 and 2 of the delivery system, plain and illustrated |
| Editing existing .drawio files | Not designed; a first import exists (see the [plugin design](docs/plugin/design.md)) |

Cross-type review (done): the automatic overlap check covers every board; the lint tool now also knows the Gantt and swimlane frames; the same thing now has the same icon and tint everywhere (Payment provider, Orders database).

Animation in draw.io (checked in the draw.io viewer code, and by rendering a file with two edges): each edge has its own `flowAnimation=1`, `flowAnimationDuration` (default 500), `flowAnimationTimingFunction` and `flowAnimationDirection`. So the two tiers of the design work: main route `strokeWidth=3;flowAnimation=1;flowAnimationDuration=500`, event stream `strokeWidth=1;flowAnimation=1;flowAnimationDuration=1500`. The viewer adds the keyframes at render time and its SVG export writes them into the file. Still not tested: opening an exported SVG file on its own, and the PNG/PDF export (which cannot animate).

## Supported diagram types

Flow aims to cover **nearly every common diagram type**, grouped into 8 categories. Each category is delivered as a plugin (or a set of plugins).

| Category | Diagram types | Status |
| --- | --- | --- |
| Process & business | Flowchart, Swimlane / cross-functional, BPMN, User flow | Built (BPMN as a look, not the full standard) |
| UML behavior | Sequence, Use case, Activity, State machine | Built; activity is drawn with the flowchart skill |
| Structure & data | ER diagram, Class diagram, Data flow diagram (DFD) | Built |
| Architecture & infrastructure | Architecture, C4 model, Cloud (AWS / GCP / Azure), Network, Deployment | Built (network and deployment use the architecture or cloud skill; no provider icons) |
| Planning & management | Gantt, Org chart, Mind map, Roadmap / Kanban | Built |
| UI design | Wireframe / mockup | Built (a simple stack of boxes) |
| Explainer / infographic | Layered flow (icon-based tiers/lanes), Tree / hierarchy, Side-by-side comparison, Concept illustration | Layers, tree and comparison (through Kanban) built; concept illustration not built |
| Editing | Update or restyle existing `.drawio` files | Import only (best effort) |

## Getting started

Flow installs as a Claude Code plugin from this repository. Flow writes `.drawio` files itself; the official draw.io plugin is optional and only useful for exporting them to PNG, SVG or PDF. To install Flow alone:

```
/plugin marketplace add iamcaominhtien/flow
/plugin install flow@flow
```

To export to PNG, SVG or PDF, also run `/plugin marketplace add jgraph/drawio-mcp` and `/plugin install drawio@drawio`. Then run the `doctor` skill (`/flow:doctor`) to check the install. Then ask for a flowchart, for example `/flow:flowchart how a customer pays and gets an order delivered`. Claude writes a short spec; a script places the boxes, routes the lines, checks the result and writes an animated HTML page and a `.drawio` file next to the spec. Today the plugin has these skills, all in the plain style:

| Skill | Draws |
| --- | --- |
| `/flow:flowchart` | Flowcharts, top to bottom or left to right, with swimlanes and an overrides file for fixes |
| `/flow:sequence` | Sequence diagrams: activation bars, fragments, notes, create and destroy |
| `/flow:er` | ER diagrams: tables, keys, crow's-foot cardinality |
| `/flow:architecture`, `/flow:cloud`, `/flow:c4` | Components in nested zones; cloud resources; C4 elements |
| `/flow:state`, `/flow:bpmn`, `/flow:usecase`, `/flow:class`, `/flow:dfd`, `/flow:screen-flow` | State, BPMN-style, use case, class, data flow and screen flow diagrams |
| `/flow:org-chart`, `/flow:mind-map` | Trees with a tidy layout (top down; left to right) |
| `/flow:gantt`, `/flow:roadmap` | Time axis in named periods; lanes of items |
| `/flow:kanban`, `/flow:layers`, `/flow:wireframe` | Columns of cards (also a comparison); stacked bands; low-fidelity screens |
| `/flow:import-drawio` | Reads an existing `.drawio` file into a scene (best effort) |
| `/flow:doctor` | Checks the install |

You can also add your own icons: Claude writes `icons.local.json` next to the spec, and the build checks it before use. The illustrated style is partial: add `"style": "illustrated"` and boxes with an icon become cards (large icon on a disc, name pill, detail line) in the flowchart, architecture, cloud, C4, BPMN, use case, DFD, screen flow, Kanban and layers skills, in both outputs. The detailed 64 px icons and the per-type illustrated notation of the design pages are not built. Not built: BPMN event types and pools with message flow checks, an explainer "concept" shape, and editing a `.drawio` file in place. The types above are simpler than the design pages describe (for example no device frames, no provider icons, no dates in the Gantt chart). Nothing has been tested in the draw.io editor, in claude.ai or in Cowork, or on Windows.

## Roadmap

- [x] Design foundation, icon sets, Screen flow, Flowchart, Sequence, ER, Architecture, Explainer, Planning, UML, Wireframe, BPMN, C4, Cloud and DFD notation
- [x] Cross-type review and a first test of draw.io animated edges
- [x] Write the [design document](docs/design/README.md) (18 pages, 104 pictures)
- [ ] Design how plugins edit existing `.drawio` files
- [ ] Test an exported SVG with animated edges on its own
- [x] Plugin skeleton: marketplace, `flow` plugin, `doctor` skill, installs locally; the draw.io plugin is optional
- [x] Write the [plugin design](docs/plugin/design.md) (pipeline, spec, layout, renderers, checks)
- [x] Shared library: diagram description (JSON), one layout step, HTML/SVG renderer, checks, and the first skill (flowchart, top to bottom)
- [x] draw.io renderer from the same description (checked in the draw.io viewer; not yet in the editor)
- [x] Generate valid draw.io XML from a text prompt (flowchart, sequence, ER, architecture, state)
- [x] First plugins: flowchart, sequence, ER, architecture, state
- [x] Expand to the remaining categories above (simplified; see the table)
- [ ] Support editing existing `.drawio` files (import exists; editing in place does not)
- [ ] Documentation and examples

## Contributing

The project is just getting started. Ideas and issues are welcome; contribution guidelines will follow.

Python code is checked with [ruff](https://docs.astral.sh/ruff/) and tested with pytest (`pip install ruff pytest`; run `python3 -m pytest`; settings in `pyproject.toml`; the `docs/` folder is skipped):

```
ruff format .
ruff check .
```

A Claude Code hook in `.claude/settings.json` runs both on every Python file Claude edits, and reports any error ruff cannot fix.

## License

Released under the [MIT License](LICENSE).
