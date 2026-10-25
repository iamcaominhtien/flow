from pllib import *
W = 1700
LW, CW, X0 = 300, 88, 64          # label column, week width, left margin
GX = X0 + LW                       # grid left
NW = 14
RH = 52
HY = 190                           # header top
rows = [('P', 'Discover', None), ('T', 'Research', ('done', 1, 2, 'M', 'violet')), ('T', 'Write the spec', ('done', 3, 3, 'A', 'blue')), ('MS', 'Spec approved', 3.0),
        ('P', 'Build', None), ('T', 'Design', ('done', 4, 5, 'S', 'amber')), ('T', 'Mobile app', ('doing', 6, 10, 'L', 'teal', 0.3)), ('T', 'Payments', ('plan', 8, 10, 'J', 'blue')), ('T', 'Backend API', ('doing', 4, 9, 'K', 'green', 0.7)),
        ('P', 'Launch', None), ('T', 'Beta test', ('plan', 11, 12, 'M', 'violet')), ('T', 'Fix bugs', ('plan', 13, 14, 'K', 'green')), ('MS', 'Launch', 14.0)]
H = HY + 70 + len(rows) * RH + 120
b = Board('Planning_Gantt', 'Gantt: launching the delivery app', W, H,
  'Time runs left to right, one row per task. Bar colour is status, the blue chain is the critical path, the red line is today. Diamonds are milestones.')
gw = NW * CW
# header
b.raw(f'<div style="position:absolute;left:{GX}px;top:{HY}px;width:{gw}px;height:62px;box-sizing:border-box;border:1.5px solid #CBD5E1;border-radius:10px;background:#fff" data-lint="box"></div>')
for i, m in enumerate([('March', 0, 4), ('April', 4, 8), ('May', 8, 12), ('June', 12, 14)]):
    b.raw(f'<div style="position:absolute;left:{GX+m[1]*CW}px;top:{HY}px;width:{(m[2]-m[1])*CW}px;height:30px;box-sizing:border-box;border-right:1.5px solid #CBD5E1;font:800 13px/30px Inter,sans-serif;padding-left:12px">{m[0]}</div>')
for i in range(NW):
    b.raw(f'<div style="position:absolute;left:{GX+i*CW}px;top:{HY+30}px;width:{CW}px;height:32px;box-sizing:border-box;border-top:1.5px solid #E2E8F0;{"border-left:1.5px solid #E2E8F0;" if i else ""}font:600 12px/30px Inter,sans-serif;color:#475569;text-align:center">W{i+1}</div>')
gy0 = HY + 70
for i in range(NW + 1):
    b.raw(f'<div style="position:absolute;left:{GX+i*CW}px;top:{gy0}px;height:{len(rows)*RH}px;border-left:1px solid #E2E8F0"></div>')
pos = {}
for r, (kind, name, spec) in enumerate(rows):
    y = gy0 + r * RH
    cy = y + RH / 2
    if kind == 'P':
        b.raw(f'<div style="position:absolute;left:{X0}px;top:{y+6}px;width:{LW+gw}px;height:{RH-12}px;background:#F1F5F9;border-radius:8px"></div>')
        b.text(X0 + 14, cy - 11, name, size=14, color='#0F172A', weight=800)
    elif kind == 'T':
        st, a, c, ini, tone = spec[:5]
        prog = spec[5] if len(spec) > 5 else (1 if st == 'done' else 0)
        avatar(b, X0 + 14, cy - 13, ini, tone)
        b.text(X0 + 50, cy - 10, name, size=13, color='#0F172A', weight=600)
        col, soft = STAT[st]
        x0, x1 = GX + (a - 1) * CW + 8, GX + c * CW - 8
        b.raw(f'<div style="position:absolute;left:{x0}px;top:{cy-13}px;width:{x1-x0}px;height:26px;box-sizing:border-box;border:2px solid {col};border-radius:8px;background:{soft};overflow:hidden"><div style="width:{prog*100:g}%;height:100%;background:{col};opacity:.85"></div></div>')
        if st == 'done':
            b.raw(f'<svg width="14" height="14" viewBox="0 0 14 14" style="position:absolute;left:{x0+8}px;top:{cy-7}px;fill:none;stroke:#fff;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round"><path d="M2 7.5L5.5 11L12 3.5"/></svg>')
        pos[name] = (x0, x1, cy)
    else:
        b.raw(f'<svg width="22" height="22" viewBox="0 0 22 22" style="position:absolute;left:{GX+(spec)*CW-11}px;top:{cy-11}px"><path d="M11 1L21 11L11 21L1 11Z" fill="#F59E3A" stroke="#0F172A" stroke-width="2" stroke-linejoin="round"/></svg>')
        b.text(X0 + 14, cy - 10, name, size=13, color='#0F172A', weight=700)
        pos[name] = (GX + spec * CW - 11, GX + spec * CW + 11, cy)
