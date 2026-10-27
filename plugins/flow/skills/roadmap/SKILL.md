---
description: Draw a roadmap (what each team ships in each quarter or period, in rows) as an animated HTML page and a draw.io file. Use when the user asks for a roadmap or a plan by theme or team.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Roadmap

You write a short **spec**: the periods and the lanes (rows) with their items. A script sizes the columns, places the cards, stacks the ones that overlap in time, draws the one dependency arrow and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Choose the periods (quarters, months) and the lanes (teams or themes), then list each lane's items with the period they start in, whether they are committed, and who owns them. Dates do not belong here: use a Gantt chart.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "roadmap",
  "title": "Roadmap: now, next, later",
  "periods": [
    {"label": "Now", "detail": "March to April", "tone": "green"},
    {"label": "Next", "detail": "May to June", "tone": "amber"},
    {"label": "Later", "detail": "Second half", "tone": "gray"}
  ],
  "lanes": [
    {"label": "Ordering", "tone": "blue", "icon": "cart", "items": [
      {"id": "tracking", "label": "Live order tracking", "period": "Now", "owner": "Kai Novak"},
      {"label": "Group orders", "period": "Later", "committed": false}
    ]},
    {"label": "Delivery", "tone": "teal", "icon": "courier", "items": [
      {"label": "Courier tips", "period": "Next", "depends_on": "tracking"}
    ]}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- `periods`: the columns, a name (`"Now"`, `"Q1"`) or an object with `label`, `detail` (the dates in words, such as `March to April`) and `tone`. The names `Now`, `Next` and `Later` get green, amber and grey. Up to about six columns fit; the column width shrinks from 464 px as they grow.
- **Lane** (a row, one theme or team): `label`, `tone`, `icon` (drawn large, in its detailed form when there is one: `cart courier bell package team store money target flag idea chart` and the rest of the detailed set), `items`.
- **Item** (a card): `label`, `period` (a period name, or its number from 0; `start` is the older name for the number), optional `length` (how many periods it spans, default 1), `committed` (default true; `false` draws a dashed card tagged Exploring: an idea under study), `owner` (a name, drawn as a circle with initials like the Gantt and org chart ones; pin the tint with a top-level `people` object), `detail`, `id`. Cards of a lane that share a period are stacked in extra rows.
- **The one dependency**: `depends_on` (this item cannot start before the other is done) or `blocks` (the other cannot start before this one is done), naming the other item by `id` or by its label. It is drawn as the one blue, animated arrow, and a note below the chart says what it means. Only one is allowed (a second is an error): pick the one that decides the order. The other item may not be in an earlier period.
- `note`: replaces the generated note below the chart.
- An exact date in a card or a detail gets a warning; write months or quarters.

## Limits to tell the user

- Time is in whole periods; there are no dates and no progress marks.
- Only one dependency is drawn; more belong in a Gantt chart.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
