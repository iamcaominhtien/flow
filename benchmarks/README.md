# Benchmarks: diagram briefs

A set of 24 briefs for testing the Flow plugin on harder, realistic subjects than the examples in `examples/`. Each brief is a plain-language request, as a user would write it. The plugin is run on the brief, and the picture it produces is compared with what the brief says.

- `briefs/<type>.md`: three briefs per type, at levels A (8-12 elements), B (20-30) and C (40-60). Types: flowchart, sequence, er, architecture, bpmn, state, orgchart, gantt.
- `briefs/index.md`: the list, with the element and connection counts the research tool gave.
- `briefs/CHECKS.md`: what `check_briefs.py` measured, and what a person found when reading. **Read it before trusting the counts.**
- `briefs/research-notes.md`: the research tool's own notes and its works-cited list. Not verified.
- `check_briefs.py`: checks the format and compares the claims with the text. `python3 benchmarks/check_briefs.py`.

## Format of a brief

A heading `## <type>-<level>-<nn> — title`, a list of fields (`type`, `level`, `elements`, `connections`, `groups`) and the sections `Brief`, `Must show`, `Traps`, `Sources`, `Uncertain`.

## How to run a brief

1. Give a fresh agent **only the text under `Brief`**, and the plugin skill for the type (for example `flow:bpmn`). Do not show `Must show` or `Traps`: the agent would fit its answer to them.
2. The agent writes the spec, builds, fixes errors by changing the spec (at most three rounds as the skill says), and looks at the HTML and draw.io pictures. Use an absolute path with `node /tmp/shot.js` and a viewport as wide as the diagram.
3. Compare the picture with `Must show`, one point at a time, and count the elements and lines that are drawn against the brief's text (not against the claimed counts).
4. Record the result in `benchmarks/results/<date>-<id>.md`: the spec, the build output, the number of rounds, what the check reported, what a person saw that the check did not, and the unclear parts of the skill.

## Known limits of this set

- The element and connection counts in the briefs are the research tool's claims. Several briefs name fewer elements than they claim (see `briefs/CHECKS.md`), so compare with the text.
- The brief text was cleaned of citation numbers that the research tool left glued to words (for example `AdjRibIn18` became `AdjRibIn`). The cleaning was reviewed by reading every change, but a missed one would show as a wrong element name.
- Several briefs cite a book or standard and no URL, although the request was for URLs. None of the sources was opened.
- Nothing here has been run through the plugin yet.
