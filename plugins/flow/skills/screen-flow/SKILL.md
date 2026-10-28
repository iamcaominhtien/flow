---
description: Draw a screen flow (the screens of an app and how a person moves between them) as an animated HTML page and a draw.io file. Use when the user asks for a user flow, a screen flow or an app navigation map.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Screen flow

You write a short **spec**. A script places the screens in device frames, routes the arrows, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Ask, or pick from the stage of the design, the **fidelity** of each screen: L0 names only, L1 skeleton, L2 key elements (see below). There is no default level in the design; a screen with no `fidelity` is drawn as L0.
2. List the screens (device, id, name), the decisions, the entry points and the arrows: what the person does, which condition decides the path, what happens on the way.
3. Put the screens in zones. For up to about 12 screens give each an `at: [row, column]` (flow runs left to right in a row; a branch goes to the next row). With more, leave `at` out and let the script arrange the zones (see Layout). Draw a web flow as its own zone below the phone flow.
4. Write `diagrams/<name>.spec.json` in the current project.
5. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
6. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good" unless you have looked at the picture.
7. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "screen",
  "title": "Shop app: checkout",
  "zones": [{"id": "co", "label": "Checkout", "tone": "violet"}],
  "screens": [
    {"id": "cart", "code": "S13", "label": "Cart", "device": "phone", "size": "mini",
     "fidelity": "L2", "zone": "co", "at": [0, 0], "elements": ["Checkout"]},
    {"id": "pay", "code": "S21", "label": "Payment", "device": "phone", "size": "mini",
     "fidelity": "L2", "zone": "co", "at": [0, 1], "elements": ["Pay"]},
    {"id": "ok", "kind": "decision", "label": "Payment ok?", "trigger": "API result",
     "system": "cloud", "at": [0, 2]},
    {"id": "done", "code": "S22", "label": "Done", "device": "phone", "size": "mini",
     "fidelity": "L2", "content": "success", "at": [0, 3]}
  ],
  "taps": [
    {"from": "cart", "to": "pay", "trigger": "tap Checkout", "guard": "cart not empty", "main": true},
    {"from": "pay", "to": "ok", "trigger": "tap Pay", "main": true},
    {"from": "ok", "to": "done", "guard": "paid", "effect": "send receipt", "main": true},
    {"from": "ok", "to": "pay", "guard": "declined", "kind": "failure"}
  ]
}
```

Top level: `type` (`screen`), `title`, `desc`, `theme` (see the flowchart skill), `zones`, `screens`, `taps`, `buses`, `conditions` (`inline` default, or `coded`), `tab_count` (tabs in a tab bar, default 4), `captures` (the manifest of L4 screenshots).

### Screens and ids

- **Item**: `id` (any name you use in `taps`), `label` (the name), `kind`, `at: [row, column]`, `zone`, `tone`.
- **Kinds**: `screen` (default), `decision` (a diamond, no id), `start`, `end`, `entry` (a green pill in the left column; `label` is its source: App icon, Push, Deep link; `detail` a second line; `at` is `[row]`), `flag` (an off-page mark with `label` and `detail`, such as "To Checkout flow" and "diagram 02"), `tab` (one tab of a bar, with an `icon`).
- **Screen id chip**: `code` is the id written on the chip, `S` and two digits (group digit: 0 onboarding, 1 browse, 2 checkout, 3 account), `W` for web (W01). Default: the `id`. A state of one screen shares its id: `"code": "S31", "state": "loading"` is `S31 · loading`. An overlay drawn on the screen it covers: `"overlay": "modal"` (or `sheet`, `toast`) gives `S12 + modal`. Give an overlay its own code only if it has onward arrows of its own.
- **Device**: `device` is `phone` (default), `tablet`, `desktop` (a browser bar) or `watch`; `orientation` is `portrait` or `landscape`; `"size": "mini"` draws a phone at 120 × 240 for diagrams with many screens; `"size": "large"` draws any device at twice its size, so an L4 screenshot can be read on the page (the layout makes room). Sizes: phone 156 × 324, tablet 164 × 236, desktop 240 × 170, watch 80 × 96 (landscape swaps them). Use the frame that matches the platform; never a badge. A title is drawn on one line and cut off when too wide: about 17 characters fit a mini phone, 24 a phone; the check warns `text-may-not-fit` when one is cut.
- **Fidelity** `L0` to `L4`. Every level has the width of the device frame and the same centre line, so raising a screen never moves an arrow.
  - `L0`: a rounded card with the id and the name, 96 px high. The name is one line: about 19 characters fit a phone card, 13 a mini card and 29 a desktop card; the check warns when one is cut.
  - `L1`: a frame with the same generic skeleton and "content TBD".
  - `L2`: only the elements that cause a transition are drawn and named, the rest is hatched. `elements` is a list; each is a string (a primary button with a red dot where it was tapped) or an object `{"text", "style": "primary|secondary|outline|danger|field", "at": "top|bottom", "on": "overlay", "hotspot": false}`. `hatch` is the text of the hatched block (default "other content"). `content` replaces it with `splash`, `success`, `error`, `loading` or `empty`. `tab: 1` draws a tab bar with the second tab active.
  - `L3`: a full wireframe. Give the screen `blocks` (the same blocks as the wireframe skill: navbar, card, list item, form field, button, table and so on, placed by row, column and span; a block with `"tap": true` gets the red dot). They are drawn at 0.6 of a phone (0.5 tablet, 0.35 desktop), so small text is a structure, not a reading size. Blocks are read only at L3. An L3 screen with `elements` and no `blocks` is drawn as L2.
  - `L4` (as built): a screenshot of the running app in the frame, under the screen's name. Take the screenshots with `capture.js` (see "Screens as built" below), then name the manifest once at the top of the spec, `"captures": "captures/manifest.json"`, and each L4 screen by its code, `"capture": "W02"`. A capture can also be written out: `"capture": {"image": "captures/S01.png", "source": "src/pages/Login.tsx", "hotspots": [{"text": "Sign in", "box": [24, 295, 342, 50]}]}`; paths are read from the spec's folder. The screenshot is fitted to the width of the body and cut at its bottom; each hotspot (left, top, width, height in the screenshot's pixels) gets the red dot. In the HTML a click on the screenshot opens it full size. The check reports a missing or broken file (error), a screenshot of the wrong width for its device, one older than its `source`, a hotspot outside it, and more than 8 MB of screenshots (warnings).
  - `"undecided": true`: a dashed card with a TBD tag; the arrows into it are dashed.
- **Overlays**: `overlay`, `overlay_title` (the title of a modal or the text of a toast); elements with `"on": "overlay"` belong to the overlay (the buttons of a modal, the rows of a sheet).

### Arrows

An arrow is written `trigger [guard] / effect`.

- `trigger`: a chip. Dark when the user does it (verb plus target: tap Login, click product, swipe left). Slate with an icon when the system does: add `"system": "clock"` (time), `bolt` (event), `shield` (permission), `cloud` (API result), `phone` (device action). Use tap on touch, click on desktop.
- `guard`: lower case, in brackets. Green on the success path, rose when `kind` is `failure`.
- `effect`: grey, after a slash.
- `kind`: `forward` (default), `main` (the happy path: blue, thick, animated; or `"main": true`; only one route per diagram), `failure` (rose), `back` (dashed slate, runs in a strip above the row), `retry` (dashed slate, returns to an earlier screen).
- `route` (optional): `direct` keeps a back arrow straight between two frames, `elbow` leaves the top or bottom of the source and turns once into the side of the target.
- `code`, `conditions: "coded"`: a label longer than about 20 characters, or shared by several arrows, becomes a code (C1, C2) on the arrow and a table below the diagram. The check warns about a long label.
- Old specs still work: a spec with only `label` and `style` (`tap`, `back`) is drawn as plain boxes as before.

### Layout

- Rows and columns come from `at`. Gap between frames: 130 px when an arrow carries a chip, 96 px otherwise. Arrows leave the middle of the facing edge; two arrows between the same frames use the upper and lower third.
- **Arrows never cross a frame.** A neighbour arrow is straight; a diagonal one runs in the channel between two rows. Any other arrow, and every `back` or `retry` that cannot turn once, runs in the free lanes between rows and columns (or round the outside of the grid) and gets a slot of its own, so that two returns never run on top of each other. A return in the same row runs in a strip above the row.
- **Words** (trigger chip, guard, effect) sit on the longest free stretch of their line, clear of frames, id chips, zone labels and other words. If a stretch is taken they move along the line.
- **No `at`: automatic arrangement.** A screen with no `at` is placed by zone. Each zone is a block; its screens are read left to right in the order of the flow (steps from where the flow enters the zone) and wrap in whole rows: a row is filled before the next begins, and the next row starts at the left (a zone is at most 5 columns wide, rows balanced). Blocks sit on shelves from the left, up to 9 columns, in the order of the flow; a zone with desktop screens goes below the app zones; the tabs of a bar stay on one row. A screen or decision with no zone joins the zone of a neighbour in the flow. You can mix: screens with `at` stay, the others are arranged below them.
- `zones`: `id`, `label`, `tone` (`blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`). Each is a dashed tinted frame with a pill; the id chip takes the zone colour. A zone is the box around its screens, so keep a zone's screens next to each other.
- Rows of desktop screens are laid out in their own columns: the web flow goes in its own zone below the app flow.
- **Tab bar**: one `tab` item per tab on one row, and `"buses": [{"trigger": "tap any tab", "to": ["tab1", "tab2"]}]`. The bar is drawn once as a bus. Then an arrow from each tab to the first screen of its stack. Screens that hide the bar go in their own zone.
- Examples: `examples/ride-screen-flow.spec.json` (52 screens, 6 zones, 77 arrows; take the `at` keys out and it still builds with no error), `examples/shop-screen-flow.spec.json` (the complete shop app at mixed fidelity), `shop-highlight-screen-flow`, `shop-fidelity-screen-flow`, `shop-entry-screen-flow`, `shop-tabs-screen-flow`, `shop-overlays-screen-flow`, `shop-states-screen-flow`, `shop-coded-screen-flow`, `shop-wireframe-screen-flow` (two screens at L3 with blocks).
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart` and the others of the icon library. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Screens as built (L4)

