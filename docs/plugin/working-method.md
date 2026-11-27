# Working method: from any input to a diagram

Status: version 2 of the design, after one review (an independent agent, 2026-11-27). Built in 0.20.0 and fixed after a second review of the code; not yet measured. The held-out briefs that will measure it, and the rule that decides, are in `benchmarks/heldout/` and were committed before the build.

## The gap

Every skill starts from a brief that already lists what to draw: the pipeline is "brief (words) → spec" (`design.md`), the author skill's first step was "Read the brief. List every step", and every benchmark brief enumerates its elements. So the plugin teaches and measures transcription plus layout. It does not teach, and nothing measures, the work before that: what the diagram is for, understanding the source, choosing what to leave out, and checking the picture against the source. On raw input an agent does what the skills ask: it finds something that looks like a brief (in two blind runs on the x-algorithm repo, the README's own box diagram), transcribes it, and stops when the check report is clean.

## What a person does

1. **Purpose.** Who reads it, which question it answers. Done: one sentence.
2. **Medium.** Where it is read: phone, screen, slide, print, an editor.
3. **Understand the source.** As deep as the question needs. Done: you can walk one concrete case through it and say where each fact came from; unknowns are listed.
4. **Type.** From the structure of what is shown and the question; the user's word is a strong hint, not a rule.
5. **Scope and level.** Start, end, in, out; one level of detail per diagram, with an overview and linked details when one is not enough. Done: what was left out is written down.
6. **Model**, 7. **Lay out and draw:** the type's skill (build path or author path).
8. **Verify.** Walk two or three cases on the picture against the source; look at the picture at the size it will be read.
9. **Deliver.** The picture, the sources, what was left out, what is uncertain, the next level of zoom on offer.

## What the review changed, and why

- Prose alone did not change behaviour: run 2 had "read the source itself (not only its README)" inline in the flowchart skill and still drew from the README. So the method is not only text to read: it produces a file the tools read back and print, and the last step makes the agent tell the user its sources and omissions. That makes a shallow reading visible to the person, which is the only general check of step 3 there is; nothing in the tool judges understanding, and the held-out briefs measure it.
- No trace table (element → source): self-reported, and "every element → README.md" would pass it.
- No size check from the medium. Measured with `benchmarks/measure_text_size.py` on the 78 examples that have node text: fitted to a phone's 390 px, the smallest node text is 1.3 to 6.6 px (edge labels are smaller still); even the narrowest one-column flowchart (704 px) gives 6.6 px. The build path has no narrow format, so a warning would fire on every phone diagram and tell the agent nothing it can act on. **Open issue: Flow has no phone format.** That is a gap in the design system (node widths, margins, text sizes), to be designed on its own.
- The text-too-long rule counts words separated by spaces; it fires on short Vietnamese phrases (one word per syllable) and never on Chinese or Japanese. A language proxy; recorded here, not changed now.

## The change

1. **`plugins/flow/skills/WORKING.md`**: steps 1-5, 8 and 9 with their "done". Not a skill, so routing cannot skip it.
2. **The same short block at the start of every SKILL.md** (a test keeps the copies identical): before the spec or the script, follow WORKING.md and write `<name>.brief.md` beside the spec (on the author path, in the output folder, as `<folder>/<name>.brief.md`), with the lines `Question:`, `Reader:`, `Medium:`, `Sources read:`, `Left out:` and `Unknowns:`. And at the end: tell the user the sources read and what was left out.
3. **The build and the author kit read the brief back.** `flow.py build` and `Canvas.write` look for it; if present they print its `Question`, `Medium`, `Sources read` and `Left out` lines with the report, and if missing they print a warning `no-brief`. Nothing else is parsed.
4. **Undo the patches of 0.18.0 and 0.19.0:** remove `few-shapes` and `long-column`; remove the routing by input kind from the flowchart and author descriptions; remove the flowchart skill's step 0 (now WORKING.md). Keep `end-has-exit` and the balanced fan-out of a split bar.
5. **Author skill:** "do not drop a step" and "keep the brief's names" apply to an enumerated brief; for raw input, keep what the question needs and list what was left out. The fixed page size gives way to the medium.

## How it is measured

`benchmarks/heldout/`: seven raw inputs of different kinds, two runs per brief and version, graded by a separate model that answers five questions per brief from the PNG at the medium's size, against a control with no picture. The decision rule is in that README and was fixed before the runs.
