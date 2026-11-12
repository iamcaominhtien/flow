# Blind test: state skill, ride trip brief

1. Path: both. Quick: 1 build, exit 0, 0 errors, 35 warnings (label-on-line 14, lines-cross 17, text-may-not-fit 2, crosses-border 2). No fix round (no errors). Author (diagrams/author/make.py): 2 runs, final exit 0, 0 errors, 3 warnings (lines-cross 1, crosses-border 2). The skill asks for 3 or more looks; I did fewer.

2. Counts. Brief: about 26 named states plus initial, choice, two regions, history; about 45 transitions with "from any substate" expanded. Quick spec: 27 states incl. start, 4 composites, 45 transitions; scene 25 nodes, 3 frames (Assigned, Movement, Safety; no InProgress), 45 edges. Author: 26 nodes (choice diamond included), 4 frames, 46 edges. Both .drawio files parse as XML; not rendered (no draw.io here).

3. Problems, quick path (diagrams/full.png, c1-c4.png), worst first:
- InProgress is not drawn as a frame; Movement and Safety are separate frames, Safety far bottom left; Completing straddles Movement. Nesting and regions lost.
- Page 2950 x 1477 with page-long lines (driverCancelled, riderCancelled, reconnected); around Driving the lines destinationChanged, resume, routeReady, connection lost, reconnected are stacked within a few px, so chips cannot be matched to lines.
- Closed and WrittenOff labels are covered by lines.
- The gpsUpdate chip hides the Assigned pill.
- Large empty lower right.
Author path (author/full.png), much clearer. Left: Closed and WrittenOff are small rings but lines attach to an invisible 160 px box, so "rated" and the right-hand arrows stop short of the Closed ring; failure states have a blue fill because I gave a tone (my choice); the blue Arrived to Driving line crosses the "Region Movement" pill; start is a plain green circle, not a filled dot; one crossing. I looked only at the downscaled full view, no crops.

4. Not expressible: parallel regions (nearest: two dashed frames), history pseudostate (label text), choice pseudostate (guards in quick path; diamond in author), transitions from a composite (drawn from each substate; InProgress to Suspended drawn from Driving only), "after" timers (event text).

5. Bugs: (a) quick path loses the InProgress frame when a composite holds two nested composites: `python3 plugins/flow/scripts/flow.py build diagrams/ride.spec.json` gives 3 frames. (b) Author kit: Shape.END/FAIL with width/height 64 gives a small ring but ports sit at the 160 px box, so side-attached lines float (see Closed).

6. Skill text: no advice for "from any substate" or for choice, history and regions; nested composites are not mentioned (the example has one level) though the build accepts them and then drops a frame silently. The quick skill's 15-element threshold for the author skill was clearly met here (about 26 states) and the author result was the better one.

Not verified: draw.io rendering; author picture at full zoom.
