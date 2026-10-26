---
description: Lay out a diagram by hand, in a script of your own, when the automatic layout of the other Flow skills is not good enough (long or dense flows, many groups, a hub with many lines). You choose every position and route, in the Flow design, and write HTML and draw.io files. Use for large or complex diagrams, or when the user wants the best result rather than the quickest.
allowed-tools: Bash(python3 *)
---

# Author a diagram by hand

The other Flow skills turn a short spec into a diagram with one fixed automatic layout. That is quick and fine for small diagrams. For a big or dense one it gives long pages, bundles of lines and wasted space. Here you do the layout yourself: you decide the arrangement, write a small Python script that places everything, build it, **look at the picture**, and change the script until it is good. The kit keeps the design (sizes, colours, line roles, files); the arrangement is yours.

## Steps

1. Read the brief. List every step and every connection, and keep the list: every one must appear.
2. Decide the arrangement before you write code. See "Arranging" below. Sketch the rows and columns in a comment.
3. Write `make.py` next to the output (the script stays with the diagram, so it can be changed later). Use the kit, below.
4. Run it. Read the check report. Fix every error; read every warning.
5. Look at the picture (see "Looking"). Ask: is the main path easy to follow, is there wasted space, are any lines bundled or very long, are any labels hard to read, are the groups clear? Change the script. Repeat at least three times; stop when you would be happy to show it.
6. Report what you drew, the check result, and what is still weak. Do not say it looks good unless you looked.

## The kit

```python
import sys

sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
from flowlib.author import Canvas, NodeOptions, Route, Side, sentence_case
from flowlib.check import format_report
from flowlib.model import Role, Shape, Tone

canvas = Canvas("Title", "One sentence of description")
canvas.lane("ops", "Operations", Tone.BLUE, (40, 120, 1800, 240))  # left, top, width, height
canvas.zone("core", "Core", Tone.GREEN, (400, 420, 600, 300))  # a group area
canvas.node("go", Shape.TERMINATOR, "Start", NodeOptions((200, 240)))  # centre point
canvas.node("ok", Shape.DECISION, "Valid?", NodeOptions((420, 240), tone=Tone.AMBER))
canvas.edge("go", "ok")  # sides that face each other
canvas.edge(
    "ok",
    "go",
    Route(
        leave=Side.BOTTOM,
        arrive=Side.BOTTOM,
        via=((420, 330), (200, 330)),
        role=Role.BACK,
        label="Retry",
    ),
)
findings = canvas.write("out", "diagram")  # writes out/diagram.scene.json, .html, .drawio
print(format_report(findings))
```

- `Canvas.node(id, shape, text, NodeOptions(centre, icon=, tone=, number=, detail=, card=, width=, height=))`: the node is sized by the design's rules to hold its text (widened, never made taller, until it fits; at most two lines). You may force `width`/`height`.
- `Box.port(side, along=0.5)` gives the attach point on `top`, `bottom`, `left`, `right`; `along` (0 to 1) moves it along the side, so a wide node or a bar can take several lines apart (`Route(leave_along=, arrive_along=)` does the same for a line). A diamond attaches only at its four tips. `canvas.boxes[id]` is the box; `box.centre` is its middle.
- `Canvas.edge(from, to, Route(...))`: with no route the line leaves and enters the facing sides. `via` is a list of waypoints; corners are added so every segment is horizontal or vertical. A route is `leave`, `arrive`, `via`, `role`, `label`, `dashed`, `head`.
- `Canvas.lane(...)` is a swimlane (a dark tab with the name, a lightly tinted band). `Canvas.zone(...)` is a dashed tinted group area with a name pill.
- `Canvas.text(id, words, (left, middle_y))` is free text with no outline (a heading, a note). `Canvas.legend((left, top), (Role.MAIN, Role.NO, Role.BACK))` adds a "Reading the chart" legend: a heading and, for each role, a sample line and its words. Add one to a chart that uses more than two line roles; leave room for it under the diagram.
- `Canvas.write(folder, name)` writes the scene, the HTML (animated) and the draw.io file, runs the check and returns the findings. Labels that cover a node or another label are moved along their line for you.
- Shapes: `TERMINATOR FAIL PROCESS SUBPROCESS DECISION IO DOCUMENT PREPARATION CONNECTOR START END INTERMEDIATE CYLINDER STORE BAR NOTE ACTOR TABLE`. Use a shape for what it means in the diagram type you are drawing; do not invent meanings.
- Icons: names from `flowlib.theme.icon_names()`; a card (`card=True`, with an icon and a `detail`) is the illustrated style.
- `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py check <scene.json>` re-checks a scene; `flow.py edit` changes a draw.io file in place.

## The design to follow

