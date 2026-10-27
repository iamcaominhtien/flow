---
description: Draw a wireframe (phone, tablet or desktop screens made of blocks on a grid, with numbered notes, a state set or a responsive set) as an HTML page and a draw.io file. Use when the user asks for a wireframe, a screen layout, the states of a screen or a responsive layout.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Wireframe

A wireframe shows what is on one screen and where. You write a short **spec**; a script places the blocks on a 12 column grid, draws the device around them and writes the files. Never write coordinates or HTML yourself. One style only: grey with a single blue accent. **Nothing animates.**

## Steps

1. Decide the shape: a few screens of one task, one desktop screen, a **state set** (the same screen in normal, loading, empty and error) or a **responsive set** (desktop, tablet and phone).
2. Write `diagrams/<name>.spec.json` in the current project, with real words on buttons and labels.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` and prints a check report. Exit code 0: no error; 2: errors (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say it "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{"type": "wireframe", "title": "...", "desc": "...",
 "set": "states" | "responsive",
 "shared": [ block, ... ],
 "screens": [{"id": "1", "label": "Cart", "device": "phone", "state": "normal",
              "note": "1024 px and up", "address": "example.com/orders",
              "blocks": [ block, ... ],
              "annotations": [{"target": "block id", "part": "stepper", "corner": "tl",
                               "title": "Quantity stepper", "text": "One line.", "number": 1}]}]}
```

- **Screen**: `id` and `label` give the name above it, `1 · Cart` (or `S12 · Cart`, the same id and name as a screen flow at L3). `device` is `phone` (330 x 680), `tablet` or `desktop` (1320 x 760, with a browser bar and `address`). `shared` blocks are added at the start of every screen (the navbar of a state set).
- **Block** (a position is a row, a column and a span, never coordinates): `kind`, `id`, `row`, `col` (1 to 12), `span`, `rows` (how many rows tall). Leave them out to stack blocks: no row is the next row; a `col` above 1 with no row goes in the row of the block before. `anchor: "bottom"` pins a block above the foot of the screen (the primary button). `height` overrides the height of an image, a card or a chart.
- **Kinds**: `navbar` (`text` title or brand; flags `back`, `logo`, `menu`, `bell`, `avatar`; `items` links with `selected`; `action` the one primary button; `detail` a search placeholder on a wide bar), `sidebar` (`items`, `icons`, `selected`), `card` (`image` left or top, `text`, `detail`, `price`, `stepper`, `chip`, `action`; no `text` draws grey bars), `panel` (`text` title and `children` blocks), `list_item` (`lead` avatar, radio, pin or thumb, `text`, `detail`, `trail` link, `chip` with `tone`, `selected`, flag `tinted`), `form_field` (`text` label, `detail` placeholder or none for a grey bar, `value`, `hint`, `action` a button on the same row, flag `focus`, `tone: "rose"` for an error), `button` (`text`, `style` primary, secondary, danger or disabled, `icon`), `image` (a crossed box; `text` is a hero line), `tab_bar`, `bottom_nav` (`items`, `icons`, `selected`), `search_bar`, `table` (`columns` with `label`, `weight`, `kind` text, bold, chip or button; `data` rows of strings or `{"text", "style"}`), `chart` (`values`, `selected` bar), `figure` (`text`, `value`, `chip`, `tone`), `chip` (`text` and `tone`, or `items` as choices with `selected`), `stepper`, `rows` (`items` as `Name|Value`), `checklist` (`items`, `selected` checked), `text` (flags `heading`, `label`, `bold`; `bars` grey lines), `loading` (`bars` skeleton rows, `text` spinner words), `empty`, `error`, `success` (`text`, `detail`, `action`, `items` second buttons), and the overlays `modal` (`text`, `detail`, `items` buttons), `sheet` (`text`, `items` rows) and `toast` (`text`). `tone` is `blue`, `green`, `amber`, `rose` or `gray`; green and amber belong in chips only.
- **Tap target**: `"tap": true` on a button, a list item, a card, a table or an empty or error block draws the red dot with a halo. At most one per transition.
- **Annotations**: a numbered badge on a corner (`tl`, `tr`, `bl`, `br`, `l`, `r`, `t`, `b`) of a block or of one of its parts (`part`: `stepper`, `price`, `chip`, `action`, `input`, `icon`, `title`, `image`, `item-N`, `row-N`, `action-N`, `bar-N`, `logo`, `search`, `menu`; a wrong part lists the right ones). Numbers follow the order you list them, screen by screen; `number` sets one, and the same `title` on two screens shares one number. Put a badge on a corner, never over text (a warning says when). A note says what the detail does or why: a bold title and one line.
- **State set** (`"set": "states"`): exactly four screens with `state` normal, loading, empty, error. Loading has skeleton rows and spinner words, empty one dashed icon and one action, error a rose icon with the retry first and a secondary option.
- **Responsive set** (`"set": "responsive"`): one screen each of `desktop` (1024 and up), `tablet` (640 to 1023) and `phone` (under 640), same height; say in notes what changes (columns, filters, links).
- `theme` (optional) only changes the page background. The older `elements` of a screen (header, text, input, button, image, list) still build, stacked.

## Rules the check enforces

- **One primary button per screen** (error; a modal has its own). Others are outlined.
- Warnings: a badge over text, blocks that overlap, a screen taller than its device, stand-in words such as `Button`, a note over two lines, a state screen without its block, an empty state without exactly one action, an error without retry, a responsive set with no notes.

## Limits to tell the user

- Text width is estimated, not measured; a long word can be cut. The draw.io file was checked in an approximate viewer, not in the draw.io editor.
- A table, a chart and a list are drawn from the data you give, not live.
- Examples: `examples/wireframe-mobile.spec.json`, `wireframe-desktop`, `wireframe-states`, `wireframe-responsive` (the four complete examples of the design) and `login-wireframe` (older elements). For screens in a flow, see the screen flow skill (L3 uses these blocks).

For a large or dense diagram use the `author` skill (`/flow:author`) instead.
