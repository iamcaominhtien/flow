---
description: Draw a state diagram (the states of something and the events that move it between them) as an animated HTML page and a draw.io file. Use when the user asks for a state machine, a lifecycle, or the statuses of an order, ticket or account.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# State diagram

You write a short **spec**: the states and the transitions. A script places the states, routes the transitions, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the states, the start and the end, and what moves the thing from one state to another.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "state",
  "title": "States of an order",
  "desc": "One sentence that says what the diagram shows.",
  "states": [
    {"id": "begin", "kind": "start"},
    {"id": "created", "label": "Created"},
    {"id": "cancelled", "label": "Cancelled", "kind": "fail"},
    {"id": "done", "kind": "end"}
  ],
  "transitions": [
    {"from": "begin", "to": "created"},
    {"from": "created", "to": "cancelled", "label": "cancel"},
    {"from": "created", "to": "done", "label": "finish", "main": true}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **State**: `id`, `label`, optional `kind` (`state` default, `start`, `end`, `fail`), `detail`, `icon`, `tone`. A `start` or `end` mark needs no label.
- **Transition**: `from`, `to`, optional `label` (the event), `main: true` to highlight and animate the path to follow first.
- `direction`: `down` (default) or `right`.
- Nested states, guards and actions on transitions are not supported: put them in the label or the `detail`.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

## Limits to tell the user

- Two transitions that leave the same side of a state can share the first stretch of line, and a label can sit on the neighbouring line. Check the picture.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