When the user wants the screens as the app shows them now, draw them at L4 from screenshots of the app, built and run from its own source. Plan: `docs/plugin/l4-as-built.md`.

1. **Run the app** with the project's own commands (its README, `package.json` scripts), against seeded or demo data, never a real user's. If the app cannot run here, say so and draw L2 or L3 instead; do not invent screenshots.
2. **Read the flow from the code**: the routes (and their guards, which are decisions such as "Signed in?") and the links and navigation calls of each page. Each screen is a route in a state: signed in or out, empty, an error.
3. **Write a plan** for `${CLAUDE_PLUGIN_ROOT}/skills/screen-flow/capture.js` (the steps it knows are at the top of the file):

```json
{"base_url": "http://127.0.0.1:4200", "viewport": [1280, 800],
 "sessions": {"signed-in": {"steps": [
   {"goto": "/register"}, {"fill": "input[name=\"username\"]", "value": "demo${run}"},
   {"fill": "input[name=\"email\"]", "value": "demo${run}@example.com"},
   {"fill": "input[name=\"password\"]", "value": "demo-${run}"},
   {"click": "button[type=\"submit\"]"}, {"wait": "a[href=\"/settings\"]"}]}},
 "screens": [
   {"code": "W02", "goto": "/login", "wait": "form", "source": "../src/app/auth/auth.component.ts",
    "hotspots": {"Sign in": "button[type=\"submit\"]"}},
   {"code": "W12", "session": "signed-in", "goto": "/settings", "wait": "form",
    "hotspots": {"Update Settings": "button:has-text(\"Update Settings\")"}}]}
```

   A session is made once and shared by the screens that name it; every screen is shot in a fresh browser. Steps reach a state (fill a form, click, wait); `remember` keeps a part of the address (a new article's slug) for later screens as `${name}`. A hotspot is the element a transition starts from, found by a stable selector (a test id, a form field's name, a button's text). `source` is the file that draws the screen, relative to the spec's folder; the check warns when it is newer than the screenshot. Viewports: desktop `[1280, 800]`, phone `[390, 844]`. `"full_page": true` on a screen takes the whole page; the frame still shows its top, the zoom shows all of it, and hotspots below the fold are kept. The script finds Playwright in the project, else in the machine's global `npm root`.
4. **Run it**: `node ${CLAUDE_PLUGIN_ROOT}/skills/screen-flow/capture.js plan.json captures`. It needs Playwright and Chromium. It writes `captures/<code>.png` and `captures/manifest.json`; each entry lists the hotspots it found and the ones it did not (`missing`): fix a missing selector and run it again. Look at every screenshot before you draw: right page, right state, nothing still loading.
5. **Write the spec** with `"captures"` and `"capture": "<code>"`, the transitions you read from the code, and build with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build <spec> -o <folder>`. Screens that are not built yet can stay at L0 to L2 in the same diagram. Draw the links of a top bar that every page has once, from the home page, and say so in `desc`. Use `"size": "large"` when the reader must read the screenshots on the page.

## Limits to tell the user

- L3 blocks are shrunk to fit the flow: a screen at L3 is taller than one at L2 only by the device, but its text is small. Open the wireframe skill for a screen you want to read.
- Elements are named, not laid out: the frame shows them in a fixed order (top ones, the hatched block, bottom ones, tab bar).
- Routing follows the grid. Long returns and arrows between far zones cross other lines (the check warns `lines-cross`): that is geometry, not a bug. Put the screens a flow goes through next to each other, and a hub that many screens return to near them.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor; the dark and slate chips are text with a background there, not pills.
- The automatic arrangement orders by flow, not by how the diagram will look: it gives no errors on a large flow, but a hand-set `at` usually crosses far fewer lines.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`. Any other value is refused by the build.

For a diagram with more than about 25 screens split it by zone into several specs and join them with `flag` items ("To Checkout flow", "diagram 02"), or use the `author` skill (`/flow:author`), which lays the diagram out by hand and looks at the result. The automatic layout does handle a large flow without an error (no line through a frame, no chip on a frame), but the page is large (a 52-screen flow is about 3800 x 5700 px) and long returns still cross other lines.
