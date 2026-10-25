from pllib import *
def build(style):
    ill = style == 'detail'
    cw, chh = (232, 110) if ill else (210, 78)
    ys = [290, 560, 830] if ill else [280, 520, 760]
    W, H = 1980, ys[2] + chh // 2 + 150
    b = Board('Planning_Org' + ('_Illustrated' if ill else ''), 'Org chart: the delivery team' + (', illustrated' if ill else ', plain'), W, H,
      'Lines run from a manager down to the people who report to them. A dashed line is a working relationship without reporting. A dashed card is an open role.')
    def person(cx, cy, name, role, tone, initials='', vacant=False):
        if ill:
            b.card(cx, cy, name, role, 'User', TONES[tone], w=cw, h=chh, style='detail')
            if vacant: b.raw(f'<div style="position:absolute;left:{cx-cw/2}px;top:{cy-chh/2}px;width:{cw}px;height:{chh}px;box-sizing:border-box;border:3px dashed #64748B;border-radius:12px;background:rgba(248,250,252,.55)"></div>')
        else:
            bg, pill = TONES[tone]
            bd = '2px dashed #64748B' if vacant else '2px solid #0F172A'
            b.raw(f'<div style="position:absolute;left:{cx-cw/2}px;top:{cy-chh/2}px;width:{cw}px;height:{chh}px;box-sizing:border-box;border:{bd};border-radius:12px;background:{"#F8FAFC" if vacant else bg}">'
                  f'<div style="position:absolute;left:12px;top:{chh/2-20}px;width:40px;height:40px;border-radius:999px;background:{pill};border:2px solid #0F172A;box-sizing:border-box;font:800 14px/36px Inter,sans-serif;text-align:center">{initials}</div>'
                  f'<div style="position:absolute;left:62px;top:{chh/2-22}px;font-size:14px;font-weight:800;line-height:20px;white-space:nowrap">{name}</div><div style="position:absolute;left:62px;top:{chh/2-1}px;font-size:12px;line-height:18px;color:#475569;white-space:nowrap">{role}</div></div>')
    ceo = (1030, ys[0]); leads = [(345, 'Minh Tran', 'Head of Product', 'blue', 'MT'), (1030, 'Sam Ortiz', 'Head of Engineering', 'green', 'SO'), (1675, 'Lena Park', 'Head of Operations', 'teal', 'LP')]
    kids = [[(220, 'Noah Kim', 'Product analyst', 'blue', 'NK', False), (470, 'Ava Lopez', 'Designer', 'blue', 'AL', False)],
            [(780, 'Lia Chen', 'Mobile developer', 'green', 'LC', False), (1030, 'Kai Novak', 'Backend developer', 'green', 'KN', False), (1280, 'QA engineer', 'Open role', 'gray', '?', True)],
            [(1550, 'Joy Adams', 'Support lead', 'teal', 'JA', False), (1800, 'Max Rossi', 'Courier operations', 'teal', 'MR', False)]]
    person(ceo[0], ceo[1], 'Dana Reed', 'CEO', 'violet', 'DR')
    for (x, n, r, t, i) in leads: person(x, ys[1], n, r, t, i)
    for k in kids:
        for (x, n, r, t, i, v) in k: person(x, ys[2], n, r, t, i, v)
    top, bot = chh / 2, chh / 2
    # bus lines
    mid1 = (ys[0] + ys[1]) / 2 + 4
    line(b, [(ceo[0], ys[0] + bot), (ceo[0], mid1)])
    line(b, [(leads[0][0], mid1), (leads[2][0], mid1)])
    for (x, *_) in leads: line(b, [(x, mid1), (x, ys[1] - top)])
    mid2 = (ys[1] + ys[2]) / 2 + 4
    for (lx, *_), k in zip(leads, kids):
        line(b, [(lx, ys[1] + bot), (lx, mid2)])
        line(b, [(min(c[0] for c in k), mid2), (max(c[0] for c in k), mid2)])
        for c in k: line(b, [(c[0], mid2), (c[0], ys[2] - top)])
    # dotted working line Designer -> Mobile developer
    line(b, [(470 + cw / 2, ys[2]), (780 - cw / 2, ys[2])], col='#475569', dash='6 5')
    b.label((470 + cw / 2 + 780 - cw / 2) / 2, ys[2] - 16, 'works with', 'back')
    # legend
    ly = H - 80
    b.raw(f'<svg width="40" height="10" style="position:absolute;left:64px;top:{ly+4}px;stroke:#0F172A;stroke-width:2"><path d="M0 5H40"/></svg>'); b.text(112, ly - 2, 'Reports to', size=12, color='#334155')
    b.raw(f'<svg width="40" height="10" style="position:absolute;left:230px;top:{ly+4}px;stroke:#475569;stroke-width:2;stroke-dasharray:6 5"><path d="M0 5H40"/></svg>'); b.text(278, ly - 2, 'Works with, no reporting line', size=12, color='#334155')
    b.raw(f'<div style="position:absolute;left:520px;top:{ly-2}px;width:34px;height:20px;box-sizing:border-box;border:2px dashed #64748B;border-radius:6px"></div>'); b.text(566, ly - 2, 'Open role', size=12, color='#334155')
    return b
for st in ('plain', 'detail'):
    print(save4(build(st)))
