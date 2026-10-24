# Flow

**A set of AI plugins for creating and editing diagrams in [draw.io](https://www.drawio.com/) (diagrams.net).**

Describe a diagram in plain language and let AI draw it for you: flowcharts, sequence diagrams, architecture diagrams, ER diagrams, and more, all as editable draw.io files.

> 🚧 **Status: early development.** The project has just started. APIs, structure, and features described below will change.

## Why Flow?

Drawing diagrams by hand is slow, and AI-generated diagrams are often hard to edit afterward. Flow aims to bridge the two by letting AI produce and modify native draw.io diagrams that you can keep refining in the editor.

## Goals

- **Text to diagram**: generate draw.io diagrams from a natural-language description.
- **Edit with AI**: modify existing diagrams ("add a cache between the API and the database").
- **Native output**: produce standard draw.io XML (`.drawio`) so results stay fully editable.
- **Pluggable**: a collection of focused plugins, each handling one kind of diagram or task.
- **One consistent look**: a shared theme (colours, fonts, icons, line styles) for every diagram type, in a plain and an illustrated style.

## Design system

The visual language is designed first, on a canvas of sample artboards, before any plugin code is written. The canvas currently lives outside this repository; the decisions it holds are summarised here.

- **Foundation**: a flat pastel palette with ink outlines, Inter and JetBrains Mono, 12 px node radius, 2 px strokes.
- **Icons**: a flat set of 98 icons and a detailed set that has a twin for every one of them (shaded, with highlights and accents).
- **Line roles**: next step, yes / success, no / failure, return (dashed), one animated main path, and a slower animated data stream.
- **Two styles**: *plain* (shapes with text, optional small icon; the default) and *illustrated* (cards with a name pill, one line of explanation and a large icon, tinted by swimlane). Styles can be mixed in one diagram.
- **Per-type notation**: each diagram type gets its own rules page, patterns and complete examples, so a plugin can rely on written conventions instead of guessing.

| Diagram type | Design status |
| --- | --- |
| Screen flow | Done: rules, fidelity levels, conditions, tabs, overlays, devices, full examples |
| Flowchart | Done: rules, patterns, plain and illustrated examples, swimlane, complete delivery flow |
| Sequence, ER, Architecture, Explainer and the rest | Not started |

Not yet verified: whether draw.io's `flowAnimation` edge style survives export well enough to reproduce the animated lines.

## Supported diagram types

Flow aims to cover **nearly every common diagram type**, grouped into 8 categories. Each category is delivered as a plugin (or a set of plugins).

| Category | Diagram types | Status |
| --- | --- | --- |
| Process & business | Flowchart, Swimlane / cross-functional, BPMN, User flow | Planned |
| UML behavior | Sequence, Use case, Activity, State machine | Planned |
| Structure & data | ER diagram, Class diagram, Data flow diagram (DFD) | Planned |
| Architecture & infrastructure | Architecture, C4 model, Cloud (AWS / GCP / Azure), Network, Deployment | Planned |
| Planning & management | Gantt, Org chart, Mind map, Roadmap / Kanban | Planned |
| UI design | Wireframe / mockup | Planned |
| Explainer / infographic | Layered flow (icon-based tiers/lanes), Tree / hierarchy, Side-by-side comparison, Concept illustration | Planned |
| Editing | Update or restyle existing `.drawio` files | Planned |

## Getting started

Installation and usage instructions will be added once the first plugin is available.

## Roadmap

- [x] Design foundation, icon sets, Screen flow and Flowchart notation
- [ ] Design the remaining diagram types (Sequence, ER, Architecture, Explainer, ...)
- [ ] Test draw.io animated edges and export
- [ ] Define the plugin interface and project structure
- [ ] Generate valid draw.io XML from a text prompt
- [ ] First plugins: flowchart, sequence, ER, architecture
- [ ] Expand to the remaining categories above
- [ ] Support editing existing `.drawio` files
- [ ] Documentation and examples

## Contributing

The project is just getting started. Ideas and issues are welcome; contribution guidelines will follow.

## License

Released under the [MIT License](LICENSE).
