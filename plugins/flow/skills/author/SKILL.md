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

- `Canvas.node(id, shape, text, NodeOptions(centre, icon=, tone=, number=, detail=, card=, rows=, width=, height=, screen=))`: the node is sized by the design's rules to hold its text (widened, never made taller, until it fits; at most two lines). You may force `width`/`height`.
- **ER tables:** `Canvas.node("orders", Shape.TABLE, "orders", NodeOptions(centre, rows=(Row("id", "uuid", ("PK",)), Row("customer_id", "uuid", ("FK",)), Row("note", "text?")), tone=Tone.VIOLET))` draws a table (`from flowlib.model import Row`); add `card=True, icon="cart"` for the illustrated one (tall header, name in a pill, large icon). A relation is `Canvas.edge("customers", "orders", Route(...))` with `head=Head.ZERO_MANY` and `tail=Head.ONE_ONLY` (also `ZERO_ONE`, `ONE_MANY`) for the crow's feet; leave 150 px or more between two tables that a labelled line joins.
- Node ids that look like `e1`, `e2` are kept for the lines; the kit refuses them. The first y below the title and the description is `CONTENT_TOP_PX` (160) in `flowlib.author`: start the first lane or table at or below it.
- `Box.port(side, along=0.5)` gives the attach point on `top`, `bottom`, `left`, `right`; `along` (0 to 1) moves it along the side, so a wide node or a bar can take several lines apart (`Route(leave_along=, arrive_along=)` does the same for a line). A diamond attaches only at its four tips. `canvas.boxes[id]` is the box; `box.centre` is its middle.
- `Canvas.edge(from, to, Route(...))`: with no route the line leaves and enters the facing sides. `via` is a list of waypoints; corners are added so every segment is horizontal or vertical. Between two points that differ in both x and y the added corner goes horizontal first (along x, then up or down); to turn vertical first, give that corner as a waypoint yourself. A route is `leave`, `arrive`, `via`, `role`, `label`, `words`, `dashed`, `head`.
- `Canvas.lane(...)` is a swimlane (a dark tab with the name, a lightly tinted band). `Canvas.zone(...)` is a dashed tinted group area with a name pill.
- `Canvas.text(id, words, (left, middle_y))` is free text with no outline (a heading, a note). `Canvas.legend((left, top), (Role.MAIN, Role.NO, Role.BACK))` adds a "Reading the chart" legend: a heading and, for each role, a sample line and its words (a screen flow adds its kinds of words, below). Add one to a chart that uses more than two line roles; leave room for it under the diagram.
- `Canvas.write(folder, name)` writes the scene, the HTML (animated) and the draw.io file, runs the check and returns the findings. Labels that cover a node or another label are moved along their line for you.
- Shapes: `TERMINATOR FAIL PROCESS SUBPROCESS DECISION IO DOCUMENT PREPARATION CONNECTOR START END INTERMEDIATE CYLINDER STORE BAR NOTE ACTOR TABLE`. Use a shape for what it means in the diagram type you are drawing; do not invent meanings.
- Icons: names from `flowlib.theme.icon_names()`; a card (`card=True`, with an icon and a `detail`) is the illustrated style.
- `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py check <scene.json>` re-checks a scene; `flow.py edit` changes a draw.io file in place.

## Screen flows by hand

For an app's screens (design 02) use the same pieces as the `screen-flow` skill; import `ScreenView`, `Device`, `Fidelity`, `ChipPlace`, `ScreenElement`, `LabelKind` from `flowlib.model` and `EdgeWords` from `flowlib.author`.

```python
from flowlib.author import Canvas, EdgeWords, NodeOptions, Route
from flowlib.model import Fidelity, Role, ScreenElement, ScreenView, Shape, Tone

canvas = Canvas("Checkout", "Pay or fail")
canvas.zone("pay", "Payments", Tone.TEAL, (40, 170, 1300, 400))
cart = ScreenView("S31", fidelity=Fidelity.L2, elements=(ScreenElement("Pay now"),))
canvas.node("cart", Shape.SCREEN, "Cart", NodeOptions((400, 360), tone=Tone.TEAL, screen=cart))
canvas.node("ok", Shape.DECISION, "Card approved?", NodeOptions((760, 360), width=140, height=104))
canvas.node("done", Shape.SCREEN, "Receipt", NodeOptions((1160, 360), screen=ScreenView("S32")))
canvas.node("push", Shape.TERMINATOR, "Push", NodeOptions((130, 360), detail="Entry", width=130))
canvas.edge("push", "cart", Route(words=EdgeWords("tap the push")))
canvas.edge("cart", "ok", Route(role=Role.MAIN, words=EdgeWords("tap Pay now")))
canvas.edge("ok", "done", Route(words=EdgeWords(guard="approved", effect="send receipt")))
back = EdgeWords("tap Retry", guard="declined", is_failure=True, segment=1)
route = Route(leave="bottom", arrive="bottom", via=((760, 540), (400, 540)), words=back)
canvas.edge(
    "ok", "cart", route
)  # a failure draws as a "no" line; a return could add role=Role.BACK
```

