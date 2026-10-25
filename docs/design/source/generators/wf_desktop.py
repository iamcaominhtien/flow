from wflib import *
W, H = 1520, 1260
b = Board('Wireframe_Desktop', 'Annotated wireframe: restaurant dashboard', W, H,
  'A desktop screen built from the same blocks: top bar, side menu, figures, chart, a list and a table. Numbers point at details, notes are below.')
FX, FY, FW, FH = 100, 190, 1320, 760
b.raw(f'<div style="position:absolute;left:{FX}px;top:{FY}px;width:{FW}px;height:{FH}px;box-sizing:border-box;border:3px solid #0F172A;border-radius:16px;background:#F8FAFC;overflow:hidden"></div>')
# browser bar
R(b, FX + 3, FY + 3, FW - 6, 40, G2, G2, 0, 0)
for i, c in enumerate(['#F87171', '#FBBF24', '#4ADE80']): R(b, FX + 20 + i * 20, FY + 16, 12, 12, c, c, 6, 0)
R(b, FX + 120, FY + 9, 560, 28, '#fff', G3, 14); T(b, FX + 140, FY + 14, 'console.padthai.example/orders', 12, 500, '#475569')
# top bar
TY = FY + 43
R(b, FX + 3, TY, FW - 6, 56, '#fff', G3, 0, 1.5)
R(b, FX + 24, TY + 14, 28, 28, BLUE, BLUE, 8, 0); T(b, FX + 62, TY + 17, 'Restaurant console', 15, 800, '#0F172A')
R(b, FX + 420, TY + 11, 420, 34, G1, G3, 17); b.raw(icon_svg('clock', FX + 436, TY + 19, 18, G4)); T(b, FX + 462, TY + 18, 'Search orders, dishes, customers', 12, 500, G4)
b.raw(icon_svg('bell', FX + FW - 130, TY + 17, 22, '#334155')); icon_dot(b, FX + FW - 80, TY + 10, 36, 'user')
# sidebar
SX_, SY_, SW_ = FX + 3, TY + 56, 220
R(b, SX_, SY_, SW_, FH - 6 - 40 - 56, '#fff', G3, 0, 1.5)
for i, (t, ic) in enumerate([('Orders', 'cart'), ('Menu', 'doc'), ('Reviews', 'star'), ('Payouts', 'card'), ('Settings', 'check')]):
    y = SY_ + 20 + i * 48
    if i == 0: R(b, SX_ + 12, y, SW_ - 24, 38, '#DCEEFB', '#DCEEFB', 8, 0)
    b.raw(icon_svg(ic, SX_ + 26, y + 9, 20, BLUE if i == 0 else G4)); T(b, SX_ + 58, y + 10, t, 13, 700, BLUE if i == 0 else '#334155')
# main
MX, MY = SX_ + SW_ + 28, SY_ + 22
MW = FX + FW - 3 - MX - 28
T(b, MX, MY, 'Today', 22, 800, '#0F172A'); chip(b, MX + 80, MY + 5, 'Fri 24 Oct', 'gray')
btn(b, MX + MW - 130, MY - 4, 130, 'Pause orders', 'danger', 36)
kw = (MW - 3 * 16) / 4
for i, (k, v, d, tone) in enumerate([('Orders', '42', '+8%', 'green'), ('Revenue', '$1,280', '+5%', 'green'), ('Prep time', '14 min', '+2 min', 'amber'), ('Rating', '4.7', '0.0', 'gray')]):
    x = MX + i * (kw + 16)
    R(b, x, MY + 46, kw, 92, '#fff', G3, 12); T(b, x + 16, MY + 58, k, 12, 600, '#64748B'); T(b, x + 16, MY + 80, v, 26, 800, '#0F172A'); chip(b, x + 16, MY + 112, d, tone)
cwid = MW * 0.58
R(b, MX, MY + 156, cwid, 222, '#fff', G3, 12); T(b, MX + 16, MY + 168, 'Orders per hour', 13, 800, '#0F172A')
for i, hgt in enumerate([40, 62, 90, 130, 150, 110, 80, 96, 60]):
    x = MX + 30 + i * ((cwid - 60) / 9)
    R(b, x, MY + 356 - hgt, (cwid - 60) / 9 - 12, hgt, BLUE if i == 4 else G3, BLUE if i == 4 else G3, 4, 0)
