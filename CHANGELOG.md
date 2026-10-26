# Changelog

## 0.1.0 (2026-10-26)

First release.

- **Plugin** `flow` for Claude Code with 24 skills: flowchart, sequence, ER, architecture, cloud, C4, state, BPMN, use case, class, DFD, screen flow, org chart, mind map, Gantt, roadmap, Kanban, layers, wireframe, concept, import-drawio, edit-drawio, doctor, and `author`.
- **Two outputs** from one set of positions: an animated HTML page and a native `.drawio` file. Plain and illustrated styles; 40 flat and 97 detailed icons; custom icons checked before use.
- **Automatic layout** for small diagrams (layered engine, tidy trees, timelines, boards), with swimlanes drawn as in the design, a route search for blocked lines, and folding of long charts into bands.
- **Author path** (`/flow:author`, `flowlib/author.py`): for large or dense diagrams Claude lays the diagram out itself in its own script, using a kit that keeps the design, and looks at its own picture.
- **Checks:** overlaps, lines through boxes, covered labels and captions, overlapping lines, crossings, text that does not fit.
- **Editing:** `flow.py import` and `flow.py edit` for existing `.drawio` files.
- **Benchmarks:** 25 test briefs and a checker; the first blind agent runs on level C briefs (`benchmarks/results/`).
- **Install notes** in `INSTALL.md`, including an untested route for Google Antigravity (`plugins/flow/plugin.json`).

Not verified: the draw.io editor, claude.ai, Cowork, Windows and Antigravity; runs of the author path for the other types; averages over several runs.
