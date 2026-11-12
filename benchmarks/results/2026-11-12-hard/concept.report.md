# Concept skill, hard brief

1. Path: quick only. 2 rounds. Round 1: exit 1, spec invalid ("'items' must list between 1 and 10 items"), no files written. Round 2 (12 parts merged to 10): exit 0, "check: no problems found" (0 errors, 0 warnings). Author path not taken: the check was clean and the picture is readable, so the skill's condition (errors or hard to read) was not met, although most of the brief is missing (see 2).

2. Counts. Brief: 1 centre, 12 parts, about 33 satellites, 16 labelled cross-links (Instrumentation fan-out counted as 4), 4 families, an analogy line, a highlighted main path. Spec: 1 centre, 10 parts (Incident response + Runbooks merged; Collection pipeline + Storage and retention merged), satellites written as extra words inside each detail line, 0 links, families only as tone, analogy in `desc`. Drawn: 1 centre, 10 cards, 10 centre spokes, the analogy under the title; 0 satellites as shapes, 0 cross-links, 0 labels, no highlighted path. The draw.io file has 48 mxCell elements.

3. Picture problems (concept/diagrams/obs.png), most serious first:
- All spokes run through the centre, the opposite of what the brief wants (links between parts). Metrics, SLO, Alerting, Incident response are not connected and the main story is not shown.
- Satellites are not drawn; they only appear as a run-on sentence in the detail ("...cheap to keep. Counter, gauge, histogram").
- Profiles card: the last detail line "Flame graph, CPU, heap" touches or is cut by the card's bottom border (the card is shorter than its text). Instrumentation card: the detail wraps awkwardly ("SDK," alone on a line).
- Families are only hinted by colour (blue, amber, green, teal); there is no legend or group label. Clockwise order puts Ownership next to Logs.
- Page is 1600x1529 for 10 parts; the ring leaves much empty space.
- Icons have mixed styles (some illustrated, some flat circles); Logs uses a doc icon.

4. Not expressible: more than 10 parts (12 asked); satellites; links between parts, arrows, link labels; highlighted path; family grouping; an analogy line other than `desc`. I merged parts to fit the limit; that loses two parts' separate identity.

5. Plugin bugs: none with a traceback. Possible check gap: the clipped Profiles detail was not reported (the check said "no problems found"). Command: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/obs.spec.json.

6. Skill text: the "up to ten" limit is stated, but the skill does not say what to do with a larger brief; the redirect to `author` is only in the last line and names "more than about 15 elements", while 12 parts plus satellites and links exceeds that in intent. The skill should say to switch before building when the brief asks for links between parts. "Hub with many lines" is vague.

Not verified: draw.io rendering (the file parses as XML; I could not render it); the HTML animation; behaviour on other viewports. I did not try the author skill.
