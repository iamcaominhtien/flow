---
description: Draw a flowchart (steps, decisions, loops, optional swimlanes, top-to-bottom or left-to-right) as an animated HTML page and a draw.io file from a short description. Use when the user asks for a flowchart, a process flow, or the steps and decisions of a procedure.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Flowchart

You write a short **spec** (the steps and how they connect). A script places every box, routes the lines, checks the result and writes the HTML. Never write coordinates or HTML yourself.

Scope today: flowcharts in the plain style, top to bottom or left to right, with or without swimlanes. For anything else (illustrated, other diagram types such as ER or architecture), say that it is not built yet. For the order of messages between systems, use the sequence skill.

## Steps

1. Work out the steps, the decisions and the places where the flow loops back. Ask only if the process is unclear.
2. Write `<name>.spec.json` in a `diagrams/` folder of the current project (create it if needed).
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` (view and share) and `<name>.drawio` (open and edit in draw.io) next to the spec, and prints a check report.
4. Read the report. Exit code 0 means no error; 2 means errors were found (the files are still written); 1 means the spec is invalid and the message lists every problem.
5. Fix errors by changing the spec (see below) and build again, at most three rounds. Warnings may stay; mention them.
6. Tell the user where the HTML and the `.drawio` file are and what, if anything, the check still reports. Do not say a diagram "looks good": you have not seen it.

## The spec

```json
{
  "type": "flowchart",
  "title": "Place an order",
  "desc": "One sentence that says what the chart shows.",
  "nodes": [
    {"id": "start", "kind": "terminator", "text": "Customer opens the app"},
    {"id": "pay", "kind": "process", "text": "Pay by card", "icon": "card", "tone": "amber"},
    {"id": "ok", "kind": "decision", "text": "Payment accepted?"}
  ],
  "edges": [
    {"from": "start", "to": "pay"},
    {"from": "pay", "to": "ok"},
    {"from": "ok", "to": "start", "role": "back", "label": "Retry"}
  ]
}
```

- `kind`: `terminator` (start or end, green), `process` (one action, blue), `decision` (a question, amber), `io` (data in or out, violet), `document` (a readable output), `subprocess` (a step with its own chart), `preparation` (setup, teal), `fail` (a failed end, rose), `connector` (off-page link, one letter).
- `role` of an edge: `next` (default, a normal step), `yes`, `no`, `back` (returns to an earlier step), `main` (the one most important path, drawn thick and animated), `data` (an event or data flow, drawn violet and animated slowly). Use `main` on at most one connected path.
- Optional on a node: `detail` (a small second line under the text), `icon` (one of `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`), `tone` (`blue violet amber green teal gray`, marks the owner or domain, never a meaning), `number` (a short chip such as `3`), `side` (`left` or `right`, asks for a branch on that side).
- Edge `label`: short; `Yes` and `No` for decision exits.
- `direction`: `down` (default) for up to about ten steps, `right` for pipelines and timelines. Never mix them.
- Swimlanes: add `"lanes": [{"id": "support", "label": "Support", "tone": "violet"}, ...]` and give every node a `"lane"`. One lane per actor (person, team or system); the actor who starts goes first. Swimlanes read best with `"direction": "right"`. A step sits in exactly one lane, and with lanes the `side` hint is ignored.

## Writing good content

- A process starts with a verb (*Check stock*). A terminator names a state (*Order placed*). Four words or fewer, sentence case. Do not break lines yourself; the script wraps and widens boxes.
- A decision is a question that ends with `?`. It has at least two exits, labelled `Yes` and `No`. Give the exit that continues the happy path the role `yes` so it stays straight; the other exit leaves sideways. A decision with one exit is a process.
- A line that returns to an earlier step has the role `back`. Never draw a loop with a normal edge.
- Every step except the first has an incoming edge, and every step except an end has an outgoing one. About ten steps fit one chart; split a larger process with a `subprocess` step.
- Pick icons only where they help a reader scan; skip them on most nodes.

## Reading the report

`line-through-node`, `nodes-overlap`, `label-covers` and `outside-canvas` are errors. `text-may-not-fit` and `lines-cross` are warnings. Fix an error by:

1. Shortening the text of the nodes involved.
2. Moving a branch with `side`, or changing which exit has the role `yes`.
3. Splitting the chart into two with a `subprocess` or a `connector`.

If those steps do not clear an error, fix it by hand with an **overrides** file next to the spec, `<name>.overrides.json`. Read the positions in `<name>.scene.json`, then write only what changes:

```json
{"nodes": {"pay": {"x": 120, "y": 340}},
 "edges": {"e3": {"points": [[10, 10], [10, 90]], "label_at": [30, 50]}}}
