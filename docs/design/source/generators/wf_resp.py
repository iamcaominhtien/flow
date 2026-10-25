from wflib import *
W, H = 1700, 1110
b = Board('Wireframe_Responsive', 'Responsive wireframe: one page, three widths', W, H,
  'The same menu page at desktop, tablet and phone width. Columns drop from three to two to one, the filters move out of the way, and the links fold into a menu.')
def page(x, y, w, h, cols, nav, filters):
    R(b, x, y, w, h, '#F8FAFC', '#0F172A', 14, 3)
    R(b, x + 3, y + 3, w - 6, 52, '#fff', G3, 0, 1.5)
    R(b, x + 16, y + 15, 24, 24, BLUE, BLUE, 7, 0); T(b, x + 48, y + 17, 'Pad Thai House', 14, 800, '#0F172A')
    if nav == 'links':
        for i, t in enumerate(['Menu', 'Reviews', 'Contact']): T(b, x + w - 340 + i * 76, y + 19, t, 12.5, 700 if i == 0 else 500, BLUE if i == 0 else '#334155')
        btn(b, x + w - 110, y + 12, 94, 'Order', 'primary', 30)
    else:
        for i in range(3): R(b, x + w - 44, y + 17 + i * 8, 24, 3, '#334155', '#334155', 2, 0)
    cx0, cy0 = x + 20, y + 74
    inner = w - 40
    img(b, cx0, cy0, inner, 110 if cols > 1 else 90, 12); T(b, cx0 + 16, cy0 + 20, 'Fresh Thai, 25 minutes', 18 if cols > 1 else 14, 800, '#fff' if False else '#0F172A', w=inner - 32)
    cy1 = cy0 + (130 if cols > 1 else 110)
    gx = cx0
    if filters == 'side':
        R(b, gx, cy1, 150, 300, '#fff', G3, 10); T(b, gx + 14, cy1 + 12, 'Filters', 12.5, 800, '#0F172A')
        for i, t in enumerate(['Vegan', 'Spicy', 'Under $10', 'Gluten free']):
            R(b, gx + 14, cy1 + 44 + i * 36, 16, 16, '#fff', G4, 4, 1.5); T(b, gx + 40, cy1 + 44 + i * 36, t, 12, 500, '#334155')
        gx += 166; inner -= 166
    else:
        R(b, gx, cy1, 100, 34, '#fff', G4, 17); b.raw(icon_svg('pin', gx + 12, cy1 + 8, 18, '#334155')); T(b, gx + 38, cy1 + 9, 'Filters', 12, 700, '#334155')
        cy1 += 48
    gap = 14
    cw = (inner - (cols - 1) * gap) / cols
    n = cols * 2 if cols > 1 else 3
    for k in range(n):
        r_, c_ = divmod(k, cols)
        x_, y_ = gx + c_ * (cw + gap), cy1 + r_ * (190 if cols > 1 else 142)
        if y_ + (176 if cols > 1 else 130) > y + h - 20: break
        ch = 176 if cols > 1 else 130
        R(b, x_, y_, cw, ch, '#fff', G3, 12)
        if cols > 1:
            img(b, x_ + 8, y_ + 8, cw - 16, 82, 8); bar(b, x_ + 12, y_ + 104, cw * 0.6, 8, G4); bar(b, x_ + 12, y_ + 122, cw * 0.4, 6); chip(b, x_ + 12, y_ + 142, '$9.50', 'blue'); btn(b, x_ + cw - 60, y_ + 140, 50, '+', 'primary', 26)
        else:
            img(b, x_ + 8, y_ + 8, 80, ch - 16, 8); bar(b, x_ + 100, y_ + 20, cw - 140, 8, G4); bar(b, x_ + 100, y_ + 38, cw * 0.4, 6); chip(b, x_ + 100, y_ + 62, '$9.50', 'blue'); btn(b, x_ + cw - 54, y_ + 90, 44, '+', 'primary', 28)
page(80, 250, 760, 680, 3, 'links', 'side')
page(880, 250, 470, 680, 2, 'menu', 'chip')
page(1390, 250, 230, 680, 1, 'menu', 'chip')
for x, w, t, s in [(80, 760, 'Desktop', '1024 px and up'), (880, 470, 'Tablet', '640 to 1023 px'), (1390, 230, 'Phone', 'under 640 px')]:
    T(b, x, 190, t, 17, 800, '#0F172A', w=w, center=True); T(b, x, 214, s, 12, 500, '#64748B', w=w, center=True)
notes(b, 80, 980, 1540, [(1, 'Columns', 'Three, two, one. The card shape changes from tall to wide at one column.'), (2, 'Filters', 'A side panel on desktop, a button that opens a sheet below that.'), (3, 'Navigation', 'Links on desktop, one menu button below 1024 px.')], cols=3, gap=0)
callout(b, 80 + 36, 250 + 100, 1) if False else None
callout(b, 80 + 118, 250 + 280, 2); callout(b, 80 + 406, 250 + 14, 3); callout(b, 1390 + 215, 250 + 36, 3); callout(b, 880 + 22, 250 + 252, 1); callout(b, 1390 + 20, 482, 1)
print(save6(b))
