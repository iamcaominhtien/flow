# mind-map blind test (Vietnamese, 7 uneven branches, 3 cross links)

1. Path: quick only (no errors, so the author skill was not tried). Rounds: 1. Exit code 0. Check: 0 errors, 11 warnings: mindmap-phrase-long x9, text-may-not-fit x2 (topic n0; n64 "Chương trình khách hàng thân thiết"). To keep each link's ends on one side I set `side` by hand: right = Chiến lược, Con người, Quy trình, Công nghệ, Rủi ro; left = Khách hàng, Dữ liệu (5/2, not 4/3).

2. Counts: brief = 1 topic + 7 branches + 75 sub-items (83 nodes) + 3 links. Spec: 83 nodes, 82 tree edges + 3 links. Drawn: all 83 nodes and 3 links visible; diacritics render correctly.

3. Problems (screenshot mind-map/diagrams/full.png, 2901x2708, viewed scaled down only):
   - The three link arcs run down the right margin as one bundle, cross each other and cross leaves ("Hỗ trợ của nhà nước", "Thời gian xử lý đơn", "Gợi ý sản phẩm", "Mã độc tống tiền"). Their pills ("rủi ro", "liên quan", "dùng") are tiny. Hardest part to follow.
   - Layout is lopsided: right column very tall, left side short. Caused by my side choice, forced by the same-side link rule.
   - "Chương trình khách hàng thân thiết" overflows its pill and overlaps the line.
   - Topic label is one line wider than its card; the card's lower half is empty.
   - Depth-4 items under "Kho vận" are faint tinted boxes with no outline.
   - Legend text "Link between branches" is English in a Vietnamese map; no spec field seen to change it.

4. Not expressible: nothing in the content. The same-side link rule means links between opposite default sides need a manual `side` override and a lopsided map.

5. Plugin bugs: no crash. The topic card does not wrap or grow for a long label (warning is right, layout does not adapt). The English legend is a localisation gap.

6. Skill text: does not say how 7 branches split by default (I overrode it). Says labels at most four words, but ordinary Vietnamese phrases run 5-6 words; no advice. Does not warn that even three links on one side bundle together. Nothing says where link labels go.

Not verified: .drawio parses as XML (230 mxCell) but I cannot render it, so its look in draw.io is unknown. I did not take full-resolution crops of the HTML.
