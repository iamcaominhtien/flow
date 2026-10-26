---
description: Draw a concept diagram (one central idea with its parts around it, joined by spokes) as an animated HTML page and a draw.io file. Use when the user asks to explain a concept, a hub and spokes, or what something is made of.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Concept diagram

You write a short **spec**: the central idea and the parts around it. A script places the parts clockwise from the top on a ring, joins each to the centre and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Name the central idea, then list the parts (up to ten), each with a short name and one line saying what it does.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "concept",
  "style": "illustrated",
  "title": "Concept: a card payment",
  "desc": "One payment touches five parties, each with one job.",
  "center": {
    "label": "Card payment",
    "tone": "violet"
  },
  "items": [
    {
      "label": "Customer",
      "icon": "user",
      "detail": "Taps the card",
      "tone": "blue"
    },
    {
      "label": "Shop",
      "icon": "store",
      "detail": "Asks for the money",
      "tone": "green"
    },
    {
      "label": "Card network",
      "icon": "globe",
      "detail": "Routes the request",
      "tone": "amber"
    },
    {
      "label": "Bank",
      "icon": "database",
      "detail": "Checks the balance",
      "tone": "violet"
    },
    {
      "label": "Receipt",
      "icon": "doc",
      "detail": "Proof for both sides",
      "tone": "teal"
    }
  ]
}
```

- `center`: `label`, optional `detail`, `icon`, `tone`.
- `items`: 1 to 10 of `label`, optional `detail`, `icon`, `tone`. They are placed clockwise from the top, in the order written.
- `style`: `plain` (default) or `illustrated`. Illustrated draws each part that has an `icon` as a card (large icon, name pill, detail line); icons with a detailed drawing show it.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- The ring is a circle: many wide parts make it large. Ten is the most.
- The spokes are plain lines; there are no arrows and no labels on them. To show direction or order, use another skill.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