- **Screen**: `Shape.SCREEN` with `NodeOptions(screen=ScreenView(code="S31", device=Device.DESKTOP, fidelity=Fidelity.L2, elements=(ScreenElement("Pay now"),), ...))`. It is sized by the device table (phone 156 x 324, mini phone 120 x 240 with `is_mini=True`, tablet, desktop 240 x 170, watch); `width`/`height` force another size. A title is drawn on one line and its end is cut off when it is too wide: about 17 characters fit a mini phone and 24 a phone. The check warns `text-may-not-fit` for a title or an element name that is cut; shorten it or give that screen `width=` (150 holds about 23 characters on a mini phone). The id chip (`code`) sits above the frame; `chip_place=ChipPlace.ABOVE_RIGHT` or `BELOW` moves it. `elements` are the named parts that cause a transition (a red dot marks the tapped one, `is_hotspot=False` turns it off); `overlay=Overlay.SHEET`, `tab_active=`, `tab_count=` and `is_undecided=True` work as in the spec. `ScreenView` without `fidelity` is L0.
- **L0 (names only)**: a rounded card as wide as its device and 96 px high, much lower than a frame, so rows of cards can sit closer than rows of phones. It shows the id chip inside its top-left corner, a small device icon at the top right and the name in 13 px bold at the bottom; it has no `elements`. Give every screen a `code`: it is the chip, and the words a reader uses to point at a screen. Write `S` and two digits for an app screen, the first digit for its group in the order of the flow (`S01`, `S02` in the first group, `S11` in the second), and `W` and two digits for a web screen. A decision, an entry pill and a flag have no code. The name is one line: about 19 characters fit a phone card, 13 a mini card and 29 a desktop card. The check warns `text-may-not-fit` when a name is cut; shorten it, or give the card `width=`. Write names as words in sentence case (`Payment methods`, not `PaymentMethods`), as the design asks for every node.
- **Decision**: `Shape.DECISION` as usual. **Entry pill**: a `Shape.TERMINATOR` with a `detail` line that names the kind of way in (`Launch`, `Push`, `Link`), not the name again; it is green by default. The design puts the entry pills in **one column at the left** of the flow, each at the height of the screen it opens so its line runs straight in. Plan the rows for it before anything else: put each screen an entry opens at the left end of its row (`In trip` first in the Trip row, `Promo code` first in its row), so the pill beside it needs a short straight line and crosses nothing. Only when a screen must stay in the middle of a row, run the entry line in a channel between two rows of zones, never across a zone. The entry zone is the narrow column that holds the pills; it may be tall with gaps between pills when the screens they open are in different bands. Do not split it into two frames.
- **Zone**: `Canvas.zone`, one per group of the brief; never draw two frames with the same name. Put a screen inside a zone only if the brief puts it there. When the brief lists connections paragraph by paragraph ("In Booking: From X ...") and not the members of each group, put a screen in the group whose paragraph first has it as a source ("From X"), and a screen that is only ever a target in the group of the screen that leads to it; say in your report which screens you placed by this rule. A zone is a rectangle; leave the gap between two zones wider than the widest chip that sits on a line crossing it (about 140 px), or put the words on a stretch inside one zone with `segment=`, or the check warns that the chip of the line straddles a border.
- **Arrow words** `EdgeWords(trigger=, system_icon=, guard=, effect=, is_failure=)` on `Route(words=...)` build `trigger [guard] / effect` for you: a dark chip for what the person does, a slate chip with an icon (`clock`, `cloud`, `bolt`, `phone`) for what the system does, the guard in square brackets (green; rose and a red line for `is_failure=True`), the effect after a slash. Write the guard and the effect without the brackets or the slash. Keep each under about 20 characters (the check warns `label-too-long`). When the brief's own words are longer (`click Request invoice`), either shorten them and keep the meaning (`click Invoice`), or give the arrow a code: `EdgeWords("click Request invoice", code="C1")` draws only `C1` on the arrow, and `canvas.conditions((left, top))` adds the Conditions table under the diagram with one row per coded arrow (`W03 → W05 · click Request invoice [guard] / effect`), as the automatic screen flow does with `"conditions": "coded"`. Number the codes C1, C2 in the order of the flow. `segment=` picks the stretch of the line (default the longest), `along=` how far along it, `shift=(dx, dy)` nudges. On a vertical stretch the words go beside the line: left of it when the line runs down the left half of the screen it leaves or enters, right of it otherwise, so a back-and-forth pair (`leave_along=0.3` one way, `0.7` the other) carries its words outside the pair. `is_left=True` or `False` forces a side. Words and `label=` cannot be mixed.
- Chips that cover a screen, or that sit on another line, are slid along their own line to a clear place, the guard and the effect with them. A chip wider than the gap between two screens cannot be, so leave 140 px or more between screens that a line with words joins. When no clear place exists, the check warns `label-on-line` (the chip names the wrong line to a reader) or `label-covers`; move the chip with `segment=`/`along=`, or move a line.
- **Legend of a screen flow**: `canvas.legend((left, top), (Role.MAIN, Role.NEXT, Role.BACK), (LabelKind.USER, LabelKind.SYSTEM, LabelKind.GUARD_OK, LabelKind.GUARD_FAIL))` adds, after the lines, a sample of each kind of words with what it means (a dark chip for the person, a slate chip for the system, the green and rose guards; also `EFFECT` and `CODE`). List only the kinds the diagram uses.
- **Long returns** (a line back to the start or to the home screen): never run them through a screen or through the middle of a zone. Give each its own row in a channel in the gap between two rows of zones, or in a column at the left or right edge of the page, about 20 px apart, and send it there with `via` waypoints; put its words on a long stretch (`segment=`). Two returns with the same words (for example `tap Confirm`) need distinct arrival points (`arrive_along`) so they are not mistaken for one line. If a return would run most of the page, check whether the brief needs it drawn at all; drawn or not, say so in the report.

