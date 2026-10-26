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

- **Table**: `id`, `name`, `columns`, optional `icon` and `tone`, and `at: [row, column]` to put it in a grid cell (give `at` to every table or to none).
- **Column**: `name`, optional `type`, optional `flags` from `pk`, `fk`, `uq`, `null`. The keys are drawn as chips before the name (`PK` amber, `FK` blue, `UQ` violet); `null` adds a `?` to the type. Keys first, then the columns that explain the relations.
- **Relation**: `from`, `to`, optional `label`. `from_end` and `to_end` set the mark at each end: `one`, `zero_one`, `one_many`, `zero_many`. The default is `one` at `from` and `zero_many` at `to`. `style` is `solid` (a foreign key) or `logical` (dashed, no real key). `main: true` highlights and animates the relation to follow first. Mark one or two, not all.
- Optional `from_column` and `to_column` name the columns the relation joins; they are not drawn yet.

## Style and layout (from the design)

- **Style:** `"style": "illustrated"` at the top level gives tables with a 64 px header (a name pill and a large detailed icon); the default `plain` has a 40 px header with a small flat icon. Rows, keys, lines and marks are the same in both. A table with no `icon` gets the `table` icon when illustrated.
- **Names:** a table name is a singular noun in PascalCase (`Order`, `OrderItem`); a column name is snake_case, and a foreign key is the name of what it points to plus `_id` (`customer_id`). Order the columns: primary key, foreign keys, then the rest. Show the keys and the columns that explain the relations, not the whole schema.
- **Types:** generic names (`uuid`, `text`, `int`, `decimal`, `bool`, `timestamp`); a dialect is fine if the author uses it. `null` in `flags` adds a `?`.
- **Tone by domain** (it groups, it never means anything alone): customer or user `blue`, order or document `violet`, payment or money `amber`, restaurant or catalogue `green`, courier or delivery `teal`, junction or lookup `gray`.
- **Many to many** is never one line: add a junction table with two foreign keys that together are its primary key (`flags: ["pk", "fk"]` on both columns), and two relations from the outer tables (`one` to `zero_many`). The junction is `gray` unless it carries data of its own (a quantity, a grade); then it gets a domain tint and a real name (`OrderItem`).
- **Relations:** name the columns with `from_column` and `to_column` (the foreign key on the "many" side), so the line leaves and enters level with those rows, as in the design. `style: "logical"` is a dashed slate link with no constraint (for example to another service); a solid line is an enforced foreign key. One relation may have `main: true`: it is the animated blue path a typical read follows (one per diagram). A verb names each link, in the active voice, read from the "one" side (`places`, `contains`). A table that points at itself (a manager, a parent) is a relation from the table to itself; it is drawn as a loop at the right side.
- **Placement:** for more than four tables give every table a grid cell, `at: [row, column]`: parents above or to the left of their children, the table the story is about in the middle, the most connected table where it touches the most neighbours, lines short. Columns are 240 px wide with 160 px between them.
- **Domains:** give each table a `domain` (`"domain": "Orders"`). With `"domain_frames": true` at the top level each domain gets the design's dashed tinted frame with its name in a pill; keep the tables of one domain side by side in the grid so that no frame covers a table of another domain.
- **Subtype:** `"style": "subtype"` on a relation, from the parent to the child: a hollow triangle at the parent, no mark at the child (the child shares the parent's key).
- **Size:** about ten tables fit on a page. Past that, split by domain: give every table a `domain` and run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py split diagrams/<name>.spec.json`. It writes `<name>-overview` (one box per domain, one line per foreign key that crosses a domain border, named after the column) and `<name>-<domain>` (the tables of the domain in full; a table of another domain that is joined to them appears once as a grey dashed copy with its key only and a tag such as "See Orders page"), each with its HTML and `.drawio` file, and prints a check report per page.
- **A table drawn on another page** can also be written by hand: `"see": "See Orders page"` on a table makes it a dashed copy with that tag under it.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

## Limits to tell the user

- Text width is estimated, not measured; a long column name may be tight.
- The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
