---
description: Draw a system architecture diagram (components, the zones they live in, and how they call each other) as an animated HTML page and a draw.io file. Use when the user asks for an architecture, infrastructure or cloud diagram, or a system overview.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Architecture diagram

You write a short **spec**: the zones, the components and the links. A script places components, draws a frame around each zone, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the components, the zones (a cloud, a network, a team boundary) they sit in, and the calls or data flows between them.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "architecture",
  "title": "Architecture: online shop",
  "desc": "One sentence that says what the diagram shows.",
  "direction": "down",
  "zones": [
    {"id": "cloud", "label": "Cloud", "tone": "blue"},
    {"id": "backend", "label": "Backend", "tone": "violet", "parent": "cloud"}
  ],
  "components": [
    {"id": "web", "label": "Web app", "zone": "cloud", "icon": "phone"},
    {"id": "api", "label": "API", "detail": "REST, JSON", "zone": "backend"},
    {"id": "db", "label": "Orders DB", "kind": "database", "zone": "backend"}
  ],
  "links": [
    {"from": "web", "to": "api", "label": "calls", "main": true},
    {"from": "api", "to": "db", "label": "reads and writes"}
  ]
}
```

- **Zone**: `id`, `label`, optional `tone`, optional `parent` (another zone) to nest it.
- **Component**: `id`, `label`, optional `kind` (`service` default, `client`, `external`, `database`, `store`, `queue`), `detail` (a small second line), `icon`, `tone`, `zone`.
- **Link**: `from`, `to`, optional `label`, `style` (`call` solid, `async` dashed), `main: true` to highlight and animate the path to follow first (one or two links, not all).
- `direction`: `down` (default) or `right`.
- Optional `at: [row, column]` on a component places it on an explicit grid cell. Use it only when the automatic placement is wrong.

## Limits to tell the user

- A zone is a frame around the bounding box of its components. Whether an unrelated component can fall inside that box is not verified; look at the picture if zones are crowded.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).
