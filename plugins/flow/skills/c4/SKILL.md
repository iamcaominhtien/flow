---
description: Draw a C4 model diagram (people, systems, containers, components and their relations) as an animated HTML page and a draw.io file. Use when the user asks for a C4 context, container or component diagram.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# C4 diagram

You write a short **spec**. A script places the boxes on a grid, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Pick one level and answer one question: **1 context** (who uses the system, what does it depend on), **2 containers** (what runs inside it), **3 components** (how one container is built). Level 4 is a UML class diagram: not drawn here.
2. Write `diagrams/<name>.spec.json` in the current project. Write level 1 first; a lower level names the box it opens.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

Level 1:

```json
{
  "type": "c4",
  "title": "Level 1, system context: food delivery",
  "desc": "Who uses the platform and which outside systems it depends on.",
  "elements": [
    {"id": "customer", "label": "Customer", "kind": "person", "description": "Orders food and tracks the delivery."},
    {"id": "platform", "label": "Delivery platform", "kind": "system", "description": "Takes orders, charges payments, dispatches couriers."},
    {"id": "psp", "label": "Payment provider", "kind": "external", "description": "Charges and refunds cards."}
  ],
  "relations": [
    {"from": "customer", "to": "platform", "label": "Orders food using", "main": true},
    {"from": "platform", "to": "psp", "label": "Charges cards using"}
  ]
}
```

Level 2 opens the system of level 1; level 3 opens one container of level 2:

```json
{
  "type": "c4",
  "title": "Level 2, containers: food delivery",
  "opens": {"spec": "context.spec.json", "element": "platform"},
  "elements": [
    {"id": "customer"},
    {"id": "psp"},
    {"id": "app", "label": "Customer app", "kind": "container", "technology": "iOS, Android", "description": "Browse, order, track.", "icon": "phone"},
    {"id": "db", "label": "Orders database", "kind": "database", "technology": "PostgreSQL", "description": "Orders, customers, menus."}
  ],
  "relations": [
    {"from": "customer", "to": "app", "label": "Orders food using", "main": true},
    {"from": "app", "to": "db", "protocol": "SQL"}
  ]
}
```

- **Element**: `id`, `label` (the name, no technology in it), `kind`, `technology`, `description` (one sentence), `icon`, `tone`, `at`. Every box shows an icon, the bold name, a mono line `[Kind: technology]` and the sentence. Kinds: `person` (round corners), `system` (violet, solid), `external` (grey, **dashed**), `container`, `database` (a container with the database icon, never a special shape) and `component`. Without `icon` and `tone` a box gets those of its kind: a person blue, a system violet, an external system grey, a container or component blue (give a `tone` to tint by domain).
- **Level**: read from the kinds (a `component` makes level 3, a `container` or `database` level 2, else level 1); `"level": 1|2|3` states it and is checked. A level never mixes kinds of another: no components in a container diagram. Level 1 has exactly one `system`.
- **`opens`**: `spec` is the file of the level above (relative to this spec), `element` the box of it that is opened (a `system` on level 2, a `container` or `database` on level 3). The box becomes a dashed frame with its name on the bottom edge, `Name [Software system]` or `Name [Container]`. An element that has only an `id` is the same neighbour as on the level above and takes its name, kind, technology, sentence, icon and tone from it: people and outside systems stay as they were on level 1, neighbouring containers stay containers on level 3. Without `spec`, give `label` (and `tone`) for the frame.
- **Relation**: `from` (the box that starts the call) to `to`, `label` (a verb phrase: *Charges cards using*), `protocol` (*HTTPS, JSON*), `kind` (`call`, `main`, `event`) or `main: true`. Level 1 needs a `label`. On level 2 a line between two containers needs a `protocol`; an event may have only a `label` (`order.placed`). The text drawn is `label, protocol`.
- **One blue route** (`main`) per diagram, the same on all three levels. **Violet** (`event`) is the event stream; everything else is ink.
- Layout: people on the top row, what is studied in the middle, what it depends on below or to the right. Columns are 520 px and rows 270 px apart; boxes are 280 x 132 (the system of level 1 is 360 x 150). Optional `at: [row, column]` (decimals allowed) places a box on a cell; use it when the automatic placement is wrong or to keep the same position on every level.
- At most 15 boxes in the frame: past that, zoom into a part instead.
- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill. C4 is plain only: `style: illustrated` is refused.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`, and the detailed names `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Limits to tell the user

- Automatic placement uses the lines: rows follow the distance from the people, an outside system goes to the right of the box that calls it. For a layout like the design pictures give `at` on each box. Say so when you did.
- The pill with the name of the frame can sit on a line that leaves the frame at the bottom left; look at the picture.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout can give long lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
