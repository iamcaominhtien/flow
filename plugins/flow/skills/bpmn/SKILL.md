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

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- Time runs left to right; `direction` is accepted and ignored. Placement is automatic: an element is one column after the one that leads to it, and a decision sends its alternative branch to the row below. You never write coordinates.
- **Zone**: `id`, `label`, `tone`, optional `parent`, optional `black_box`. A zone without `parent` is a **pool** (one participant); a zone with a `parent` is a **lane** of that pool. A pool with lanes needs no `label` (its lanes carry the names); each element then names a lane. `"black_box": true` draws the pool as a bar with its name only: no element may name it as its zone, and a message flow may start or end on it by naming its id (for a partner you do not model inside). Pools are stacked in the order written. When there are zones, every element needs a `zone`; with no zones the diagram is flat.
- **Element**: `id`, `label`, `kind`, `zone`, optional `tone`, `trigger`, `repeat`, `attached_to`, `interrupting`, `column`, `row`, `number`.
  - Events (a circle, radius 20, name under it): `start` (thin green ring), `end` (thick rose ring), `event` (plain intermediate, double amber ring), and the intermediate kinds `timer`, `message`, `error`, `signal`. `trigger` (`message`, `timer`, `error`, `signal`) puts the mark in a `start`, `end` or `event`: a message start, an error end. Marks: envelope, clock, lightning, triangle.
  - Tasks (130 x 64, a verb and a noun): `task`, `user` (person), `service` (gear), `send` (filled envelope), `receive` (outlined envelope), `manual` (hand), `subprocess` (a `+` at the bottom). `repeat`: `multi` (three bars: once per item) or `loop` (a loop mark).
  - Gateways (diamond, 52 wide): `exclusive` (cross), `parallel` (plus), `inclusive` (circle), `event_based` (ringed pentagon), `gateway` (empty). Give a split a `label` that is a question ("Valid?"); a join has none.
  - `store` is a data store (a can); join it to a task with a flow of style `data`. `document` is a document shape.
  - `attached_to` (the id of a task) makes an event a **boundary event** on the bottom edge of that task. A solid ring interrupts the task; `"interrupting": false` draws a dashed ring that only nudges. The flow that leaves it leads to the handler, which is placed under the task.
  - `column` pins an element to a column (columns count from 0; look at the picture, then pin to separate two elements); `row` shifts it in its lane (0 is the main row, 1 the row below, -1 above). `number` draws a small dark badge on the element.
- **Flow**: `from`, `to`, `label`, `style`, `main`, `failure`. `style`: `sequence` (solid, default: inside one pool), `message` (dashed, a ring at the start and a hollow head: between pools only), `return` (dashed slate: a loop back or a retry), `data` (dotted: a task and a data store). `main: true` marks the blue animated happy path: **one path per diagram, not one per pool**. `failure: true` draws a red line (a failure exit, a deadline).
- The build refuses: a message flow inside one pool, a sequence flow between two pools, a start event with a flow into it, an end event with a flow out, an element with no zone when there are zones, an element in a black-box pool, a boundary event on something that is not a task, `trigger` or `repeat` on the wrong kind, `"style": "illustrated"` (BPMN has one style: the shapes are the standard).
- Elements that happen at the same moment in different pools share a column when a message flow joins them, so the message runs straight up or down. Where that would put two elements on one line, pin one with `column`.
- Top level: `type`, `title`, `desc`, `zones`, `elements`, `flows`. Pool band 38 px, lanes at least 200 px, pools 40 px apart, at least 100 px between two elements where a flow carries a label.

## Limits to tell the user

- Not drawn: the legend of numbered notes under the diagram of the design's Advanced board (a `number` only puts a badge on an element), an expanded sub-process, data objects (documents held by a task), a message flow label on its own line, and the standard's other event types (conditional, link, compensation).
- A flow is placed by search among right-angled routes with at most two bends; a message flow may cross a pool but not an element. When no route is clear the build reports `line-through-node`: move an element with `column` or `row`, or shorten the labels. A crossing of two lines is only a warning.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build. A task takes the tone of its lane (or pool); events and gateways keep their own colours.

When the brief names an event without saying its type, choose from its name: "Timer", "Deadline" or "Wait" is a `timer`; a message, report or notice that is received is a `message`; "Error", "Rejected" or "Failed" is an `error` (or an `end` with `"trigger": "error"` when it ends the path); anything else is a plain `event`. A deadline on a task is a boundary `timer` with `attached_to`. A gateway that splits into alternatives is `exclusive`; one that starts or joins parallel work is `parallel`; one that waits for the first of several messages is `event_based`; say in the answer which you chose. A person's task is `user`, a system's `service`, a task that sends a message `send`, one that waits for a message `receive`.

The check reports `line-through-node`, `caption-covered` and `nodes-overlap` as errors: fix the spec (`column`, `row`, a shorter label). `lines-cross`, `lines-overlap`, `bpmn-too-many-elements` (more than 25), `bpmn-route-bends` and `bpmn-main-path` (a blue path in more than one pool) are warnings: mention them. Do not shorten a flow label to make a check pass when the build reports `label-covers`: the build moves a label along its line to find a clear spot.

Animation: a flow with `"main": true` is drawn thick, blue and animated. Message flows are static dashed lines. A diagram with no `main` flow does not move.

For a large or dense diagram (more than about 25 elements, or a hub with many lines) use sub-processes, or the `author` skill (`/flow:author`), which lays the diagram out by hand and looks at the result.
