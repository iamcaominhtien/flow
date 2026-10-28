# Benchmarks: diagram briefs

A set of 25 briefs for testing the Flow plugin on harder, realistic subjects than the examples in `examples/`. Each brief is a plain-language request, as a user would write it. The plugin is run on the brief, and the picture it produces is compared with what the brief says.

- `briefs/<type>.md`: three briefs per type (BPMN has a second level C brief), at levels A (8-12 elements), B (20-30) and C (40-60). Types: flowchart, sequence, er, architecture, bpmn, state, orgchart, gantt.
- `briefs/index.md`: the list, with the element and connection counts (exact for level C, the research tool's claims for A and B).
- `briefs/CHECKS.md`: what `check_briefs.py` measured, and what a person found when reading. **Read it before trusting the counts.**
- `briefs/research-notes.md`: the research tool's own notes and its works-cited list. Not verified.
- `briefs/screen.md`: one level C brief for the screen flow (52 items, 77 connections). Written here, not by the research tool, and **not read by `check_briefs.py`** (the checker expects levels A, B and C for every type). Results: `results/2026-10-27-screen-C-01.md` (automatic layout, 0.11.0), `results/2026-10-27-screen-C-01-author.md` (author kit, 0.11.1) `results/2026-10-28-screen-C-01-author-sonnet.md` (author kit, 0.11.2, a Sonnet agent) `results/2026-10-28-screen-C-01-l0-sonnet.md` (the same at L0, 0.11.3) and `results/2026-10-28-screen-C-01-l0-sonnet-2.md` (L0 again, 0.12.0).
- `briefs/screen-l4.md`: one level A brief for the screen flow at L4 (screens as built), on RealWorld Conduit (Angular), with the structure read from its code. `l4/conduit/plan.json` is the capture plan used to check that the app runs and the screens can be taken (a solution; do not show it to a blind agent). Not read by `check_briefs.py`.
- `check_briefs.py`: checks the format and compares the claims with the text. `python3 benchmarks/check_briefs.py`.

## Format of a brief

A heading `## <type>-<level>-<nn> — title`, a list of fields (`type`, `level`, `elements`, `connections`, `groups`) and the sections `Brief`, `Must show`, `Traps`, `Sources`, `Uncertain`. Level C briefs also have `Structure`: the elements by group (a Gantt task is written `Name@start+length`, in weeks from 0) and the connections as `A -> B (label)`. For a sequence brief, elements are the participants and connections are the messages, named in the label.

## How to run a brief

1. Give a fresh agent **only the text under `Brief`**, and the plugin skill: `flow:author` for large or dense diagrams (level B and C), or the skill for the type (for example `flow:bpmn`) for the quick build path. Do not show `Must show`, `Traps` or `Structure`: the agent would fit its answer to them. Tell it not to open `benchmarks/`, `examples/`, `docs/`, `tests/`, the changelog or the git history: `examples/ride-screen-flow.spec.json` is a solution of `screen-C-01`, and the run records describe earlier answers.
2. The agent writes the spec, builds, fixes errors by changing the spec (at most three rounds as the skill says), and looks at the HTML and draw.io pictures. Use an absolute path with `node /tmp/shot.js` and a viewport as wide as the diagram.
3. Compare the picture with `Must show`, one point at a time, and count the elements and lines that are drawn against the `Structure` (level C) or the brief's text (levels A and B).
4. Record the result in `benchmarks/results/<date>-<id>.md`: the spec, the build output, the number of rounds, what the check reported, what a person saw that the check did not, and the unclear parts of the skill.

## Known limits of this set

- Levels A and B were not recounted: their element and connection counts are the research tool's claims. Level C briefs have an exact `Structure`; six of them were rewritten here (see `briefs/CHECKS.md`).
- The brief text was cleaned of citation numbers that the research tool left glued to words. The cleaning was reviewed by reading every change.
- Several briefs cite a book or standard and no URL. No source was opened. The domain details of the rewritten level C briefs were not checked against their sources.
- `results/2026-10-26-translated-specs.md` is a script translation of the level C structures, not an agent run. `results/2026-10-26-author-path.md` records the first blind agent runs (one per row, level C flowchart and BPMN only); the other types and levels have not been run.
