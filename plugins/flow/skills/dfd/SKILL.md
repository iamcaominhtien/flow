---
description: Draw a data flow diagram (external parties, processes, data stores and the data moving between them) as an animated HTML page and a draw.io file. Use when the user asks for a DFD or for how data moves through a system.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Data flow diagram (DFD)

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the external parties, the processes, the data stores, and each flow of data between them.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "dfd",
  "title": "Level 1: inside the delivery system",
  "desc": "The steps hand work to each other through the Orders store.",
  "elements": [
    {"id": "customer", "label": "Customer", "kind": "external", "tone": "blue", "icon": "user"},
    {"id": "take", "label": "Take order", "detail": "checks the basket", "icon": "cart"},
    {"id": "pay", "label": "Take payment", "icon": "money"},
    {"id": "orders", "label": "Orders", "kind": "store", "icon": "database"}
  ],
  "flows": [
    {"from": "customer", "to": "take", "label": "Basket, card details", "main": true},
    {"from": "take", "to": "customer", "label": "Confirmation, tracking"},
    {"from": "take", "to": "pay", "label": "Amount to pay", "main": true},
    {"from": "take", "to": "orders", "label": "New order"},
    {"from": "orders", "to": "take", "label": "Order status", "status": true},
    {"from": "pay", "to": "orders", "label": "Payment status"},
    {"from": "orders", "to": "pay", "label": "Paid order"}
  ]
}
```

Gane-Sarson shapes: an **external entity** is a square-cornered box with its id (`E1`); a **process** is a rounded box with its number in a header strip (`1.0`); a **data store** is a box open on the right with an id cell (`D1`).

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Element**: `id`, `label`, `kind` (`process` default, `external`, `store`), optional `detail` (a few words under a process name), `icon`, `tone`, `number`, `at: [row, column]`. Ids are made up in order: `E1`, `E2` for parties, `D1` for stores, `1.0`, `2.0` for processes (`0` for the one process of level 0). A `number` you give is kept and never made up again. Names: a process is a verb phrase ("Take order"), a party or store a noun.
- **Flow**: `from`, `to`, `label` (required: the data, as a noun phrase such as "Order ticket", never a verb). `main: true` marks the one blue journey of the data; `status: true` marks a flow that only reports status (violet, thin). A reply is its own flow: two flows between the same two boxes are drawn side by side, 60 px apart.
- The build **refuses**, with the reason: a flow between two external entities, between two stores, or between an entity and a store (put a process between them); a process with no output (black hole) or no input; a store on level 0.
- Warnings: a level 1 with fewer than 4 or more than 7 processes, a level 2 with fewer than 3 or more than 6, a store that is only written or only read.
- Top level: `type`, `title`, `desc`, `style` (`plain` or `illustrated`), optional `level` (0, 1 or 2; derived when left out: one process and no store is level 0; `opens` makes it level 2).
- Placement is automatic (columns 640 px apart, rows 400 px: parties on the outside edge, processes in the middle, stores between). `at: [row, column]` on an element overrides it; halves are allowed (`[1, 1.5]`).
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Levels and balancing

A DFD is drawn in levels, one spec per level:

1. **Level 0, context**: one process and the outside parties, no stores.
2. **Level 1**: the process opened into 4 to 7. Stores appear here.
3. **Level 2**: one level-1 process opened into 3 to 6, numbered `4.1`, `4.2`... Add `"opens": {"spec": "level1.spec.json", "process": "deliver"}` (the file is relative to this spec; `process` is the id of the process in it).

In a level 2 spec, an element whose `id` is the id of a level 1 element (a party or a store) is the same neighbour: it takes its label, number, icon and tone from level 1 (write only `{"id": "courier"}`), and a store of level 1 is drawn dashed for reference. New stores (`"number": "D3"`) and the parts of the process are new ids. The opened process is drawn as a dashed frame labelled `4.0 Deliver order`.

**Balancing**: opening a process keeps every flow that crossed it, from the same neighbour, in the same direction, with the same label. A flow may be split into parts: give each part `"of": "<label on level 1>"`. A flow may not appear or vanish: the build refuses the spec and names the flow. Level 2 is the last level; do not open a level 2 spec.

## Illustrated style

Add `"style": "illustrated"` at the top level to draw every box as a card: the name in a pill at the left, a large icon at the right, the `detail` under the name; the number strip and the id cell are kept. Cards are bigger (process 300 x 170, party 280 x 120, store 340 x 96) and the grid is wider. Give each box an `icon`, a `tone` and a short `detail`. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on a card in place of the disc: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Limits to tell the user

- Balancing is checked only between a level 2 spec and the level 1 spec it opens; levels 0 and 1 are not compared.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
