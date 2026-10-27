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
  "title": "State machine: the life of an order",
  "desc": "One sentence that says what the diagram shows.",
  "states": [
    {"id": "begin", "kind": "start"},
    {"id": "placed", "label": "Placed", "tone": "blue"},
    {"id": "preparing", "label": "Preparing", "tone": "green", "do": "cook"},
    {"id": "delivering", "label": "Delivering", "states": [
      {"id": "picked", "label": "Picked up", "tone": "teal"},
      {"id": "arrived", "label": "Arrived", "tone": "teal"}]},
    {"id": "cancelled", "label": "Cancelled", "kind": "fail"},
    {"id": "finish", "kind": "end"},
    {"id": "closed", "kind": "end"}
  ],
  "transitions": [
    {"from": "begin", "to": "placed", "main": true},
    {"from": "placed", "to": "preparing", "event": "restaurant accepts", "main": true},
    {"from": "preparing", "to": "preparing", "event": "item out of stock", "action": "substitute"},
    {"from": "preparing", "to": "picked", "event": "courier arrives", "main": true},
    {"from": "picked", "to": "arrived", "guard": "near address", "action": "notify customer", "main": true},
    {"from": "arrived", "to": "finish", "main": true},
    {"from": "placed", "to": "cancelled", "event": "cancel"},
    {"from": "cancelled", "to": "closed", "event": "cleanup"}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **State**: `id`, `label`, optional `kind` (`state` default, `start` the filled dot, `end` the ringed dot, `fail` a rose box for a failure or cancel), `tone`, `icon`, `detail`. A `start` or `end` mark needs no label; more than one `end` is fine. The name is a noun or an adjective (`Paid`, `On the way`).
- **Activities** under the name, in mono grey: `entry`, `do`, `exit` (text only: `"do": "cook"` is drawn `do / cook`).
- **Composite state**: put states in a state's `states` list, or give each a `group` name. They are drawn in a frame with the name in a pill. Keep the members next to each other on the happy path.
- **Transition**: `from`, `to`, and any of `event` (in words), `guard` (a condition, drawn in brackets) and `action` (drawn after a slash), shown as `event [guard] / action`. `label` is accepted for `event`. `main: true` marks the happy path: blue, thick, animated. Mark every transition of one path, and only one path. A transition from a state to itself is a loop above the box. Transitions to or from a `fail` state are rose; `fail: true` makes any other one rose.
- **Layout (from the design):** the happy path runs left to right in the first row (the transitions with `main`, else the first transition of each state); other states sit below the state that leads to them; an end that is not on the path sits right of the state that leads to it. Boxes are 160 x 64 and at least 130 px apart where a label sits between them. Tint states by phase (`tone`); it groups, it never means alone.
- Use `status` values of the ER table as state names, so the two diagrams agree.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

## Limits to tell the user

- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- A line that comes into a state from the side of a different row can bend twice; two lines that share a side of a state are spread 60 px apart. Transitions to a composite state go to a state inside it.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
