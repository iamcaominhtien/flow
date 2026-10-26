# bpmn-C-01, one blind agent run, illustrated style

Date: 2026-10-26. One fresh agent with no context was given only the Brief
of `bpmn-C-01` and the `flow:bpmn` skill, and asked for the illustrated style.
It had 3 rounds of check and fix. This is one run, not a benchmark average.

## Completeness (checked by script against `Structure`)

- Elements: 41 of 41 drawn, none extra.
- Connections: 48 of 48 drawn, none missing or extra (14 are message flows).

## Plugin check

- Final: 0 errors, 2 warnings (`lines-cross`: Standard safety database to
  Periodic report against Suspected reaction to Issue site hold; Benefit risk
  to Assess causality against Acknowledge notice to Draft submission).
- Round 2 had 7 `label-covers` errors. The agent fixed them by shortening
  flow labels ("data has errors" became "Errors", "standard track" became
  "Standard"), so the brief's wording is partly lost.
- Page size is about 6200 x 1100 px with direction `right`.

## What the picture shows that the check did not report

Looked at in a headless browser render (the draw.io file was not opened).

- Three message lines labelled "Standard" run down one shared vertical
  stretch, with the labels stacked on it. It is hard to tell which line goes
  where.
- A solid and a dashed line overlap next to the Suspected unexpected reaction
  gateway (the line to Unblind trial arm and a message line).
- The "Extended review" caption is partly covered by the "More time" label.
  The "Submission rejected" caption is crossed by a line.
- The "Further inquiry" and "Fast-track" message lines are very long and
  run across most of the page.
- The data safety board and regulator lanes are mostly empty in the left
  half, so the diagram is wide and sparse.
- Illustrated style: only 8 of 41 elements got a card, chosen by the agent.
  The rest are plain boxes, so the page looks uneven.

## What the agent reported as unclear in the skill

- The list of tones (blue, violet, amber, green, teal, gray) is not in the
  skill; it was learned from the validator error.
- The skill says three rounds; nothing says how to draw a named intermediate
  event the brief only names (the agent picked message and error itself).
- Gateway types are not in the brief; the agent chose exclusive and one
  parallel.

## Not verified

- Domain correctness of the brief.
- The draw.io file in the editor.
- Whether another agent, or the same agent in another run, gives the same.

## Follow-ups this suggests (not done)

1. Check: report overlapping line stretches and a label covering a caption.
2. Skill: list the tones; say when to use cards on many elements.
3. Layout: spread shared stretches; shorter routes for long message lines.