# dependencies
def dep(a, c, crit=False):
    xa, xb = pos[a][1], pos[c][0]
    ya, yb = pos[a][2], pos[c][2]
    mid = xa + 12
    ms = c in ('Launch',)
    pts = [(xa, ya), (xa + 8, ya), (xa + 8, yb - 12)] if ms else [(xa, ya), (xa + 8, ya), (xa + 8, yb), (xb, yb)]
    col, sw = ('#1D4ED8', 4) if crit else (INK, 1.5)
    last = pts[-1]
    b.mid += 1
    mid_id = f'dc-arrow-head-filled-{b.mid + 7000}'
    hu = 4 if crit else 5
    gap = 8 if crit else 5
    p2 = pts[:-1] + [(last[0], last[1] - gap)] if ms else pts[:-1] + [(last[0] - gap, last[1])]
    xs, ys = [p[0] for p in p2], [p[1] for p in p2]
    pad = 8; ox, oy = min(xs) - pad, min(ys) - pad
    d = 'M ' + ' L '.join(f'{p[0]-ox:g} {p[1]-oy:g}' for p in p2)
    cls = ' class="flow"' if crit else ''
    b.raw(f'<svg width="{max(xs)-ox+pad+10:g}" height="{max(ys)-oy+pad:g}" style="position:absolute;left:{ox:g}px;top:{oy:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round"><defs><marker id="{mid_id}" orient="auto" markerWidth="{hu}" markerHeight="{hu}" refX="{hu/2}" refY="{hu/2}" overflow="visible"><path d="M0 0 L{hu} {hu/2} L0 {hu} Z" fill="{col}" stroke="none" style="stroke:none;fill:{col}"/></marker></defs><path{cls} d="{d}" marker-end="url(#{mid_id})"/></svg>')
for a, c, crit in [('Research', 'Write the spec', True), ('Write the spec', 'Design', True),  ('Design', 'Mobile app', True), ('Write the spec', 'Backend API', False), ('Backend API', 'Beta test', False), ('Payments', 'Beta test', False),
                   ('Mobile app', 'Beta test', True), ('Beta test', 'Fix bugs', True), ('Fix bugs', 'Launch', True)]:
    dep(a, c, crit)
# today
tx = GX + 7.0 * CW
b.raw(f'<div style="position:absolute;left:{tx-1}px;top:{gy0-8}px;height:{len(rows)*RH+16}px;border-left:2px dashed #D92D20"></div>')
b.raw(f'<div style="position:absolute;left:{tx-28}px;top:{gy0+len(rows)*RH+10}px;width:56px;height:22px;border-radius:999px;background:#D92D20;color:#fff;font:800 12px/22px Inter,sans-serif;text-align:center">Today</div>')
# legend
ly = gy0 + len(rows) * RH + 56
items = [('done', 'Done'), ('doing', 'In progress'), ('plan', 'Planned')]
x = X0
for st, t in items:
    col, soft = STAT[st]
    b.raw(f'<div style="position:absolute;left:{x}px;top:{ly}px;width:34px;height:16px;box-sizing:border-box;border:2px solid {col};border-radius:6px;background:{soft}"></div>')
    b.text(x + 44, ly - 2, t, size=12, color='#334155'); x += 44 + 8 * len(t) + 34
b.raw(f'<svg width="34" height="10" viewBox="0 0 34 10" style="position:absolute;left:{x}px;top:{ly+3}px;fill:none;stroke:#1D4ED8;stroke-width:4;stroke-dasharray:8 5"><path d="M0 5H34"/></svg>')
b.text(x + 44, ly - 2, 'Critical path', size=12, color='#334155')
print(save4(b))
