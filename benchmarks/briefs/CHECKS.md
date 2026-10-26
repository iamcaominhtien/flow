# Checks of the briefs

Produced by `python3 benchmarks/check_briefs.py` and by reading. Re-run the script after any edit; `tests/test_briefs.py` runs it too.

## What was changed after the first check

The first version of this set came from a research tool. Reading it showed that its level C briefs named fewer elements than they claimed (for example bpmn-C-01 named about 33 elements and 31 connections, and claimed 46 and 55; the Gantt brief had no durations and asked for loops, which a Gantt chart cannot show). So:

- **Six level C briefs were rewritten** (flowchart, er, architecture, bpmn, state, gantt) by Claude, keeping the research tool's subject and group names and enlarging them to 41-44 elements and 48-60 connections.
- **Two level C briefs were given a `Structure`** without changing their prose: org chart (44 elements, 43 connections; the claim was 45 and 44) and sequence (14 participants and 43 messages; the claim was "44 participants" and 52 connections).
- Each level C brief now has a `Structure` section listing every element by group and every connection. The `Brief` text of the rewritten ones was generated from it, so it is plain and repetitive on purpose: every sentence names both ends of a line.
- The script checks that the counts equal the Structure, that every connection names known elements, that every name appears in the Brief, and that a Gantt task starts after its predecessors end.
- Levels A and B were **not** rewritten or counted by hand. Their counts are still the research tool's claims.
- The domain details of the rewritten briefs were written to give the diagram a realistic shape. They were not checked against the cited sources (each has that line under `Uncertain`).

## Measured by the script

"Names in text" is the number of distinct CamelCase identifiers in the brief text. For briefs with a Structure the counts are exact and this column is only informational.

| id | claimed elements | names in text | words | claimed connections |
| --- | --- | --- | --- | --- |
| flowchart-A-01 | 10 | 11 | 107 | 10 |
| flowchart-B-01 | 21 | 20 | 177 | 28 |
| flowchart-C-01 | 43 | 43 | 387 | 51 |
| sequence-A-01 | 10 | 14 | 81 | 9 |
| sequence-B-01 | 22 | 39 | 152 | 25 |
| sequence-C-01 | 14 | 55 | 240 | 43 |
| er-A-01 | 9 | 7 | 100 | 10 |
| er-B-01 | 22 | 20 | 158 | 26 |
| er-C-01 | 41 | 41 | 260 | 50 |
| architecture-A-01 | 9 | 10 | 97 | 10 |
| architecture-B-01 | 24 | 20 | 157 | 28 |
| architecture-C-01 | 41 | 41 | 331 | 52 |
| bpmn-A-01 | 10 | 11 | 100 | 11 |
| bpmn-B-01 | 24 | 20 | 142 | 28 |
| bpmn-C-01 | 41 | 41 | 348 | 48 |
| state-A-01 | 9 | 9 | 130 | 11 |
| state-B-01 | 22 | 20 | 190 | 27 |
| state-C-01 | 41 | 41 | 333 | 51 |
| orgchart-A-01 | 11 | 11 | 61 | 10 |
| orgchart-B-01 | 24 | 23 | 80 | 23 |
| orgchart-C-01 | 44 | 44 | 124 | 43 |
| gantt-A-01 | 10 | 10 | 80 | 9 |
| gantt-B-01 | 23 | 23 | 148 | 26 |
| gantt-C-01 | 44 | 44 | 612 | 60 |


Errors: 0

Warnings: 17
- sequence-A-01: claims 10 elements, the text names 14 CamelCase identifiers
- sequence-B-01: claims 22 elements, the text names 39 CamelCase identifiers
- sequence-C-01: the Brief names identifiers not in Structure: NasRegistrationRequest
- er-A-01: Sources holds no URL (a book or standard only)
- er-C-01: Sources holds no URL (a book or standard only)
- architecture-A-01: Sources holds no URL (a book or standard only)
- architecture-C-01: Sources holds no URL (a book or standard only)
- bpmn-A-01: Sources holds no URL (a book or standard only)
- bpmn-B-01: Sources holds no URL (a book or standard only)
- bpmn-C-01: Sources holds no URL (a book or standard only)
- state-B-01: Sources holds no URL (a book or standard only)
- state-C-01: Sources holds no URL (a book or standard only)
- orgchart-A-01: Sources holds no URL (a book or standard only)
- orgchart-A-01: the brief has 61 words, the range is 80-250
- gantt-A-01: Sources holds no URL (a book or standard only)
- gantt-B-01: Sources holds no URL (a book or standard only)
- gantt-C-01: Sources holds no URL (a book or standard only)

## Found by reading

- **Sources:** 13 of 24 briefs give a book or a standard and no URL, although URLs were asked for. No source was opened here.
- **The research tool said all briefs met their size and structure targets** (see `research-notes.md`). That did not hold for the original level C briefs.
- **Levels A and B:** sequence-A-01 and sequence-B-01 name more identifiers than claimed (14 against 10, 39 against 22), because the messages are also named in CamelCase. orgchart-A-01 has 61 words (below 80). These are soft.
- **Citation numbers** glued to words were removed from the original briefs (101 places, each read). Names that end in a digit were kept (`RemediationFixCycle1`, `RemediationFixCycle2`, `N1`, `N2`, `N4`, `H3`).
- **The rewritten level C briefs read mechanically** ("X routes to Y. Y splits 3 ways: ..."). That is fine as test input and makes the lines checkable, but it is not how a user writes. A real user brief would be shorter and vaguer; that would be a different test.