**Shapes by meaning** (flowchart): terminator = start or end (green pill, a failed end is rose); process = one action (blue box); decision = a question (amber diamond); IO = data in or out (violet parallelogram); document = a readable output; subprocess = a step with its own chart; preparation = setup (teal); connector = off-page link, one letter. A database is a cylinder only in diagram types that have one (architecture, DFD, ER); a flowchart has none.

**Colour**: six tones, `blue violet amber green teal gray`. A tone groups things by owner or domain and never means anything by itself (courier is teal everywhere). Shape colours follow the shape (decision amber, terminator green). Line colours are for line roles only.

**Line roles** (`Role`): `main` = the one most important path, thick, blue, animated; `data` = a data or event stream, violet, animated slowly; `yes` green and `no` rose for decision exits; `back` = dashed slate, a return or retry; `next` = a plain step, ink. Mark the main path with `main` on every line of that chain (one connected route from the start to an end) so the page moves; everything else stays still.

**Text**: a process starts with a verb (`Check stock`); a terminator names the state (`Order placed`); a decision is a question ending with `?`. Four words or fewer, **sentence case** (use `sentence_case`; names with capitals inside, such as `RIB` or `Adj-RIB-In`, are kept), never wrapped by hand. A decision with two exits labels them `Yes` and `No`; with more, label each with its value and the last `Else`. Edge labels are short.

**Illustrated style** (when the user asks for it): a work step can be a **card**: `NodeOptions(centre, icon="cart", detail="Save the items", tone=Tone.VIOLET, card=True)` gives a name pill, one short line of explanation (six words or fewer) and a large detailed icon. Use cards for the steps people must notice, not for every step: decisions stay diamonds, start and end stay pills, connectors stay circles, so the shape grammar still reads at a glance. A card takes the tone of its lane or group, so the owner of the step is clear before reading. Pick the icon by the noun (a payment is `card`, an order is `cart`, a database is `database`); the same thing gets the same icon everywhere. A card is about 180 px wide and 150 to 190 px tall including its pill and detail, and its sides are the box's sides: attach lines to the card's top, left, right and bottom as usual. Leave more room around cards than around plain nodes and check the page size again. Give number chips (`number="3"`) when other text refers to steps.

**Layout**: the happy path stays on one straight line; exceptions branch to the side or down. Steps in a row share a centre line. Gaps: 56 px or more between rows, 70 px or more between columns, more where a line carries a label. Return lines run *outside* the flow, never through a step. Snap positions to a 10 px grid. In a swimlane chart a step sits in exactly one lane, the actor who starts is in the top lane, a line that changes lane runs straight across.

**Arranging** (your judgement, but think about these):
- Keep the page readable at normal zoom: aim for no more than about 3000 px wide and 2500 px tall. A long chain of steps should be folded into a column or into rows, not left as one very long row.
- A node that many lines meet (a hub) can be a tall bar or a wide band so the lines arrive in parallel and apart, instead of bunching into one point.
- Put what belongs together close and group it in a lane or a zone; put the main path where the eye starts (top left) and let it run to the end.
- Use the space. If a large part of the page is empty (a corner, half of a zone), move things so the diagram is compact: put the legend under or beside the diagram where it does not leave a hole, shrink zones to their contents, and bring far-apart groups closer. An empty zone corner is a sign the arrangement can be tighter.
- Give a hub or a big shared node a `tone` (`NodeOptions(tone=Tone.AMBER)`) so it stands out from its neighbours; any shape takes a tone, which tints its fill.
- Avoid several near-parallel lines closer than about 12 px, and lines that cross a whole page. Move a node, change the side a line uses, or give a line a waypoint.
- Use one icon style per diagram. Cards (illustrated) are for the few steps people must notice, not for every step.

## Looking

You cannot judge a layout from numbers. Render the HTML to an image and open it: with Chromium and Playwright if they are installed (`python3 -c "from playwright.sync_api import sync_playwright"` tells you), or any other renderer you have, then read the PNG. If the page is larger than the screenshot, crop and resize it. If you have no way to see the picture, say so plainly, rely on the check report, and keep the arrangement simple.

## Do not

- Do not use `flow.py build` for the diagram you are authoring by hand; it applies the automatic layout and ignores your positions.
- Do not edit the plugin's code. If the kit lacks something you need, write it in your own script and say so in your report.
- Keep the brief's step names recognisable. The design wants a decision to be a question and a process to start with a verb, so reword where needed, but a reader should be able to match every step to the brief; keep a list of the mapping in your script.
- A step that the brief puts in a group belongs in that group's area. If the layout needs it elsewhere, say so in your report.
- Do not drop a step or a connection to make the layout easier. If the brief cannot be expressed, say what and why.
