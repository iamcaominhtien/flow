---
description: Draw a diagram of how something works, fits together, moves, is organised or is planned, from any input (code, a repo, a schema, a table, notes, a transcript, a log, a document or a sentence), as an animated HTML page and a draw.io file, and a PNG when a headless browser is available. Use when the user asks to draw, show, picture, visualise, map out or sketch such a thing, or for an image or a diagram of it, and names no diagram type that another Flow skill covers. Not for charts of numbers (bar, line, histogram), illustrations, posters or photos, or diagrams written as text (Mermaid, ASCII).
allowed-tools: Bash(node ${CLAUDE_PLUGIN_ROOT}/scripts/view.js *)
---

# Draw

The way in when the request says what to show but not which diagram. This skill chooses the diagram from the structure of what is shown, hands over to that type's skill, and delivers the picture.

## Steps

Before step 1, follow the working method in `${CLAUDE_PLUGIN_ROOT}/skills/WORKING.md`: know the question, the reader and the medium; read the source as deep as the question needs; choose what is in and what is left out; and write the brief, one line each for `Question:`, `Reader:`, `Medium:`, `Sources read:`, `Left out:` and `Unknowns:`, as `<name>.brief.md` in the folder of the spec, with the spec's name (on the author path, in the folder and with the name you pass to `canvas.write`). `flow.py build` and `canvas.write` print it back with the check report. Before you deliver, look at the picture at the medium's size (step 8), and tell the user the sources you read and what you left out.

1. Check that Flow is the tool. A chart of numbers (bars, lines, a histogram, a scatter), a picture that is an illustration, a poster or a photo, and a diagram the user wants as text (a Mermaid block in a file, ASCII art in the reply) are not Flow's: say so in one line and do the work without Flow.
2. From what you read in WORKING.md steps 1-5, name the structure the question is about, and pick the skill from the table below. When two fit, pick the one that answers the question; when the question needs two levels, draw the overview first and offer the detail.
3. Load that skill (the Skill tool, `flow:<name>`) and follow its steps. The brief you wrote carries over: keep its name for the spec.
4. Deliver. When the user asked for an image, or reads on a phone or in a chat, run `node ${CLAUDE_PLUGIN_ROOT}/scripts/view.js <page>.html <medium>`: it writes `<name>.png` next to the page. It needs Node, Playwright and Chromium; when it cannot run, say so, give the HTML and the `.drawio` file, and say that `/flow:doctor` shows what is missing.

## Which skill

| What the question is about | Skill |
| :-- | :-- |
| the steps and decisions of a procedure, with who does what in lanes | `flowchart` (`bpmn` when the user asks for BPMN) |
| the states of one thing and the events that move it | `state` |
| messages between people or systems, in time order | `sequence` |
| the parts of a system and how they call each other | `architecture` (`c4` for a C4 view, `cloud` for cloud resources in regions and networks) |
| data moving between processes and stores | `dfd` |
| tables, keys and how they link | `er` |
| classes and how they relate | `class` |
| who reports to whom | `org-chart` |
| tasks and milestones on dates | `gantt` |
| what each team or theme delivers per period | `roadmap` |
| the screens of an app and how a person moves between them | `screen-flow` |
| the layout of one screen | `wireframe` |
| one idea and what it is made of | `concept` |
| a topic broken down into branches | `mind-map` |
| stacked tiers, a tech stack | `layers` |
| items in columns: a board, a comparison of options | `kanban` |
| one idea taught to a newcomer: a journey, an inside view, A or B | `explainer` |
| actors and what they do with a system | `usecase` |
| an existing `.drawio` file | `import-drawio` to redraw it, `edit-drawio` to change it in place |
| none of these, or a large or dense diagram whose automatic layout is not good enough | `author` |
