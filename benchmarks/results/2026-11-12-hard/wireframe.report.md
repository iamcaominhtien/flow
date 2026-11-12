# Wireframe blind test report

1. Path: quick only. The author skill was not tried (step 3 skipped for effort, although the skill points to it and the picture is hard to read). The skill allows one set per spec, so the brief became 3 specs: p1 (responsive), p2 (states), p3 (phone flow, no set).
Rounds: spec p1 failed validation twice (exit 1: navbar items and sidebar icons must be lists of strings), then crashed (RecursionError) on unknown icon names, then built. Final: p1 exit 0, 0 errors, 5 warnings (wireframe-too-tall x5: desktop table and text, tablet chart, table, panel). p2 exit 0, 0 errors, 1 warning (wireframe-too-tall, loading). p3 exit 0, no problems. No error rounds were needed, so the three fix rounds were not used for the warnings (the skill lets warnings stay).

2. Counts. Brief: 3 widths, about 40 desktop elements, 2 chart types, 8 table rows, 5 feed items, 4 states, 3 flow screens, at least 10 notes. Spec: 11 screens, 12 notes, 8 table rows on desktop, 5 feed items (panel children), 4 KPI cards. Drawn: desktop table 8 rows (overflows the device), feed 5 items but squeezed to unreadable text; notes 12 drawn; no sparklines, no donut, no line chart, no pagination, no row actions, no sortable header arrow, no collapse control, no carousel, no cards-list table on phone, no 5-item tab bar labels beyond generic.

3. Wrong or hard to read (most serious first):
- p1.png: Desktop table runs below the device and spills over the notes area; tablet chart, table and feed spill out of the device; table and chart cover notes 7, 8, 9 and the tablet notes text (all unreadable).
- p1.png: Desktop header row is clipped ("Revenue over", "ast 30 day", "mpa", "xpo", "Acme Analytic"); KPI values cut ("$48", "1.8"); feed items are narrow cut slivers ("N", "G"); filter chips run past the screen edge ("Owner: Me", "Add filter" lost).
- p1.png: Line and donut charts are both drawn as bars. Sparklines cannot be drawn.
- p1.png: Tablet and phone notes in the header ("640 to 1023 px...") are cut at both ends.
- p1.png: Phone: the FAB is a full-width blue bar with "+", not a floating button; the bottom bar icons are all the same document icon; the "Globex" row is cut ("$1,90"); the carousel is two static cards.
- p1.png: Tablet icon rail is a full-width sidebar showing letters, not a narrow rail.
- p2 (p2a.png, p2b.png): Loading screen has more skeleton rows than fit, one row and the spinner sit outside the device. Notes 10 and 11 sit under the wrong screens (10 under Loading, 11 under Empty though they point at screen 4; the badges are on screen 4). The selected-rows screen shows the bulk bar as three full-width stacked buttons, not a bar. Empty icon is a shopping cart. Table is not "alone" on the loading, empty and error screens: it is replaced by the state block, with no table header.
- p3.png: the tap dot on "MRR" covers the trail link text; chart type tiles have no tile icons; Save at the bottom and Cancel is placed far above it.

4. Not expressible: sparklines, line and donut charts, floating action button, icon rail, carousel, banner with Retry above a table, bulk action bar (horizontal), pagination, sortable header arrow, row actions, checkbox column, collapse control, the three parts as one page, a delta on a KPI beyond a chip. Sidebar groups (two groups) are not available.

5. Bugs: unknown icon name causes infinite recursion between icon_svg and detailed_icon_svg in flowlib/theme.py (lines 1406 and 1428), no message. Command: python3 scripts/flow.py build diagrams/p1.spec.json with sidebar icons ["users","settings"] (valid names: user, gear, home, chart, file, bell, database, card). Also `address` at top level gave "unknown field" (screen field only).

6. Skill text unclear: valid icon names are not listed; `items` and `icons` must be lists of strings but the text does not say so; the number of notes per screen versus note number order; whether `set` allows a screen with the table alone; how a state set shares one address; that a note under a screen is placed by order, not by target screen.

Not verified: the .drawio files only parse as XML (ok for all three), not rendered. Author skill not attempted.
