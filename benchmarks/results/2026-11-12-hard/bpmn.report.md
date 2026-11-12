# BPMN blind test report

1. Path: quick only, 3 builds (1 + 2 fixes), exit 2 each time. Round 1: 26 errors (line-through-node 20, caption-covered 6), 32 warnings. Round 2: 26 errors, 27 warnings. Round 3 (final): 17 errors (line-through-node 15, caption-covered 2), 32 warnings (mostly lines-cross, plus crosses-many 2, label-on-line, lines-overlap, bpmn-too-many-elements: 56 elements). I did not itemise the final warnings further. Step 3 (author skill) not done: untested for this brief.
2. Counts: brief asks for about 50 elements and about 10 message flows. Spec: 56 elements, 7 zones, 65 flows (10 message). Scene: 56 nodes, 65 edges, all drawn. I added elements the brief only implies: Notify approval, Receive approval, Receive offer, Accept offer, Receive excess, and a "Rejected?" gateway for the policyholder.
3. Wrong or hard to read (diagrams/r3.png full, r3_left.png, r3_right.png):
 - Long vertical message flows run through insurer-lane tasks: "Send offer" has three dashed lines through it; "Receive excess" and "Calculate market value" are crossed (r3_right.png).
 - The blue main path runs through the end event "Claim rejected (fraud)" and its caption (r3_left.png, bottom).
 - The red "Fraud confirmed" flow passes through "Send rejection letter" in the adjuster lane.
 - Timer boundary "10 days" overlaps the label of "Request police report" (r3_left.png).
 - "Not active" line runs along the lane crossing 9 lines; a "Total loss" line runs the height of the Insurer pool.
 - Page is 3696 px wide; chips "revise" and "approval" sit far from their lines.
 - "Receive offer" and "Accept offer" have no sequence flow and look floating.
4. Not expressible: error end event inside the collapsed subprocess (used a boundary error event); "at most twice" on the revised quote (label only); loop-backs are `return` flows with no loop marking; event-based wait of the policyholder (used receive task plus exclusive gateway).
5. Plugin bugs: no traceback. Duplicate identical message flows are accepted without a warning.
6. Skill text: no way to steer a message flow's route; `column` pins are guesses unless one reads column positions from `claim.scene.json`, which the skill does not mention. "Warnings may stay" is hard to apply with 56 elements when the check itself says to use sub-processes. It does not say whether a message may end at an end event (it was accepted).
Not verified: .drawio rendering (parses as XML, 177 mxCell elements); animation; r3.png full page was only viewed through two crops.
Files: bpmn/diagrams/ (claim.spec.json, claim.html, claim.drawio, claim.scene.json, r3*.png).
