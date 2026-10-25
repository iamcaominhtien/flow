---
description: Draw a BPMN-style process diagram (events, tasks, gateways, sequence and message flows, optionally grouped in pools) as an animated HTML page and a draw.io file. Use when the user asks for BPMN or a business process model.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# BPMN diagram

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the start and end events, the tasks, the gateways with their yes/no branches, and any groups (pools or lanes).
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "bpmn",
  "title": "BPMN: refund request",
  "desc": "A refund request is checked; an eligible one is paid, the others are declined.",
  "elements": [
    {
      "id": "begin",
      "kind": "start"
    },
    {
      "id": "check",
      "label": "Check the request"
    },
    {
      "id": "ok",
      "kind": "gateway",
      "label": "Eligible?"
    },
    {
      "id": "pay",
      "label": "Pay the refund"
    },
    {
      "id": "decline",
      "label": "Send a refusal"
    },
    {
      "id": "done",
      "kind": "end"
    }
  ],
  "flows": [
    {
      "from": "begin",
      "to": "check"
    },
    {
      "from": "check",
      "to": "ok"
    },
    {
      "from": "ok",
      "to": "pay",
      "label": "Yes",
      "main": true
    },
    {
      "from": "ok",
      "to": "decline",
      "label": "No"
    },
    {
      "from": "pay",
      "to": "done"
    },
    {
      "from": "decline",
      "to": "done"
    }
  ]
}
```

- **Element**: `id`, `label`, `kind`: `task` (default), `subprocess`, `gateway` (diamond), `event` (intermediate), `start`, `end`, `document`. Start, end, event and gateway need no label.
- **Zone**: a pool or lane, drawn as a frame: `id`, `label`, `tone`, `parent`. Put elements in it with `zone`.
- **Flow**: `from`, `to`, `label`, `style` (`sequence` solid, default; `message` dashed with an open arrow, for messages between pools), `main: true`.
- Top level: `type` (`bpmn`), `title`, `desc`, optional `direction` (`down` default, or `right`).
- Optional `at: [row, column]` on an item places it on an explicit grid cell. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Illustrated style

Add `"style": "illustrated"` at the top level to draw each box that has an `icon` as a card: a large icon on a tinted disc, the name in a pill, and the `detail` text under it. Boxes without an icon stay plain. Cards are bigger, so use it for a few boxes (about eight or fewer), give each a `tone` and a short `detail`, and keep names short: the name stays on one line. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on a card in place of the disc: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Limits to tell the user

- This is the BPMN look, not the full standard: no event types (timer, message, error), no gateway markers (X, +), no data objects. Say so if the user needs strict BPMN.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).
