from pllib import *
# ---------------- Kanban ----------------
W, H = 1640, 980
b = Board('Planning_Kanban', 'Kanban: the delivery app sprint', W, H,
  'Work moves left to right through columns. A card is one piece of work, the tag says what kind, the circle says who. A column with a limit shows how full it is.')
cols = [('Backlog', None, 'gray', [('Courier tips', 'Feature', 'J'), ('Refund screen', 'Feature', 'A'), ('Slow map on old phones', 'Bug', 'K'), ('Update libraries', 'Chore', 'L')]),
        ('In progress', 3, 'blue', [('Live order tracking', 'Feature', 'K'), ('Fix double charge', 'Bug', 'J'), ('Restaurant menu editor', 'Feature', 'A')]),
        ('In review', None, 'amber', [('Push notifications', 'Feature', 'L'), ('Crash on checkout', 'Bug', 'M')]),
        ('Done', None, 'green', [('Sign-in with phone', 'Feature', 'A'), ('Order history', 'Feature', 'K'), ('Rename API fields', 'Chore', 'L')])]
TAG = {'Feature': ('#DCEEFB', '#1E5AA8'), 'Bug': ('#FDE4E4', '#B42318'), 'Chore': ('#E2E8F0', '#334155')}
AV = {'J': 'blue', 'A': 'violet', 'K': 'green', 'L': 'teal', 'M': 'amber'}
CWID, GAP, X0, Y0 = 360, 30, 64, 170
for i, (n, lim, tone, cards) in enumerate(cols):
    x = X0 + i * (CWID + GAP)
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{x}px;top:{Y0}px;width:{CWID}px;height:740px;box-sizing:border-box;background:{bg};opacity:.55;border-radius:18px"></div>')
    cnt = f'{len(cards)}' + (f' / {lim}' if lim else '')
    full = lim and len(cards) >= lim
    b.raw(f'<div style="position:absolute;left:{x+18}px;top:{Y0+16}px;display:flex;align-items:center;gap:10px"><span style="padding:3px 14px;border:2px solid #0F172A;border-radius:999px;background:{pill};font-size:14px;font-weight:800">{n}</span><span style="padding:0 10px;height:24px;border-radius:999px;background:{"#D92D20" if full else "#0F172A"};color:#fff;font:700 12px/24px Inter,sans-serif">{cnt}</span></div>')
    for j, (t, tag, who) in enumerate(cards):
        cy = Y0 + 110 + j * 128
        tb, tf = TAG[tag]
        done = n == 'Done'
        b.raw(f'<div style="position:absolute;left:{x+18}px;top:{cy-50}px;width:{CWID-36}px;height:100px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:#fff;{"opacity:.8;" if done else ""}"><div style="position:absolute;left:14px;top:12px;right:14px;font-size:14px;font-weight:700;line-height:20px;{"text-decoration:line-through;color:#475569;" if done else ""}">{t}</div>'
              f'<div style="position:absolute;left:14px;bottom:12px;padding:0 10px;height:22px;border-radius:999px;background:{tb};color:{tf};font:700 11.5px/22px Inter,sans-serif">{tag}</div></div>')
        avatar(b, x + 18 + CWID - 36 - 14 - 28, cy + 50 - 12 - 28, who, AV[who], 28)
print(save4(b))
# ---------------- Roadmap ----------------
W, H = 1760, 1040
b = Board('Planning_Roadmap', 'Roadmap: now, next, later', W, H,
  'Themes in rows, time in columns. Solid cards are committed, dashed cards are ideas under study. The blue arrow marks a dependency that decides the order.')
LWD, X0, CWID, GAP = 220, 64, 440, 24
heads = [('Now', 'March to April', 'green'), ('Next', 'May to June', 'amber'), ('Later', 'Second half', 'gray')]
for i, (n, sub, tone) in enumerate(heads):
    x = X0 + LWD + i * (CWID + GAP)
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{x}px;top:170px;width:{CWID}px;height:64px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{pill};padding:10px 18px"><div style="font-size:18px;font-weight:800;line-height:22px">{n}</div><div style="font-size:12px;color:#334155">{sub}</div></div>')
lanes = [('Ordering', 'Cart', 'blue', [[('Live order tracking', 1)], [('Scheduled orders', 1)], [('Group orders', 0)]]),
         ('Delivery', 'Courier', 'teal', [[('Smarter courier matching', 1)], [('Courier tips', 1)], [('Drone pilot', 0)]]),
         ('Growth', 'Bell', 'violet', [[('Referral credits', 1)], [('Loyalty points', 0)], [('New cities', 0)]])]
LY0, LP = 262, 224
pos = {}
for r, (n, ic, tone, cells) in enumerate(lanes):
    y = LY0 + r * LP
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{y}px;width:{LWD-16}px;height:{LP-24}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:16px;background:{bg}">{detailicon(ic, 72, (LWD-16-72)/2, 18)}<div style="position:absolute;left:0;right:0;top:100px;display:flex;justify-content:center"><div style="padding:3px 14px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:14px;font-weight:800">{n}</div></div></div>')
    b.raw(f'<div style="position:absolute;left:{X0+LWD}px;top:{y}px;width:{3*CWID+2*GAP}px;height:{LP-24}px;box-sizing:border-box;background:{bg};opacity:.4;border-radius:16px"></div>')
    for c, items in enumerate(cells):
        for (t, committed) in items:
            x = X0 + LWD + c * (CWID + GAP) + 20
            bd = '2px solid #0F172A' if committed else '2px dashed #64748B'
            b.raw(f'<div style="position:absolute;left:{x}px;top:{y+28}px;width:{CWID-40}px;height:{LP-24-56}px;box-sizing:border-box;border:{bd};border-radius:14px;background:#fff;padding:14px 18px"><div style="font-size:15px;font-weight:800;line-height:20px">{t}</div><div style="margin-top:8px;display:inline-block;padding:0 10px;height:22px;border-radius:999px;background:{"#DCF5E1" if committed else "#E2E8F0"};color:{"#15803D" if committed else "#475569"};font:700 11.5px/22px Inter,sans-serif">{"Committed" if committed else "Exploring"}</div></div>')
            pos[t] = (x, y + 28, CWID - 40, LP - 24 - 56)
# dependency: live tracking -> courier tips
a, c = pos['Live order tracking'], pos['Courier tips']
x0_, y0_ = a[0] + a[2], a[1] + a[3] / 2
x1_, y1_ = c[0] + c[2] / 2, c[1]
b.arrow([(a[0] + a[2], a[1] + a[3] / 2), (a[0] + a[2] + 12, a[1] + a[3] / 2), (a[0] + a[2] + 12, c[1] - 16), (c[0] + c[2] / 2, c[1] - 16), (c[0] + c[2] / 2, c[1])], 'main', 'needs live tracking', (c[0] + c[2] / 2 - 120, c[1] - 16)) if False else None
b.arrow([(a[0] + a[2], a[1] + a[3] / 2), (a[0] + a[2] + 12, a[1] + a[3] / 2), (a[0] + a[2] + 12, y1_ - 400 + 400), ], 'next') if False else None
# simple L route: from tracking right edge across to Courier tips top
b.arrow([(a[0] + a[2], a[1] + 30), (a[0] + a[2] + 12, a[1] + 30), (a[0] + a[2] + 12, c[1] - 14), (c[0] + 60, c[1] - 14), (c[0] + 60, c[1])], 'main')
b.text(64, H - 70, 'The blue arrow means Courier tips cannot start before Live order tracking is done. Solid cards are committed, dashed cards are still being studied.', size=13, color='#475569', w=1500)
print(save4(b))
