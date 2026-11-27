# Working method: from any input to a diagram (draft for review)

Status: draft, not built. Written after two blind runs on the x-algorithm repo (2026-11-27) and a review of the plugin against the question "what does a person do to draw a diagram from any input". This page says what to change, why, and how to test that it generalises.

## The gap

Every skill starts from a brief that already lists what to draw: the design's pipeline is "brief (words) → spec" (`design.md`), the author skill's first step is "Read the brief. List every step", and every benchmark brief enumerates its elements. So the plugin teaches and measures transcription plus layout. It does not teach, and nothing measures, the work before that: deciding what the diagram is for, understanding the source, choosing what to leave out, and checking the picture against the source. On raw input (a codebase, a document, a transcript) an agent does what the skills ask: it finds something that looks like a brief (a README's own box diagram), transcribes it and stops when the check report is clean. That is a gap in the method, not in one skill, so it is fixed in one shared place.

## What a person does

1. **Purpose.** Who reads it and which question it answers. Done: one sentence.
2. **Medium.** Where it is read: phone (portrait, about 390 px wide), screen, slide, print, an editor. Done: a target width and orientation.
3. **Understand the source.** Read the primary source as deep as the question needs, no deeper. Done: you can walk one concrete case through it, and you can say where each fact comes from. Unknowns are listed.
4. **Type.** Choose it from the structure of what is to be shown (control flow, messages over time, structure, data, states, time) and the question. The user's word is a strong hint, not a rule; if it does not fit, say so and offer the type that does.
5. **Scope and level.** Start and end, what is in and what is out, one level of detail per diagram; an overview plus linked detail diagrams when one is not enough. Done: what was left out is written down.
6. **Model.** The elements and links, each traced to a place in the source or marked as an assumption. For a flowchart the decisions, loops and failure paths are the content.
7. **Lay out and draw.** The type's skill: the build path or the author path.
8. **Verify.** Against the source: walk two or three cases on the picture. Against the reader: look at the picture at the target size.
9. **Deliver.** The picture, the sources, what was left out, what is uncertain, and the next level of zoom on offer.

## Change 1: one shared step, written down beside the diagram

- A new reference page, `plugins/flow/skills/WORKING.md` (one file, not a skill, so it is never skipped by routing), holds steps 1-5, 8 and 9 above, each with its "done". Every SKILL.md's first step becomes: "Follow the working method in WORKING.md, then come back here for steps 6 and 7". The steps of the types stay as they are.
- The agent writes the result as `<name>.brief.md` beside the spec (or beside `make.py` on the author path), with fixed headings: Question, Reader, Medium, Sources read, Scope, Left out, Unknowns, Trace (element → source). A Markdown file, not a spec field, so no spec reader of the twenty types changes and a person can read it.
- The build (`build.py`) and the author kit (`Canvas.write`) look for that file. Missing: a warning `no-brief`. Present: they read the Medium line (`phone`, `screen`, `slide`, `print`, or a width in px) and run Change 2. Trace lines are counted against the drawn elements and reported as "n of m elements traced"; this is a report line, not a warning, because some elements (a start, a legend) need no source.

## Change 2: one size check from the medium, instead of shape quotas and fixed ratios

- `text-too-small` (warning): with the scene scaled to the medium's width (phone 390 px, screen 1440, slide 1280, print as given), the smallest text of a node or label is below 11 px. This replaces `long-column` (a fixed 4:1 ratio) and is the same rule for every type. A tall phone chart passes; a wide landscape chart on a phone fails, which is what run 2 showed and could not report.
- No size limit is set by the plugin. A size budget is the agent's own choice in the brief (Scope), from the question and the medium.

## Change 3: undo the parts of 0.18.0 and 0.19.0 that were patches

- Remove `few-shapes` (a proxy; a correct pipeline can be all process boxes).
- Remove the routing by input kind ("for the flow of a whole system or codebase, use the author skill") from the flowchart and author descriptions; the path is chosen after scoping, by how large and dense the scoped diagram is.
- Remove the flowchart skill's step 0; its content moves into WORKING.md, for every type.
- Author skill: "Do not drop a step" and "keep the brief's names" apply when the input is an enumerated brief; for raw input, keep what the question needs and list what was left out in the brief file. The fixed page size (3000 x 2500) gives way to the medium.
- Keep `end-has-exit` and the balanced fan-out of a split bar (general rules of meaning and layout).

## How to test that it generalises

- A held-out set, `benchmarks/heldout/`, written before any of this is built and never used to tune: raw inputs of different kinds, each with a one-line request as a user would write it and a medium. Inputs available offline in this container: a sentence only; Python standard library source (a retry or redirect path); a man page or long docstring; a meeting transcript written for the set; a CSV of tickets; an ambiguous request.
- Each has, hidden from the agent: five questions a reader should be able to answer from the picture, with answers from the source.
- Grading, outside the plugin's own check: a separate model answers the five questions from the PNG alone; five drawn elements are checked against the source; the smallest text at the medium's width is measured.
- Runs: the plugin before (0.17.0, main) and after, the same model (Sonnet), one run per brief and version at first; more runs where the two differ. The existing enumerated briefs stay as a regression set.

## Open questions for the reviewer

1. Is a Markdown brief file beside the spec the right carrier, or should it be in the spec after all?
2. Should `no-brief` be a warning or an error, given a one-line request should stay quick?
3. Is one size check from the medium enough to replace length and shape rules, or does something else need a general rule?
4. Is the held-out set wide enough, and is one run per brief enough to decide?
