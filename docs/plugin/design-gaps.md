# Design gaps

Where each Flow type differs from its page in `docs/design/` (the frozen design). Written by reading the design pages, the skill docs and the code, and by putting a render of one example next to the design's complete example. The plan to close the gaps is phased: foundations, flow-like types, structure types, UML, planning, explainer and wireframe.

Status: **missing** = not built, **partial** = built but not to the page, **checked** = looked at in a picture.

## Seen in a picture (ours next to the design)

| Type | What differs |
| --- | --- |
| Screen flow | Missing: device frames, fidelity levels, S ids, trigger chips, guards, hotspots, zones, entry pills, tab bus, overlays. Ours is plain boxes. |
| Sequence | Close: lifelines, bars, frames, notes, create and destroy, lost and found are there. Missing: illustrated headers; pitch is 270 px against 230. |
| Gantt | Missing: month header, status colours and fill, today line, milestones, owner circles, phase bands, dates. Dependencies are drawn. |
| BPMN | Structure is close (pools, lanes, timers, gateways, message flows). Missing: start and end event types, boundary events, task markers, black-box pool, data store. |
| DFD | Missing: Gane-Sarson shapes (numbered strip, open-ended store with id cell, square entity), ids, balancing, forbidden-link checks. Ours draws an ellipse and flat boxes. |
| State | Missing: `event [guard] / action` labels, entry and do lines, composite frame, self loop, several ends, left-to-right happy path. |
| Mind map | Missing: radial layout, curved coloured lines, icon pills, leaf cards, cross links, priority and owner marks. Ours is a plain tree. |

## Read in the docs and skills, not yet seen in a picture

Architecture (frame-edge lines, event and copy line kinds, patterns), concept and layers (explainer: comparison, concept hub, numbered badges, bands, closing line), org chart (bus, open role, works-with line), Kanban (limits, kind tags, owners), roadmap (committed and idea cards, dependency arrow), class (multiplicity, visibility, abstract, interface), use case, wireframe (real blocks, annotations, state and responsive sets), C4 (levels, technology line, external look, frame label), cloud (frame kinds, trust rules), flowchart (parallel bars, connector notes, number letters, data role).

## Foundations

Themes *Technical clean* and *Midnight* are missing. The canvas weight to `strokeWidth` table is not written down. Type scale, callout tag and root node are unchecked.
