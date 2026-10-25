---
description: Change an existing draw.io file (.drawio) in place: rename, move, resize, recolour, add or delete boxes and lines, keeping everything else as it was. Use when the user hands over a .drawio file and asks for a specific change to it.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Edit a draw.io file

This edits the file as XML, so what you do not name stays as it was: other pages, custom styles and shapes, cells this tool does not understand. It works on files written by Flow and on files drawn by hand. It does not lay anything out: you say what changes and where.

## Steps

1. Find the cell ids: open the `.drawio` file with the Read tool and look at the `id` of each `mxCell`. In files written by Flow a box is `node-<id>` and a line `edge-<id>`. If the file is compressed (the `diagram` element holds one long line of letters), run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py import file.drawio -o diagrams` first, or ask the user to save it uncompressed (File, Properties, Compressed off in draw.io).
2. Write `ops.json`, a list of operations (below), in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py edit path/to/file.drawio ops.json`. The result is written next to the file as `<name>.edited.drawio` and the original is not touched. Add `--in-place` only when the user asked to change the file itself; it keeps the old file as `<name>.drawio.bak`. Exit code 0: written; 1: nothing was changed, and the message lists every problem in the list.
4. Tell the user what changed, and any note the command printed (for example that lines were routed again).
5. Offer to run `flow.py import` on the result to get an animated HTML page.

## Operations

```json
[
  {"op": "set_text", "id": "node-api", "text": "API v2"},
  {"op": "move", "id": "node-api", "x": 300, "y": 120},
  {"op": "resize", "id": "node-api", "width": 200, "height": 64},
  {"op": "tone", "id": "node-api", "tone": "green"},
  {"op": "set_style", "id": "node-api", "key": "dashed", "value": "1"},
  {"op": "add_node", "id": "cache", "text": "Cache", "x": 400, "y": 200, "shape": "process", "tone": "blue"},
  {"op": "add_edge", "id": "api-cache", "from": "node-api", "to": "node-cache", "label": "reads"},
  {"op": "delete", "id": "node-web"}
]
```

- `set_text`: a line break in `text` is `\n`.
- `move` and `resize` also reset the stored bends of the lines that touch the box, and those lines are routed again by draw.io (so they may look different from before).
- `tone`: `blue violet amber green teal gray`. It sets the fill only.
- `set_style`: sets one style key; `"value": null` removes it. Use it for anything else draw.io styles can do.
- `add_node`: `shape` is one of Flow's shapes (`process` by default); the box gets Flow's look. A node added with `id: "cache"` becomes the cell `node-cache`. `width` and `height` default to 160 and 56.
- `add_edge`: `from` and `to` are cell ids (an id added earlier in the same list works). The line has no stored route; draw.io draws it.
- `delete` removes the cell, the cells inside it (an icon, table rows) and every line that ends on it.
- The whole list is checked first. If one operation is wrong nothing changes, and the message names each wrong one.

## Limits to tell the user

- Only the first page is edited; other pages are kept as they are.
- A compressed file is written back uncompressed. draw.io opens both.
- Edits were tested by reading the result back and by opening one edited file in the draw.io viewer, not in the editor.
- It cannot lay out a new diagram or move many boxes sensibly by itself. For that, describe the diagram again with the other skills.
