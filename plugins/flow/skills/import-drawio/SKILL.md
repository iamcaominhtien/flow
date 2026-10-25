---
description: Read an existing draw.io file (.drawio) into Flow so it can be shown as an animated HTML page and re-exported. Use when the user hands over a .drawio file and asks to animate it, restyle it, or check it.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Import a draw.io file

This reads a `.drawio` file into Flow's scene format. It is a best-effort conversion, not an editor: you cannot move a box in the original file with it.

## Steps

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py import path/to/file.drawio -o diagrams`. It writes `<name>.scene.json`, `<name>.html` and `<name>.imported.drawio` and prints notes about what it skipped, then a check report. The original file is never changed. Exit code 0: no error; 2: errors found (files still written); 1: the file cannot be read.
2. Tell the user the notes in plain words (for example "3 icons were not read back").
3. To change the result, edit the scene through an overrides file (see the flowchart skill) or ask the user what to change in the original; do not edit the HTML or the `.drawio` by hand.

## What is read

- Compressed and plain files, first page only.
- Top-level boxes become nodes. The shape is guessed from the style: diamond, ellipse (a circle when small), parallelogram, document, hexagon, cylinder, actor, a pill with fully round ends, else a rounded box.
- Swimlanes and containers become frames. Boxes inside a container are read at their position on the page.
- A swimlane with text rows (the ER table that Flow writes) becomes a table.
- Edges between boxes become lines with the same dash and arrow ends, ER crow's-foot ends included, and a text label.
- The fill colour becomes a tone only when it is one of Flow's own tints.

## What is not read

- Icons and other images, free text boxes, groups other than containers, other pages, custom shapes and styles.
- Bends of orthogonal lines that draw.io routes by itself: the line is drawn straight between the two boxes unless the file stores waypoints.
- Line animation: every line is imported as a plain line; only a line drawn in Flow's main blue becomes a main line.

## Limits to tell the user

- Tested on files Flow wrote and on one small hand-made file, not on large files from the draw.io editor.
- The result should be looked at, not trusted.
