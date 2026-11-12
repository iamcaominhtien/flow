# Explainer blind test report

1. Path: quick only (the skill never points to the author skill). Rounds: 4 build runs. Run 0 was exit 1 (analogy left/right must be single cards, not lists). Round 1: exit 2, 11 errors (10 outside-canvas, 1 line-through-node), 7 warnings. Round 2: exit 2, 2 errors (line-through-node, return line crossing the band remarks), 1 warning. Round 3: exit 0, 0 errors, 1 warning (explainer-too-many-cards, 13 cards). Final: exit 0. Files: diagrams/tap.spec.json, tap.html, tap.drawio, tap.scene.json. The .drawio parses as XML (ElementTree); not rendered, no editor here.

2. Counts. Brief asks: 14 steps in 5 bands; 5 analogy mappings; 3x5 comparison cells (15); 4 tree branches (+ root, 4 sub-reasons per branch); 3 call-outs. Spec: 13 step cards (step 12 is a labelled return link, not a card); analogy as 2 cards; comparison with 2 columns plus 1 text box for the third; tree root + 4 rows; 3 facts + hub. Drawn: all of those, but the step numbers are wrong (see below). Fewer than asked: step 12 card, 5 separate analogy pairs, Phone wallet column (10 of 15 cells filled; 5 are a sentence), the "Later that night" band holds one card.

3. Problems, most serious first (screenshots c0.png, c1.png, c2.png in diagrams/):
- Step numbers are wrong (c0.png, c1.png). Cards auto-number 1..13 in reading order: "The reader beeps" shows 4, processor 5, acquirer 6, network cards 7-9, bank cards 10-12, money moves 13. The brief's 1-14 numbering is lost. I did not set `number` per card; the skill says it exists, but I did not test it (round limit reached). The "12 the answer travels back" chip is a tiny label.
- Analogy section (c1.png) is two big cards joined by an arrow; the five role mappings are squeezed into sentences, and the left card's text overflows its box ("weekly." below the border).
- "The money actually moves" text overflows its card ("next day." below the border, c1.png).
- Comparison (c1/c2.png): the Phone wallet column is missing; it is a plain box under the table. The row labels sit between the columns and the column header cards are very large, so the table is split across a page break in my crops (not an actual defect).
- Return path from step 11 to the reader is a long grey dashed vertical on the right; its label is tiny and hard to read. The journey is one-way zigzag, and "next day" label sits at the band edge.
- Numbers-to-remember (c2.png) are numbered 1, 2, 3 and linked by arrows from a hub, which suggests a sequence; the hub card is unnecessary.
- Page is 1884 x 3894 px; the section layers area is wider than the stated 1500.
- Band remarks (definitions) collide with the return line, so I moved the definitions into card text.

4. Not expressible: a comparison with three columns (only left/right); an analogy as five mapped pairs (only two cards); a 14th numbered step as a card for the return trip without a card; call-outs without a hub; sub-branches of the decline tree (the `inside` chips exist but I did not use them; I put them in text).

5. Plugin bugs: none with a traceback. The layers shape errors "outside-canvas" when columns 4-5 are used inside a `sections` layers block (cols 0-3 fit), though the skill says layers is 1500 px wide. Command: flow.py build with my first spec (cols 0-5).

6. Unclear in the skill: how wide a layers block is inside `sections` (how many columns); that a card per line link is needed for returns; the analogy `left`/`right` must be one card each (the text says "keys of the concept's analogy" without shapes); how to model the comparison with three things; "Four to eight cards" conflicts with a 14-step brief, so the warning cannot be fixed without dropping content.

Not verified: draw.io rendering, animation, reduced-motion, mobile width, step-number override.
