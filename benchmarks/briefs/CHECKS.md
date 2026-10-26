# Checks of the briefs

Produced by `python3 benchmarks/check_briefs.py` and by reading. Re-run the script after any edit.

## Measured by the script

"Names in text" is the number of distinct CamelCase identifiers in the brief text, a rough count of the elements the brief names. It is an estimate: some briefs name elements in words instead.

| id | claimed elements | names in text | words | claimed connections |
| --- | --- | --- | --- | --- |
| flowchart-A-01 | 10 | 11 | 107 | 10 |
| flowchart-B-01 | 21 | 20 | 177 | 28 |
| flowchart-C-01 | 42 | 37 | 271 | 48 |
| sequence-A-01 | 10 | 14 | 81 | 9 |
| sequence-B-01 | 22 | 39 | 152 | 25 |
| sequence-C-01 | 44 | 54 | 235 | 52 |
| er-A-01 | 9 | 7 | 100 | 10 |
| er-B-01 | 22 | 20 | 158 | 26 |
| er-C-01 | 42 | 32 | 222 | 50 |
| architecture-A-01 | 9 | 10 | 97 | 10 |
| architecture-B-01 | 24 | 20 | 157 | 28 |
| architecture-C-01 | 45 | 32 | 197 | 54 |
| bpmn-A-01 | 10 | 11 | 100 | 11 |
| bpmn-B-01 | 24 | 20 | 142 | 28 |
| bpmn-C-01 | 46 | 28 | 220 | 55 |
| state-A-01 | 9 | 9 | 130 | 11 |
| state-B-01 | 22 | 20 | 190 | 27 |
| state-C-01 | 44 | 29 | 221 | 56 |
| orgchart-A-01 | 11 | 11 | 61 | 10 |
| orgchart-B-01 | 24 | 23 | 80 | 23 |
| orgchart-C-01 | 45 | 44 | 124 | 44 |
| gantt-A-01 | 10 | 10 | 80 | 9 |
| gantt-B-01 | 23 | 23 | 148 | 26 |
| gantt-C-01 | 44 | 31 | 208 | 52 |


Errors: 0

Warnings: 22
- flowchart-C-01: the brief has 271 words, the range is 80-250
- sequence-A-01: claims 10 elements, the text names 14 CamelCase identifiers
- sequence-B-01: claims 22 elements, the text names 39 CamelCase identifiers
- er-A-01: Sources holds no URL (a book or standard only)
- er-C-01: Sources holds no URL (a book or standard only)
- architecture-A-01: Sources holds no URL (a book or standard only)
- architecture-C-01: Sources holds no URL (a book or standard only)
- architecture-C-01: claims 45 elements, the text names 32 CamelCase identifiers
- architecture-C-01: level C but only 1 phrases about a return or loop
- bpmn-A-01: Sources holds no URL (a book or standard only)
- bpmn-B-01: Sources holds no URL (a book or standard only)
- bpmn-C-01: Sources holds no URL (a book or standard only)
- bpmn-C-01: claims 46 elements, the text names 28 CamelCase identifiers
- state-B-01: Sources holds no URL (a book or standard only)
- state-C-01: Sources holds no URL (a book or standard only)
- state-C-01: claims 44 elements, the text names 29 CamelCase identifiers
- orgchart-A-01: Sources holds no URL (a book or standard only)
- orgchart-A-01: the brief has 61 words, the range is 80-250
- gantt-A-01: Sources holds no URL (a book or standard only)
- gantt-B-01: Sources holds no URL (a book or standard only)
- gantt-C-01: Sources holds no URL (a book or standard only)
- gantt-C-01: claims 44 elements, the text names 31 CamelCase identifiers


## Found by reading

- **bpmn-C-01 is smaller than it claims.** Counting by hand from the text: about 33 named elements and about 31 connections, against 46 and 55 claimed. Two connections are only implied ("which crosses into Safety Management CRO" gives no target name; `FastTrackSafetyNoticeTask` notifies a pool, not a named element).
- **Level C briefs in general look closer to level B in size.** The script finds 28 to 37 names in the text of flowchart-C, er-C, architecture-C, bpmn-C, state-C and gantt-C, against 42 to 46 claimed. Only sequence-C and orgchart-C name as many as they claim. Only bpmn-C was counted by hand.
- **The research tool said all briefs met their size and structure targets** (see `research-notes.md`). That does not hold for the points above.
- **Sources:** 13 of 24 briefs give a book or a standard and no URL, although URLs were asked for. No source was opened here.
- **Loops:** the level C briefs for er, orgchart and gantt have little or no "return" text. That is expected for those types (no loops), so the loop check applies only to flowchart, sequence, architecture, bpmn and state.
- **sequence-A-01 and sequence-B-01 name more identifiers than claimed** (14 against 10, 39 against 22); in a sequence diagram the messages are also named in CamelCase, so the count mixes participants and messages. Not an error.
- **flowchart-C-01 has 271 words** (range 80-250) and **orgchart-A-01 has 61** (below 80). Both are soft.
- Citation numbers glued to words were removed from the briefs (101 places, each read). Names that end in a digit were kept (`RemediationFixCycle1`, `RemediationFixCycle2`, `N1`, `N2`, `N4`, `H3`).
