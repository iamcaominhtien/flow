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
  "title": "DFD level 0: order system",
  "desc": "A customer's order flows through processing to the kitchen and the order store.",
  "elements": [
    {
      "id": "cust",
      "label": "Customer",
      "kind": "external"
    },
    {
      "id": "proc",
      "label": "Process order"
    },
    {
      "id": "orders",
      "label": "Orders",
      "kind": "store"
    },
    {
      "id": "kitchen",
      "label": "Kitchen",
      "kind": "external"
    }
  ],
  "flows": [
    {
      "from": "cust",
      "to": "proc",
      "label": "order"
    },
    {
      "from": "proc",
      "to": "orders",
      "label": "save"
    },
    {
      "from": "proc",
      "to": "kitchen",
      "label": "ticket"
    }
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Element**: `id`, `label`, optional `kind`: `process` (default, an ellipse), `external` (a box for a person or system outside), `store` (open-ended box for stored data). Also `detail`, `icon`, `tone`.
- **Flow**: `from`, `to`, `label` (the data that moves), `main: true` to highlight one path.
- DFD rule: data should not flow directly between two externals, between two stores, or between an external and a store. The tool does not enforce this; check it yourself.
- Top level: `type` (`dfd`), `title`, `desc`, optional `direction` (`down` default, or `right`).
- Optional `at: [row, column]` on an item places it on an explicit grid cell. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Illustrated style

Add `"style": "illustrated"` at the top level to draw each box that has an `icon` as a card: a large icon on a tinted disc, the name in a pill, and the `detail` text under it. Boxes without an icon stay plain. Cards are bigger, so use it for a few boxes (about eight or fewer), give each a `tone` and a short `detail`, and keep names short: the name stays on one line. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on a card in place of the disc: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Limits to tell the user

- Levels (a process that opens into its own diagram) are not linked: make one diagram per level.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
