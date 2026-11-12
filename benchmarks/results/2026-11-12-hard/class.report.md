# class skill, hard brief (document editor)

1. Path: both. Quick path, 3 rounds (round 1 = auto layout; rounds 2 and 3 = my hand `at` grid). Round 1: exit 2, 28 errors (line-through-node 26, label-covers 1, outside-canvas 1), 103 warnings (lines-cross 79, crosses-many 21, label-on-line 2, lines-overlap 3). Round 2: exit 2, 4 errors (line-through-node 4). Round 3 (final): exit 0, 0 errors, 14 warnings (lines-cross 14). Author attempt (1 try, diagrams/author/make.py): exit not tested; check 53 errors (line-through-node 40, nodes-overlap 10, outside-canvas 2, label-covers 1), 39 warnings. Quick-path files kept (diagrams/editor.*).
2. Counts: brief asks 43 classes (7 interfaces, 4 abstract, 9 concrete nodes + TableCell... incl. 2 enumerations) and about 41 relations (13 inheritance, 13 realisation, 1 composition Table-TableCell, 1 composition Document-Node, 2 aggregation, 5 Editor associations/uses, 1 History-Document, 1 dependency). Spec: 43 classes, 41 relations. Drawn: 43 boxes; lines seen in the crops of the left/top parts; I did not crop the far right/bottom (x>1400,y>1100) so I did not inspect every line.
3. Picture problems (editor.html, crops diagrams/c1.png..c5.png):
 - Page is 4110 x 3124 px with big empty areas (c3.png, c5.png); lines loop around the whole page, e.g. Editor-to-Renderer "uses" and Editor-to-Plugin "has" run across the top (c2.png, c3.png), Editor-to-History aggregation loops down the right side (c1.png).
 - Six inheritance arrowheads stack on the right edge of BlockNode and run as parallel verticals close together (c1.png); hard to tell which child goes where.
 - Table-TableCell composition runs along the page edge, "1..*" chip clipped against TableCell corner (c5.png).
 - CanvasRenderer dashed lines wrap around HtmlRenderer and Renderer region (c3.png).
 - Boxes with no members show a double bottom rule (Paragraph, TableCell, SpellCheckPlugin; c4.png).
 - 14 line crossings remain (warnings).
 - Author attempt: overlapping boxes and lines through boxes (author/a1.png); worse than quick path.
4. Not expressible: static and abstract members (I wrote "{abstract}" and "static" in the text, no italics/underline); generics in names (accepted as plain text); separate "uses" vs plain association with ends; multiplicity on a Table-to-Mark-type attribute links not requested. Also NodeVisitor's "one visit method per node" written as one visit(n: Node).
5. Bugs: none (no traceback). Observation: the build writes files and exits 2 as documented.
6. Skill text: "Fix errors by changing the spec" gives no way to fix line-through-node except hand `at`; I had to guess a grid (rows/columns) over 3 rounds, and round 1 auto layout gave 28 errors. The skill says "about ten classes fit"; the brief has 43 and the skill then says to use author, but the author skill has no class shape (TABLE + Head.TRIANGLE/DIAMOND only, no compartments, no dashed-triangle helper). Not stated: whether `at` rows can be fractional (it says half column only).
Not verified: .drawio parses as XML (173 mxCell, ok) but not rendered; far right/bottom crops not opened; author exit code.