## Theme

Set `canvas.theme = "technical"` or `"midnight"` (default `"pastel"`) before `canvas.write(...)` to restyle the whole diagram in HTML and draw.io; an unknown name raises `ValueError`. Details in the flowchart skill ("Themes"). On `midnight` pick tones for the owner or domain as usual; the colours are swapped for you. Do not write colours by hand.

## The design to follow

**Shapes by meaning** (flowchart): terminator = start or end (green pill, a failed end is rose); process = one action (blue box); decision = a question (amber diamond); IO = data in or out (violet parallelogram); document = a readable output; subprocess = a step with its own chart; preparation = setup (teal); connector = off-page link, one letter. A database is a cylinder only in diagram types that have one (architecture, DFD, ER); a flowchart has none.

**Colour**: six tones, `blue violet amber green teal gray`. A tone groups things by owner or domain and never means anything by itself (courier is teal everywhere). Shape colours follow the shape (decision amber, terminator green). Line colours are for line roles only.

**Line roles** (`Role`): `main` = the one most important path, thick, blue, animated; `data` = a data or event stream, violet, animated slowly; `yes` green and `no` rose for decision exits; `back` = dashed slate, a return or retry; `next` = a plain step, ink. Mark the main path with `main` on every line of that chain (one connected route from the start to an end) so the page moves; everything else stays still.

**Text**: a process starts with a verb (`Check stock`); a terminator names the state (`Order placed`); a decision is a question ending with `?`. Four words or fewer, **sentence case** (use `sentence_case`; names with capitals inside, such as `RIB` or `Adj-RIB-In`, are kept), never wrapped by hand. A decision with two exits labels them `Yes` and `No`; with more, label each with its value and the last `Else`. Edge labels are short.

