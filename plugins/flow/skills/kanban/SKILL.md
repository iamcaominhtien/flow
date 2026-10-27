---
description: Draw a Kanban board or a side-by-side comparison (columns of cards) as an animated HTML page and a draw.io file. Use when the user asks for a Kanban board, a status board or a comparison of options.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Kanban board and comparison

You write a short **spec**: columns, each with cards. A script sizes the cards, stacks them and frames each column. Never write coordinates or HTML yourself.

## Steps

1. List the columns (statuses, or the options to compare) and the cards in each.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "kanban",
  "title": "Kanban: the delivery app sprint",
  "people": {"Kai Novak": {"tone": "green"}},
  "columns": [
    {"label": "Backlog", "tone": "gray", "cards": [
      {"label": "Courier tips", "kind": "Feature", "owner": "Joy Adams"},
      {"label": "Slow map on old phones", "kind": "Bug", "owner": "Kai Novak"}
    ]},
    {"label": "In progress", "tone": "blue", "limit": 3, "cards": [
      {"label": "Live order tracking", "kind": "Feature", "owner": "Kai Novak"}
    ]},
    {"label": "Done", "tone": "green", "done": true, "cards": [
      {"label": "Order history", "kind": "Feature", "owner": "Kai Novak"}
    ]}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Column**: `label`, optional `tone` (the tint of the column), `limit` (a work-in-progress limit, whole number), `done` (true: every card in it is finished), `cards`. Columns are 360 px wide, in the order work moves (Backlog, In progress, In review, Done).
- **Card**: `label`, optional `kind` (a tag: `Feature` is blue, `Bug` red, `Chore` grey; any other word is grey, or set `tone`), `owner` (a name, drawn as a circle with initials), `detail` (a small second line), `done` (true: struck through), `tone` (the tint of the tag). A card is 100 px high: keep the title to two lines.
- **Write the cards in priority order**: the first is drawn at the top of its column.
- **Limit**: a column with a limit shows `2 / 3` instead of its count; the pill turns red when the column is full (`3 / 3`). More cards than the limit is a warning.
- **People**: the circle takes its initials from the name and its tint from the name. To get the same tint as in a Gantt chart or an org chart, pin it: `"people": {"Kai Novak": {"tone": "green", "initials": "KN"}}` with the same values in each spec.
- A board with a `kind`, `owner`, `limit` or `done` anywhere is a work board and is plain only: an `icon` or `"style": "illustrated"` is refused. Write `"use": "board"` to force this look.

## Comparison of options

For a side-by-side comparison, make each option a column and each point a card. A board with none of `kind`, `owner`, `limit` and `done` is drawn this way (or write `"use": "compare"`): cards have `label`, `detail`, `icon`, `tone`, are sized to their text, and `"style": "illustrated"` draws a card for each box with an icon (large icon on a tinted disc, the name in a pill, the `detail` under it; use it for about eight boxes or fewer and keep names short). Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`; the detailed set of the other skills (for example `courier`, `package`, `team`) also works on an illustrated card. To draw a missing icon, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- Cards cannot be dragged or edited as a board in draw.io; they are plain boxes (with child cells for the tag and the circle).
- There are no dates, and no automatic move of a card between columns.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
