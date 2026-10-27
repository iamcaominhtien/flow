---
description: Draw a UML use case diagram (actors, the use cases they take part in, and the system boundary) as an animated HTML page and a draw.io file. Use when the user asks for a use case diagram.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Use case diagram

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the actors, the use cases, the system boundary, and which actor takes part in which use case.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "usecase",
  "title": "Use case diagram: the delivery app",
  "desc": "Who uses the system and what for.",
  "system": "Delivery app",
  "actors": [
    {"id": "customer", "label": "Customer", "tone": "blue", "icon": "user"},
    {"id": "payment", "label": "Payment provider", "tone": "amber", "icon": "card", "external": true}
  ],
  "usecases": [
    {"id": "place", "label": "Place an order"},
    {"id": "promo", "label": "Apply a promo code"},
    {"id": "pay", "label": "Pay for the order"}
  ],
  "links": [
    {"from": "customer", "to": "place"},
    {"from": "payment", "to": "pay"},
    {"from": "promo", "to": "place", "style": "extend"},
    {"from": "place", "to": "pay", "style": "include"}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **System**: `system` is the name written at the top left of the white frame.
- **Actor**: `id`, `label`, optional `tone` (default: blue, green, teal, amber, violet in turn), `icon` (for the illustrated style), `external: true` for an outside system: it stands on the right of the frame with the tag `external system`; people stand on the left.
- **Use case**: `id`, `label` (a verb phrase), optional `tone` (default: the tone of the actor that uses it; a use case that only another includes or extends takes the tone of that one). An oval of 240 x 64.
- **Link**: `from`, `to`, `style`: `association` (default: a solid line without a head; the actor takes part), `include` (dashed open arrow from the base use case to the one it always uses), `extend` (dashed open arrow from the extension to the base it may add to), `generalizes` (hollow triangle). `include` and `extend` are labelled `«include»` and `«extend»` unless you give `label`.
- **Layout (from the design):** the use cases of one actor stand in one column, one actor after the other; a use case that is included or extended goes in the second column, in the row of the one it relates to. Use cases of an external actor go in the second column too. Lines are straight. Give every use case a link, or it stands alone in the first column.
- `"style": "illustrated"` draws each actor as a card with a name pill and a large detailed icon (`user`, `store`, `courier`, `card` as in the design); the notation does not change. The default is `"style": "plain"`: stick figures.
- The older form with `items` (each with `kind`: `actor` or `usecase`) and `zones` (the first is the system) is still read.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`; detailed ones for cards include `courier`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- Lines are straight, so a line from an actor to a use case in the second column can cross a use case of the first; the check reports it, and the fix is to link the actor to the first column or to move the use case.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
