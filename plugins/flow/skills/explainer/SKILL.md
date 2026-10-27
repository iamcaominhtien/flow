---
description: Draw an explainer (one idea taught to someone outside the field: a journey through bands, a tree, a comparison, a concept with an analogy, or several of these on one page) as an animated HTML page and a draw.io file. Use when the user asks to explain how something works, what is inside something, A or B, or what a thing does, for a newcomer, a customer or a manager.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Explainer

An explainer answers **one question**, written in the title, and a reader gets the answer in under a minute. It is always illustrated (large icons, name pills, tinted cards); there is no plain mode. It tells a story about a system; to record a system for engineers use `architecture` or `sequence`. You write a short **spec**; a script places the cards, bands and lines. Never write coordinates or HTML yourself.

## Steps

1. Write the question as the title (`What a cache does`, `SQL or NoSQL?`), never an instruction. Pick the shape: `layers` (a journey through places), `tree` (one root and its parts), `comparison` (two things, row by row), `concept` (one idea, four facts, an analogy). For a complex story, combine several in `sections`.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## Writing rules (the build warns when they are broken)

- Four to eight cards on a shape; more: split into two explainers. One idea per card, at most 14 words of text.
- Name things in the reader's words (`Your browser`, not `Client`). Define a term when it first appears; prefer an analogy to a definition.
- Words on a line say what happens in everyday words (`asks "where is it?"`, `no copy`), never a protocol name such as HTTP, TCP or DNS.
- Short, active sentences in the present tense. One bold closing line at most (the fast path, the rule of thumb or the caveat).

## Shapes

Common keys: `type: "explainer"`, `shape`, `title`, `desc` (one or two sentences, what the reader will know and how to read it), optional `theme`. A **card** is `name`, `text`, `icon`, optional `tone` (`blue violet amber green teal gray red`), `id`.

**layers** (1500 px wide): `bands` (each `label`, `tone`, `cards`, optional bold `remark` in the free half), `links` (`from`, `to`, `label`, `kind`), `closing`.
- Cards sit in columns left to right (`col` starts at 0; default is the next column) and are numbered 1, 2, 3 in reading order (`numbers: false` turns it off, `number: "3a"` sets one; branches share a number and take a letter).
- `branch: true` draws a small row card; two in one column stack with `stack: 0` and `stack: 1`.
- `kind`: `path` (blue, animated; the story, the default), `step` (ink), `return` (dashed grey), `yes` (green), `no` (red).

**tree**: `root` (a card), `rows` (each `name`, `text`, `icon`, `tone`, optional `inside` list of small chips), `note` (a small grey line), `names: "code"` (mono, the default) or `"plain"`. No numbers.

**comparison**: `left` and `right` (cards), `rows` (each `label`, `left`, `right`), `rule` (`title`, `text`: the rule of thumb).

**concept**: `hub` (a card), `facts` (2 to 4 cards, read left to right, top to bottom), `analogy` (`label`, `tone`, `left`, `right`, `link`, `closing`).

**sections**: a list of `{shape, title, column}` with `column` `left`, `right` or `full`; each holds the keys of its shape. Sections get the letters A, B, C. A `shape: "analogy"` section (the keys of the concept's analogy, no `title`) goes `full` under the columns. Each section follows the same limits (eight cards).

```json
{
  "type": "explainer",
  "shape": "concept",
  "title": "What a cache does",
  "desc": "A cache keeps a copy of what you used recently, close at hand.",
  "hub": {"name": "Cache", "text": "A small, fast place that holds copies.", "icon": "in-memory-cache"},
  "facts": [
    {"name": "Fast", "text": "Answers in a blink, because it is near.", "icon": "launch"},
    {"name": "Small", "text": "Holds only a little, so it keeps what is popular.", "icon": "package"},
    {"name": "Temporary", "text": "Old copies expire so they never go stale.", "icon": "schedule"},
    {"name": "A copy, not the original", "text": "The real data stays in the database.", "icon": "database"}
  ]
}
```

Examples to copy: `examples/explainer-layers.spec.json`, `-tree`, `-compare`, `-concept` and `-payment` (the complete one with sections).

## Icons

Use detailed icons; any name of the library works: `browser dns cdn load-balancer server in-memory-cache database folder code package lock key user cart card money security warn error success info table json launch schedule id-card gateway globe` and more (see the flowchart skill). To draw a missing one, write `icons.local.json` next to the spec.

## Limits to tell the user

- Only the blue path is animated (off for viewers who prefer reduced motion; in draw.io it has its own flow animation). Checked in a viewer, not in the draw.io editor; SVG export is not tested.
- A band holds one row of cards (stacks of small branch cards aside). Text width is estimated, not measured.
- A card does not link to a page that shows it in detail (the design has not decided it).
