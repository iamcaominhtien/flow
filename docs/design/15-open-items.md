# Open items

This page lists what is **not** finished, **not** decided and **not** tested, so that nobody assumes more than has been checked. It also records what the final review found and fixed, as an honest account of the state of the design.

## 1. Not designed yet

| Item | What it is |
| --- | --- |
| **Editing existing `.drawio` files** | Changing or restyling a diagram that already exists, as opposed to drawing a new one. It is not a new diagram type but a different way of working: the plugin must read what is there, recognise which type it is, and apply the rules here without destroying the author's layout. It needs the other types to be settled first, and it is the next design step |

## 2. Not tested yet

| Item | Status |
| --- | --- |
| **Animation in an exported SVG file, opened on its own** | The per-edge animation keys were checked in the draw.io viewer, and the viewer's SVG export is written to include the keyframes. An exported file has not yet been opened in a browser to confirm |
| **PNG and PDF export** | These cannot animate; the diagram must still read well as a still. Not checked on a real export |
| **Valid draw.io XML** | Nothing in this design has been turned into draw.io XML yet. The style strings in [Foundations](01-foundations.md) are the contract, but they have not been written into a real `.drawio` file and opened |
| **Line weights in draw.io** | The canvas draws ink lines at 2 px and the main path at 4 px; the foundation's edge styles use `strokeWidth=1.5`, and the animation recipe uses 3 for the main route and 1 for the event stream. These need to be reconciled into one table of `strokeWidth` values before the plugins write XML |
| **Readability of the two animation tiers** | The 500 ms and 1500 ms speeds were chosen by reasoning from how the viewer computes speed, not by looking at them side by side with a person |
| **Layout from rules** | The pictures were arranged by hand, with scripts, using the written rules. A plugin that arranges the same content automatically has not been written, so the rules have not been proven sufficient |

## 3. Known gaps in the design

| Area | Gap |
| --- | --- |
| **Components pages** | The first-draft kit differs in small details from later type pages (for example the sequence "actor" is a stick figure there, while the type page uses a header with an icon; the planning cards differ from the final org and mind-map cards). Where they differ, the type page is the authority. The DFD, C4 and cloud-frame entries were realigned in the final review; a full pass over the rest is pending |
| **Illustrated styles** | Missing for C4 and Cloud (plain only), and for Gantt, Kanban and Wireframe by design. Cards for C4 would need a decision on how to show the technology line |
| **BPMN** | No example of an **expanded sub-process** (a sub-process opened inside its parent); linking a sub-process to its own page is not decided |
| **Mind map** | Cross-link arcs between branches are limited by taste only; a rule of about three or four per map is proposed but not written |
| **Screen flow** | No default fidelity level has been chosen (L0 to L3) |
| **Cross-diagram links** | Several pages say "not decided yet" about linking a box in one diagram to the diagram that shows it in detail (an architecture box to its ER or sequence page, an explainer card to a technical page). No link scheme exists |
| **Icons** | There is no map-pin or location icon; the *Courier positions* store in the DFD uses the Cache icon. A few other nouns reuse the nearest icon |
| **Architecture rules** | Its "not covered yet" list (deployment detail, trust boundaries as a frame kind) is now partly covered by the [cloud](13-cloud.md) type; the architecture rules page still lists them |
| **Languages** | The design text is in English. A Vietnamese version has not been written |

## 4. What the final review found and fixed

The review before this document was written covered the whole canvas (104 boards) and these things:

| Finding | Fix |
| --- | --- |
| The same thing had two icons or tints in different types: *Payment provider* (Cloud icon on the architecture boards, Card elsewhere), and the *Orders database* (green in the cloud boards, violet elsewhere) | One icon and tint everywhere |
| The Components pages showed an older DFD (circles, offset squares), a dark-blue C4 and different cloud frames from the type pages | Components realigned with the type pages |
| The **Screen flow rules board was clipped**: its last card ran past the board frame | Board enlarged |
| Twelve rules boards still said that draw.io animation "may not survive export, not tested" or "keeps one speed", which was wrong | Replaced by the checked recipe (per-edge speed) on all of them |
| A DFD level-2 board drew a flow to the Customer that level 1 did not have, and the level-1 labels for the Customer differed from level 0 (a **balancing** error) | Level 2 corrected, labels aligned across levels, and the rule written down |
| Two DFD level-1 lines **crossed** where they should not | Entry points on process 4.0 changed so the lines no longer cross |
| Gantt and swimlane were not covered by the automatic border check | Covered now |
| The checks themselves | An automatic overlap check, a clipping check and a border lint now run before each publish |

## 5. About this document

- The pictures are **screenshots of the design canvas**, taken when this document was written. Animated lines are therefore still; the text says which lines move.
- The canvas and the scripts that drew it live **outside this repository**. This document and its images are the record inside it.
- Every statement about what an example shows was checked against the picture or the board text when written. If a board is changed later, the matching page here must be updated; the board index ([16](16-board-index.md)) lists every board and the page that describes it.