b.raw(f'<div style="position:absolute;left:{MX+16}px;top:{MY+357}px;width:{cwid-32}px;border-top:1.5px solid {G3}"></div>')
lx = MX + cwid + 16; lw = MW - cwid - 16
R(b, lx, MY + 156, lw, 222, '#fff', G3, 12); T(b, lx + 16, MY + 168, 'Needs attention', 13, 800, '#0F172A')
for i, (t, s, tone, c) in enumerate([('Order #1043 late', '5 min over', 'rose', 'Late'), ('Out of stock: tofu', 'Hide dish?', 'amber', 'Stock'), ('New review 2★', 'Read it', 'blue', 'Review')]):
    y = MY + 198 + i * 56
    R(b, lx + 12, y, lw - 24, 48, G1, G2, 10); T(b, lx + 24, y + 7, t, 12.5, 700, '#0F172A'); T(b, lx + 24, y + 26, s, 11, 500, '#64748B'); chip(b, lx + lw - 24 - 14 - 7 * len(c), y + 13, c, tone)
ty0 = MY + 396
R(b, MX, ty0, MW, 190, '#fff', G3, 12); T(b, MX + 16, ty0 + 12, 'Live orders', 13, 800, '#0F172A')
cols = [('#', 0), ('Customer', 70), ('Items', 250), ('Status', 470), ('Due', 610), ('', 720)]
for t, off in cols: T(b, MX + 20 + off, ty0 + 42, t, 11, 700, '#64748B')
b.raw(f'<div style="position:absolute;left:{MX+12}px;top:{ty0+62}px;width:{MW-24}px;border-top:1.5px solid {G2}"></div>')
for i, (n, cu, it, st, tone, due) in enumerate([('1043', 'Linh N.', '2 × Pad thai, Iced tea', 'Preparing', 'amber', '11:05'), ('1044', 'Marco R.', 'Spring rolls', 'New', 'blue', '11:12'), ('1045', 'Aiko T.', 'Green curry, Rice', 'Ready', 'green', '11:14')]):
    y = ty0 + 70 + i * 36
    T(b, MX + 20, y + 6, n, 12.5, 700, '#0F172A'); T(b, MX + 90, y + 6, cu, 12.5, 500, '#0F172A'); T(b, MX + 270, y + 6, it, 12.5, 500, '#334155'); chip(b, MX + 490, y + 4, st, tone, 84); T(b, MX + 630, y + 6, due, 12.5, 600, '#0F172A')
    btn(b, MX + 740, y + 1, 96, 'Accept' if i == 1 else 'Details', 'primary' if i == 1 else 'secondary', 28)
hotspot(b, MX + 740 + 80, ty0 + 70 + 36 + 15)
for (x, y, n) in [(FX + 14, TY + 8, 1), (FX + 840, TY + 28, 2), (SX_ + SW_ - 24, SY_ + 38, 3), (MX + MW - 6, MY + 12, 4), (MX + kw - 8, MY + 52, 5), (MX + 30 + 4 * ((cwid - 60) / 9) + 20, MY + 200, 6), (lx + 6, MY + 198, 7), (MX + 2, ty0 + 2, 8), (MX + 740 + 96, ty0 + 70 + 36 + 2, 9)]:
    callout(b, x, y, n)
notes(b, 100, 990, 1320, [
 (1, 'Brand and place', 'The console name tells which restaurant is open.'), (2, 'Search', 'One box for orders, dishes and customers.'), (3, 'Current section', 'The active item is tinted blue and bold.'),
 (4, 'Pause orders', 'Rose outline: it has a cost. Asks for confirmation.'), (5, 'Key figures', 'Value, then change since yesterday as a chip.'), (6, 'Peak hour', 'The busiest bar is blue, the rest grey.'),
 (7, 'Needs attention', 'Only problems, each with a short chip, newest first.'), (8, 'Live table', 'Status as a chip, sorted by due time.'), (9, 'Row action', 'The next step is primary: Accept for a new order.')], cols=3, gap=6)
print(save6(b))
