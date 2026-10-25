# Source of the design canvas

The pictures in this document are screenshots of boards on a design canvas. This folder holds the **code behind every board**, so a board can be opened, read, changed or rebuilt without the canvas.

| Folder | What it is | Use it to |
| --- | --- | --- |
| [`html/`](html/) | One **standalone HTML file per board** (104). Opens in any browser as it is; fonts load from Google Fonts. The animated lines (main path and event stream) **really animate** in the browser | See a board at full size, with its animation, and inspect how it is built |
| [`canvas/`](canvas/) | The **original board files** in the canvas format (`*.dc.html`), plus `canvas.json`, which holds every board's page, position and size and the section titles | Republish to a design canvas, or read the board as it was authored |
| [`generators/`](generators/) | The **Python scripts and libraries** that drew the boards, and the small Node tools that checked them | Rebuild a board, or learn the layout logic a plugin will need |

## html/

Each file is a single board, for example [`html/Sequence_Delivery.html`](html/Sequence_Delivery.html). Everything is absolutely positioned HTML and inline SVG, so the file shows exactly what the picture shows.

- The first four boards that were built from a data template on the canvas (`Main`, `Components_Process`, `Components_Structure`, `Icons`) are stored **already expanded**, so they need no runtime.
- Animation comes from two small CSS classes in each file: `.flow` (the main path, fast) and `.flow2` (the event stream, slow). Both stop when the viewer prefers reduced motion.
- A board is `width × height` pixels, given in [`canvas/canvas.json`](canvas/canvas.json) and in the [board index](../16-board-index.md).

## canvas/

The `*.dc.html` files are the same boards in the format the design canvas reads. They start with `<x-dc>` and load a script, `support.js`, that belongs to the canvas runtime and is **not** included here; without it a file still shows most of its content, but the four template boards will show placeholders (`{{...}}`). To republish, put the files and `canvas.json` back into a design-canvas project.

## generators/

Almost every board was written by a small Python script, so that spacing and sizes could be computed and changed in one place.

- **Libraries** (one per family of diagrams) hold the drawing helpers: `fclib.py` (board, node, arrow, card), `fcicons.py` and `fcdetail*.py` (the flat and detailed icons), `fslib.py` (sequence), `erlib.py` (ER), `archlib.py` (architecture), `exlib.py` (explainer), `pllib.py` (planning), `umllib.py` (UML), `wflib.py` (wireframe), `bpmnlib.py` (BPMN), `c4lib.py` (C4), `cloudlib.py` (cloud) and `dfdlib.py` (DFD). `icons.json` lists the icon sets.
- **One script per board** (`fs_delivery.py`, `er_split.py`, `cl_delivery.py`, `df_level1.py`...) builds a board from its parts. The prefix says the family: `fc_` flowchart, `fs_` sequence, `er_` ER, `ar_` architecture, `ex_` explainer, `pl_` planning, `um_` UML, `wf_` wireframe, `bp_` BPMN, `c4_` C4, `cl_` cloud, `df_` DFD. `*_rules.py` builds a rules board.
- **Node tools** check and render the boards: `lint.js` (labels and shapes that straddle a frame border), `clipcheck.js` (content that runs past a board), `shot.js`, `crop.js`, `renderall.js`, `rendertpl.js` and `exporthtml.js` (screenshots and the export in `html/`).

The scripts were written to run in a scratch folder. Their paths are written as `/path/to/work/`, `/path/to/flowdesign/project/` and `/path/to/flow/docs/design/source/`; replace these with your own folders before running one. They need Python 3 and, for the tools, Node with Playwright.

## Keeping it in step

These files are a snapshot taken when the document was written. If a board changes, update its HTML here and the picture and page in the parent folder.
