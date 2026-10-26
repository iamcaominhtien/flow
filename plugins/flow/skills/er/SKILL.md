---
description: Draw an entity-relationship diagram (tables, columns, keys and how tables relate) as an animated HTML page and a draw.io file. Use when the user asks for an ER diagram, a database schema, or how tables link to each other.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# ER diagram

You write a short **spec**: the tables, their columns and the relations. A script lays the tables out, draws the cardinality marks (crow's foot), checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the tables with their columns, then the relations between them.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "er",
  "title": "ER: food delivery",
  "desc": "One sentence that says what the diagram shows.",
  "tables": [
    {"id": "customers", "name": "customers", "icon": "user", "tone": "blue", "columns": [
      {"name": "id", "type": "bigint", "flags": ["pk"]},
      {"name": "email", "type": "text", "flags": ["uq"]}]},
    {"id": "orders", "name": "orders", "tone": "violet", "columns": [
      {"name": "id", "type": "bigint", "flags": ["pk"]},
      {"name": "customer_id", "type": "bigint", "flags": ["fk"]}]}
  ],
  "relations": [
    {"from": "customers", "to": "orders", "label": "places", "main": true}
  ]
}
```

- **Table**: `id`, `name`, `columns`, optional `icon` and `tone`.
- **Column**: `name`, optional `type`, optional `flags` from `pk`, `fk`, `uq`, `null`.
- **Relation**: `from`, `to`, optional `label`. `from_end` and `to_end` set the mark at each end: `one`, `zero_one`, `one_many`, `zero_many`. The default is `one` at `from` and `zero_many` at `to`. `style` is `solid` (a foreign key) or `logical` (dashed, no real key). `main: true` highlights and animates the relation to follow first. Mark one or two, not all.
- Optional `from_column` and `to_column` name the columns the relation joins; they are not drawn yet.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

## Limits to tell the user

- Text width is estimated, not measured; a long column name may be tight.
- The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.