```

`x` and `y` are the top-left corner of a node; edge ids are `e1`, `e2`... in spec order; a route is a list of `[x, y]` points that runs along horizontal and vertical segments. The build applies the file to both the page and the draw.io file, so a fix is kept when you rebuild. Moving a node does not move its lines: re-route them in the same file. Do not edit the HTML or the `.drawio` file by hand: a rebuild would overwrite the edit.

## Themes

Add `"theme"` at the top level of any spec, of any type, to pick the look: `pastel` (the default: soft tints, radius 10, stroke 2, shadow on the draw.io boxes, animated main path), `technical` (for UML, ER and C4: white boxes with slate outlines, radius 4, stroke 1.5, no shadow, solid lines and no animation) or `midnight` (dark slides: background `#0B1220`, light text, dark tints with bright outlines, radius 12). The HTML page and the `.drawio` file both use it, including the page background. An unknown name is an error that lists the three. In draw.io the lines are written with the weights of the design (main path 3 wide, data stream 1, other lines 2) and the animation runs at 500 ms and 1500 ms.

## Illustrated style

Add `"style": "illustrated"` at the top level to draw each box that has an `icon` as a card: a large icon on a tinted disc, the name in a pill, and the `detail` text under it. Boxes without an icon stay plain. Cards are bigger, so use it for a few boxes (about eight or fewer), give each a `tone` and a short `detail`, and keep names short: the name stays on one line. The default is `"style": "plain"`. Icons with a detailed drawing (shaded, with a highlight and a ground shadow) show it on a card in place of the disc: `bell calendar card cart chat cloud code database file folder globe key lock mail phone pot refund search server store user warn wifi`. More names that exist only in the detailed set and can be used in any spec: `admin api-gateway approved-doc backup-archive bar-chart batch-scheduler block-storage bot browser bucket cache cdn ci-cd cluster container container-registry containers courier cpu dashboard data-lake data-warehouse dns email-service error event event-stream file-storage firewall firewall-waf flag function gateway id-card idea identity-iam in-memory-cache info json kubernetes laptop launch load-balancer logging message-queue ml-model money monitoring nosql-database object-storage package pie-chart pipeline plugin private-network pub-sub pub-sub-topic queue region schedule secrets security serverless-function sql-database start stop success table target team terminal virtual-machine virtual-network workflow`.

## Known limits

Back edges between two nodes on the same row arc over the top and meet the incoming line of their target. Several back edges that start from the same node share a side. Text width is estimated, not measured. In the `.drawio` file, edge labels are plain text with a background (no rounded chip), and the fonts Inter and JetBrains Mono must be installed or draw.io substitutes another font. Nothing here has been run in claude.ai or Cowork.

## Icons

Built-in icon names: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. When none fits, draw one: write `icons.local.json` next to the spec, an object of name to the inner SVG of a 24 x 24 line icon, for example `{"teapot": "<path d=\"M6 9h10v6a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4z\"/>"}`. Allowed elements: `path circle ellipse rect line polyline polygon g`. Allowed attributes: `d cx cy r rx ry x y width height x1 y1 x2 y2 points`, with coordinates between -2 and 26. Names are lowercase letters, digits and `-`, and must not reuse a built-in name. The build refuses anything else with exit code 1 and says why. Keep the icon file with the spec; the scene and overrides files live there too.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
