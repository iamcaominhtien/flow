# Roadmap blind test report

1. Path and rounds
- Path: quick only. I did not run the author skill (step 3). The skill points to it for this size, and the picture is partly hard to follow, but it has no errors. The author attempt was not made.
- Round 1: exit 1. Spec invalid: "'Passkeys' cannot start before 'Zero-trust network' (earlier period)". No files written.
- Round 2: I dropped the backwards dependency and drew Instant payouts depends_on Ledger v3 instead. Exit 0, check: 0 errors, 1 warning (text-may-not-fit: lane-5 "Security and compliance" label).
- Final: exit 0, 0 errors, 1 warning.

2. Counts
- Brief asks for: 6 periods, 6 lanes, 39 items (the penetration test is one item with two dates), 7 dependencies, 4 milestones, 1 today marker, 4 statuses.
- Spec has: 6 periods, 6 lanes, 40 cards (the penetration test split into two), 1 dependency, 0 milestones, 0 today marker. Status is plain text in each card's `detail`.
- Visibly drawn: 6 periods, 6 lanes, 40 cards, 1 arrow. Milestones, today, the other 6 dependencies and the conflict exist only as text in the bottom note.

3. Problems in the picture (roadmap/diagrams/full.png)
- The page is 4373 x 3235 px but the chart is only about 1650 px wide. The bottom note is one line about 4300 px long and sets the page width; at normal zoom the chart sits in the upper left and the note is tiny. I read it only in the full screenshot.
- Six of the 7 dependencies and the Passkeys conflict are not drawn. Milestones and "today" are not drawn.
- Status is not visible at a glance. Every card carries a green "Committed" tag, including "at risk" cards (Instant payouts, Offline mode), and the status word is small grey text. All cards are white.
- The single arrow (Ledger v3 to Instant payouts) shows only a small blue arrowhead above Instant payouts, in the Payments lane; I did not open a crop of it. It is easy to miss.
- Stacking order inside lanes does not follow time (for example Platform: Zero-trust network sits above Multi-region failover). Rows are tall and leave much empty space.
- The label of lane 6 "Security and compliance" looks cramped at the lane's bottom (the warning).
- Period headers show only "27Q1" and so on, with no year or quarter detail.
- .drawio: written; parses as XML (195 mxCell elements). I cannot render it here.

4. What the skill could not express
- Status (done, in progress, planned, at risk) as a colour or tag. Nearest: text in `detail`. `committed:false` means "Exploring", which is not the same.
- More than one dependency (a stated limit), and a dependency that points backwards (refused, exit 1). Nearest: described in the note.
- Milestones on the axis and a "today" marker. Nearest: the note.
- One item with two separate periods (Penetration test). Nearest: two cards.

5. Plugin bugs
- No traceback. Possibly a bug: the generated note makes the page 4373 px wide. Reproduce: `python3 /home/user/flow/plugins/flow/scripts/flow.py build diagrams/roadmap.spec.json`, then open the HTML.

6. Unclear parts of the skill
- The skill says to pick "the one" dependency but does not say what to do with the others, or with a backwards one. Both Passkeys and 6 others had to go to the note.
- The skill does not say how to show status. It says "Committed" is the default, and the tag is then misleading for done and at-risk items.
- Icon names such as cloud, phone and shield worked, although the skill lists only some; I did not check the full list.

Not verified: the draw.io rendering, the arrow in a crop, any author-skill result, and the text fit beyond the one warning.
