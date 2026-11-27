# Working method: from any input to a diagram

Every Flow skill draws. This page is the work before and after drawing, the same for every type and every input: a sentence, a document, a codebase, a transcript, a table. A diagram is a summary of what you understood; you cannot summarise what you have not read, and the check report only says the picture is well drawn, not that it is right.

## Before drawing

1. **Purpose.** Who will read it, and which question it must answer for them. Done when you can write the question in one sentence. If the request does not say and you cannot tell, ask.
2. **Medium.** Where it will be read: a phone, a screen, a slide, print, or an editor (draw.io). Done when you know the width it will be seen at. Flow's diagrams are designed for screens and no layout fits a phone's width at a readable size. For a phone: run the flow top to bottom (`"direction": "down"` where the type has it), keep each diagram small by drawing an overview and one diagram per part, or arrange it by hand with `/flow:author`; and tell the reader they will need to zoom.
3. **Understand the source.** Read the primary source as deep as the question needs, and no deeper. A summary of the source is a claim about it, not the source: check it against what it summarises before you draw from it. Done when you can walk one concrete case through the subject from start to end, you can say where each fact comes from, and you have listed what you could not find out.
4. **Type.** Choose it from what has to be shown (steps and decisions, messages over time, states, structure, data, time) and from the question. A type named by the user is a strong hint; if it does not fit, say so and offer the one that does.
5. **Scope and level.** Where the diagram starts and ends, what is in and what is out, one level of detail per diagram. When one diagram cannot answer the question at a readable size, draw an overview and one diagram per part. Done when what you left out is written down.

Write this down before the spec or the script, one line per field, as `<name>.brief.md` in the folder of the spec and with the spec's name (on the author path, in the folder and with the name you pass to `canvas.write`):

```
Question: <one sentence>
Reader: <who>
Medium: <phone, screen, slide, print or editor>
Sources read: <files, sections, pages or times you actually read>
Left out: <what is not drawn, and why>
Unknowns: <what you could not find out>
```

`flow.py build` and `canvas.write` print it back with the check report, and warn when the file or one of its lines is missing. They do not judge it: it is for you and the person you deliver to.

## Drawing

6. **Model**, then 7. **lay out and draw**, with the type's skill. Choose the path after the scope is set: the type's skill (one automatic layout, quick) when the diagram is small and sparse, `/flow:author` (you place everything and look at the result) when it is large or dense, or when the automatic layout's picture does not answer the question at the medium's size.

## After drawing

8. **Verify.** Against the source: walk two or three cases (the usual one and a failure or edge case) along the picture and check each step against the source. Against the reader: run `node ${CLAUDE_PLUGIN_ROOT}/scripts/view.js <name>.html <medium>` (phone, screen, slide, editor or print; it needs Chromium and Playwright; the page is next to the spec, or in the folder you passed to `canvas.write`), open `<name>.<medium>.png`, the diagram as the reader first sees it, and check the question can be answered from it. `<name>.png` is the whole diagram at full size, to deliver. If you cannot render the page, say so.
9. **Deliver.** Give the picture and say, in a few lines: the sources read, what was left out, what is uncertain, and what a next, more detailed diagram could show.
