# Kanban hard-brief test report

1. Path: quick only (skill points to author only for large diagrams; I did not run Step 3 because the quick picture has no check errors, only visible overflow on 3 cards). Rounds: 1 build, no fix round. Final exit code 0. Check: 0 errors, 41 warnings: kanban-card-full x38, kanban-over-limit x3 ('7 / 5', '4 / 3', '5 / 4').

2. Counts. Brief: 7 columns, 2 lanes, 48 cards (4 urgent + 44 normal), 6 owners, 4 kinds, 3 blocked normal + NH-420 blocked, 5 normal deadlines + 2 urgent deadlines, 2 titles over 12 words, legend of 4 kinds, one totals line. Spec: 7 columns, 0 lanes, 48 cards, 6 owners, 4 kinds, 4 blocked, 7 deadlines, 3 titles over 12 words (NH-418, NH-440, NH-449), legend and totals only inside the title text (Tổng 48 thẻ, 61 điểm đang làm dở; I counted "đang làm dở" as the 3 columns Đang phát triển, Chờ xem xét mã, Đang kiểm thử, my assumption). Drawn: all 48 cards, 7 columns; no lanes, no legend, no totals line as separate elements.

3. Wrong or hard to read (shots in diagrams/):
- No horizontal lanes. I merged urgent cards to the top of each column and marked them with "KHẨN CẤP" in small detail text; urgent and normal cards look the same (c1.png, c2.png).
- Three cards overflow: NH-418 (3-line title overlaps the tag and "điểm · Hạn 15/11", c2.png); NH-440 (4-line title overlaps tag and points, text cut off, c3.png); NH-449 (title overlaps tag, c3.png). The 2 long-title cards cannot be shown within 100 px.
- "Bị chặn" and "Hạn" are only small grey text in detail; no distinct label, so blocked cards do not stand out.
- Over-limit pills (7 / 5) have the same red as full (6 / 6, "Chờ phát hành"), so the required highlight of Đang phát triển is not distinguishable from a full column. Per-lane counts in the brief give no overflow in the other columns, but combined counts are over the limit in Chờ xem xét mã (4/3) and Đang kiểm thử (5/4); ambiguous, I counted both lanes.
- Page is 2828 x 1821; board is wide, title with legend is a plain text line, kind colours are only explained by text.
- Done column: all cards struck through and faded, hard to read; the pill shows only 7 (no limit), fine.
- 38 card-full warnings are mostly false alarms: cards with a 2-line title plus detail render fine.

4. Not expressible: swimlanes (rows) across columns; a "Bị chặn" label or a deadline field (only free detail text); separate legend; summary row with totals; per-card code field (put in label); emphasis style for an over-limit column; titles over 2 lines.

5. Plugin bugs: none with traceback. Mismatches: kanban-card-full flags cards that visually fit (build output of the spec); real overflow of 3-line+ titles in NH-418, NH-440, NH-449 is flagged identically to fitting cards, so the warning does not tell them apart.

6. Unclear in skill: "keep the title to two lines" has no word/character guidance for Vietnamese diacritics; Feature/Bug/Chore colour mapping only for English words (I set tone by hand); skill does not say how to show lanes or blocked/deadline; "Warnings may stay" conflicts with 41 warnings, some real.

Not verified: .drawio parses as XML (checked, OK) but was not rendered; I did not view the bottom of columns Chờ phát hành / Hoàn thành, nor the full page as one image.
