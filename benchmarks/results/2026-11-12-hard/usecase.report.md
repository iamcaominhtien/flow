# usecase, hard brief

1. Path: both. Quick: 3 rounds. R1 exit 2, 27 errors (line-through-node 20, caption-covered 7), 9 warnings (label-on-line). R2 (actors reordered) exit 2, 35 errors (28/7), 8 warnings. R3 (Registered user first) final exit 2, 28 errors (line-through-node 21, caption-covered 7), 9 warnings (label-on-line). Author: one script, one build, one screenshot round, exit 2: 5 errors (label-covers 3, caption-covered 2), 86 warnings (lines-cross 38, lines-overlap 24, label-on-line 17, crosses-many 6, crosses-border 1).

2. Counts. Brief: 10 actors, 31 use cases, 2 boundaries, 52 links (3 generalisations, 8 includes, 7 extends, 34 associations), 2 extend conditions. Quick spec: 10, 31, 1 frame, 52 links; drawn: 31 ellipses and all actors, one frame. Author: 10, 31, 2 frames, 52 lines, all drawn (checked in f.png and crops).

3. Problems, most serious first.
- Quick: one frame "Learning Platform + Assessment Engine" instead of two (diagrams/full.png, c1.png, c2.png).
- Quick: long diagonal lines run through many ovals and across each other; Student, Lecturer lines fan over the whole frame; actor captions struck (Registered user, Teaching assistant, Department administrator); page 1764 x 3281. Hard to read who does what.
- Author (diagrams/author/f.png, a1.png, a4.png): I moved Visitor, Registered user, Student, Lecturer, Teaching assistant and Department administrator into a gutter between the two frames, and Identity Provider and Payment Gateway to the far left, so lines stay short. This departs from the brief's left/right placement. Lines of one actor share a trunk, so overlap warnings are mostly intended buses. Remaining faults: the Student Records System to Generate transcript line runs round the bottom and crosses the TA/Admin lines; Student to Registered user line crosses that caption; the "course is full" extend label collides with an include label; four dashed «include» lines to Sign in run about 10 px apart and are hard to tell apart; Create assignment/quiz and other Lecturer lines are bunched.
- Author: use cases are pills, not UML ovals (no oval shape in the kit); frame is blue, ovals have a green outline.

4. Not expressible in the quick spec: two boundaries; abstract actor (I put "(abstract)" in the label); placing actors freely. Author kit: no oval, no abstract (italic) marking.

5. Plugin bugs: none crashed. Check messages print the external actor label with a raw newline ("Student Records System\n«external system»"), splitting one error over two lines (run the quick build).

6. Skill text: usecase skill names the legacy `zones` form but never describes it, so two frames were not attempted there. The direction of `generalizes` (child to parent) is not stated. Fixes allowed "by changing the spec" have almost no lever beyond order of actors; my reorder in R2 made it worse. The author skill has no use-case example.

Not verified: draw.io rendering (both .drawio files parse as XML; not rendered). I did not open a2.png and a3.png (top right and lower left of the author picture); the AE frame top was seen only in f.png at reduced scale, which I did not open.
