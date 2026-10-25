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
  "title": "BPMN: order with a timeout",
  "desc": "A customer's order is paid within a day, or it is cancelled; payment and packing run together.",
  "zones": [
    {
      "id": "shop",
      "label": "Shop",
      "tone": "blue"
    },
    {
      "id": "bank",
      "label": "Bank",
      "tone": "green"
    }
  ],
  "elements": [
    {
      "id": "s",
      "kind": "start",
      "zone": "shop"
    },
    {
      "id": "order",
      "label": "Take the order",
      "zone": "shop"
    },
    {
      "id": "split",
      "kind": "parallel",
      "zone": "shop"
    },
    {
      "id": "pay",
      "label": "Ask for payment",
      "zone": "shop"
    },
    {
      "id": "pack",
      "label": "Pack the goods",
      "zone": "shop"
    },
    {
      "id": "join",
      "kind": "parallel",
      "zone": "shop"
    },
    {
      "id": "ok",
      "kind": "exclusive",
      "zone": "shop"
    },
    {
      "id": "wait",
      "kind": "timer",
      "label": "1 day",
      "zone": "shop"
    },
    {
      "id": "ship",
      "label": "Ship it",
      "zone": "shop"
    },
    {
      "id": "e",
      "kind": "end",
      "zone": "shop"
    },
    {
      "id": "charge",
      "label": "Charge the card",
      "zone": "bank"
    }
  ],
  "flows": [
    {
      "from": "s",
      "to": "order"
    },
    {
      "from": "order",
      "to": "split"
    },
    {
      "from": "split",
      "to": "pay"
    },
    {
      "from": "split",
      "to": "pack"
    },
    {
      "from": "pay",
      "to": "join"
    },
    {
      "from": "pack",
      "to": "join"
    },
    {
      "from": "join",
      "to": "ok"
    },
    {
      "from": "ok",
      "to": "ship",
      "label": "Paid"
    },
    {
      "from": "ok",
      "to": "wait",
      "label": "Not paid"
    },
    {
      "from": "ship",
      "to": "e"
    },
    {
      "from": "pay",
      "to": "charge",
      "style": "message",
      "label": "charge"
    }
  ],
  "direction": "right"
}
```

- **Element**: `id`, `label`, `kind`: `task` (default), `subprocess`, `gateway` (an empty diamond), `exclusive` (diamond with an X), `parallel` (diamond with a +), `start`, `end`, `event` (plain intermediate event), `timer`, `message`, `error` (intermediate events with a clock, an envelope or a warning mark), `document`. Start, end, event and gateway kinds need no label; a label on an event sits under it.
- **Zone**: a pool or lane, drawn as a swimlane: `id`, `label`, `tone`. When there are zones, every element needs one (`zone`), and the build refuses an element without one. Zones are laid out side by side; nesting (`parent`) is not used.
- **Flow**: `from`, `to`, `label`, `style`: `sequence` (solid, default) or `message` (dashed, a dot at the start and an open arrow, for messages between pools), `main: true`.
- Top level: `type` (`bpmn`), `title`, `desc`, `zones` (the pools, see above), `elements`, `flows`, optional `direction`. **With pools use `"direction": "right"`**: each pool becomes a horizontal band and time runs left to right, as in usual BPMN. With `down` the pools are columns.
- In a pool, branches that start at the same gateway are drawn side by side (one above the other when the direction is `right`), so a parallel split looks parallel.
- Messages: a `message` flow may start and end on any element, in the same pool or another.
- Optional `at: [row, column]` on an element places it on an explicit grid cell (row = step along the flow, column = across it, both counted from 0). It switches the whole diagram to explicit cells, so give every element one. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Illustrated style

Add `"style": "illustrated"` at the top level to draw each box that has an `icon` as a card: a large icon on a tinted disc, the name in a pill, and the `detail` text under it. Boxes without an icon stay plain. Cards are bigger, so use it for a few boxes (about eight or fewer), give each a `tone` and a short `detail`, and keep names short: the name stays on one line. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on a card in place of the disc: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Limits to tell the user

- This is the BPMN look, not the full standard: only the timer, message and error events and the exclusive and parallel gateways are marked; there is no start or end event type, no boundary event, no data object, and no check that message flows cross pools. Say so if the user needs strict BPMN.
- With pools, a line that leaves a gateway on the side can go around the outside of its pool. Check the picture.
- The report names each flow by its two ends, for example `line 'e10' (Scoring failed to Send rejection) passes through ...`; the ids `e1`, `e2`, ... count the flows in the order written, from 1. To fix a line through a box, change the order of the elements or the pool of one of its ends, or move the element with `at`.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).
