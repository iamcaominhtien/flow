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

- **State**: `id`, `label`, optional `kind` (`state` default, `start`, `end`, `fail`), `detail`, `icon`, `tone`. A `start` or `end` mark needs no label.
- **Transition**: `from`, `to`, optional `label` (the event), `main: true` to highlight and animate the path to follow first.
- `direction`: `down` (default) or `right`.
- Nested states, guards and actions on transitions are not supported: put them in the label or the `detail`.

## Limits to tell the user

- Two transitions that leave the same side of a state can share the first stretch of line, and a label can sit on the neighbouring line. Check the picture.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