**Illustrated style** (when the user asks for it): this is a different look, not a few decorations. In the design's illustrated flowchart almost every **work step is a card**: a name pill, one short line of explanation (six words or fewer) and a large detailed icon, tinted by the lane or group it sits in. Only decisions (diamonds), starts and ends (pills) and connectors (circles) keep their shapes, so the shape grammar still reads at a glance. `NodeOptions(centre, icon="cart", detail="Save the items", tone=Tone.VIOLET, card=True)`.
- Make **every process, subprocess and document step a card**, unless the user says to keep some plain. A chart where only a few steps are cards reads as a plain chart with decoration; do not do that.
- Every card needs an icon and a detail line. Pick the icon by the noun of the step (a payment is `card`, an order is `cart`, a database is `database`, a message is `mail`, a check is `check`); the same thing gets the same icon everywhere. Look at the names in `flowlib.theme.icon_names()` and choose the closest; when the step's words are placeholders, vary the icons anyway so neighbouring cards do not look identical. If the brief gives no detail text, write a short one from the step name.
- A card takes the tone of its lane or group (`tone=` the lane's tone), so the owner of the step is clear before reading. Give each lane or group its own tone.
- A card is about 180 px wide and 150 to 190 px tall including its pill and detail; its sides are the box's sides, so attach lines to its top, left, right and bottom as usual. Leave 70 px or more between cards in a row, more where a line carries a label, and plan the page size for cards from the start: a lane that holds cards is about 240 px tall.
- Give number chips (`number="3"`) when other text refers to steps.

**BPMN** (when the diagram is a business process across teams or companies): the notation is fixed, so keep its shapes. Start = `Shape.START`, end = `Shape.END`, a timer, message or error event = `Shape.INTERMEDIATE` with the icon `clock`, `mail` or `warn`; a gateway = `Shape.DECISION` with the icon `x` (exclusive: one exit), `plus` (parallel: all exits); a task = `Shape.PROCESS` written as verb and noun. A pool is a `Canvas.lane` (the name on the tab); a lane inside a pool is another `lane`. A sequence flow is a plain line inside a pool. A **message flow** between pools is `Route(dashed=True, head=Head.OPEN, tail=Head.DOT, role=Role.DATA)`: dashed, an open circle at its start, a hollow head. A return or retry is dashed slate (`Role.BACK`). Time runs left to right: elements that happen at the same moment in different pools share an x position, so message flows run straight up and down. A decision sends its alternative branch into a second row and the happy path stays on the first. Pools are at least 200 px tall, stacked with about 40 px between them; leave 100 px or more between elements where a flow carries a label. A message flow may cross a pool but never an element. A gateway drawn with its mark (`icon="x"` or `"plus"`) shows its name as a caption under it, so a small diamond stays readable. One main path (blue, animated) for the whole diagram, not one per pool; where the path passes from one pool to another, give that message flow `role=Role.MAIN` too (still dashed, with its open circle) so the blue path stays unbroken. Illustrated BPMN: the design keeps the standard shapes for events and gateways, so only a few important tasks become cards (an icon and one detail line); everything else stays standard.

**Layout**: the happy path stays on one straight line; exceptions branch to the side or down. Steps in a row share a centre line. Gaps: 56 px or more between rows, 70 px or more between columns, more where a line carries a label. Return lines run *outside* the flow, never through a step. Snap positions to a 10 px grid. In a swimlane chart a step sits in exactly one lane, the actor who starts is in the top lane, a line that changes lane runs straight across.

**Arranging** (your judgement, but think about these):
- Keep the page readable at normal zoom: aim for no more than about 3000 px wide and 2500 px tall. A long chain of steps should be folded into a column or into rows, not left as one very long row.
- A node that many lines meet (a hub) can be a tall bar or a wide band so the lines arrive in parallel and apart, instead of bunching into one point.
- Put what belongs together close and group it in a lane or a zone; put the main path where the eye starts (top left) and let it run to the end.
- Use the space. If a large part of the page is empty (a corner, half of a zone), move things so the diagram is compact: put the legend under or beside the diagram where it does not leave a hole, shrink zones to their contents, and bring far-apart groups closer. An empty zone corner is a sign the arrangement can be tighter.
- Give a hub or a big shared node a `tone` (`NodeOptions(tone=Tone.AMBER)`) so it stands out from its neighbours; any shape takes a tone, which tints its fill.
- Avoid several near-parallel lines closer than about 12 px, and lines that cross a whole page. Move a node, change the side a line uses, or give a line a waypoint.
- A long chain of steps inside one lane (more than about eight) is folded: continue it on a second row inside the same lane (make the lane taller) or let the chain turn back under itself, rather than running one row across a very wide page.
- Many return lines into one node: send them along a channel inside the top (or bottom) edge of the lane, one line per row of the channel about 12 px apart, and give each its own arrival point along the node's top edge. Order them so that the line coming from farthest away has the highest row and arrives leftmost, and none of them cross. If a return line would be longer than about half the page, put a connector (`Shape.CONNECTOR`, one letter) at each end instead.
- `detail` also works on plain nodes (a second, smaller line under the name).
- Use one icon style per diagram. In the illustrated style the work steps are cards; in the plain style none are.

## Looking

You cannot judge a layout from numbers. Render the HTML to an image and open it: with Chromium and Playwright if they are installed (`python3 -c "from playwright.sync_api import sync_playwright"` tells you; if Playwright's own browser is missing but Chrome is installed, launch with `channel="chrome"`), or any other renderer you have, then read the PNG. If the page is larger than the screenshot, crop and resize it. If you have no way to see the picture, say so plainly, rely on the check report, and keep the arrangement simple.

## Do not

- Do not use `flow.py build` for the diagram you are authoring by hand; it applies the automatic layout and ignores your positions.
- Do not edit the plugin's code. If the kit lacks something you need, write it in your own script and say so in your report.
- Keep the brief's step names recognisable. The design wants a decision to be a question and a process to start with a verb, so reword where needed, but a reader should be able to match every step to the brief; keep a list of the mapping in your script.
- A step that the brief puts in a group belongs in that group's area. If the layout needs it elsewhere, say so in your report.
- Do not drop a step or a connection to make the layout easier. If the brief cannot be expressed, say what and why.
