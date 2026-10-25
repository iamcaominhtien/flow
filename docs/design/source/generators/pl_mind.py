from pllib import *
import html as _h
TONES['rose'] = ('#FDE4E4', '#F9C2C0')
W, H = 2000, 1100
b = Board('Planning_Mind', 'Mind map: launching the delivery app', W, H,
  'One topic in the middle, one colour per area of work, a few short ideas on each branch. Read it in any order. A mind map has no sequence, so nothing animates.')
cx, cy = 1000, 610
BR = [('Product', 'Idea', '#1D4ED8', 'blue', 1, -1, [('Menu and photos', 'store'), ('Checkout flow', 'cart'), ('Order tracking', 'pin'), ('Reviews', 'star')]),
      ('Engineering', 'Server', '#5B4BD6', 'violet', 1, 0, [('Backend API', 'doc'), ('Mobile apps', 'phone'), ('Payments', 'card'), ('Monitoring', 'check')]),
      ('Marketing', 'Flag', '#D97706', 'amber', 1, 1, [('Launch offer', 'star'), ('Restaurant sign-ups', 'store'), ('Social media', 'bell'), ('Press kit', 'doc')]),
      ('Operations', 'Courier', '#0F766E', 'teal', -1, -1, [('Courier onboarding', 'bike'), ('Support desk', 'user'), ('Restaurant onboarding', 'store'), ('Service areas', 'pin')]),
      ('Money and law', 'Money', '#15803D', 'green', -1, 0, [('Payment licence', 'card'), ('Terms and privacy', 'doc'), ('Budget', 'clock'), ('Insurance', 'check')]),
      ('People', 'Team', '#B42318', 'rose', -1, 1, [('Hire a QA engineer', 'user'), ('Train couriers', 'bike'), ('Team rituals', 'clock'), ('Handbook', 'doc')])]
def curve(x0, y0, x1, y1, col, sw):
    mx = (x0 + x1) / 2
    lx, ty = min(x0, x1) - 10, min(y0, y1) - 10
    b.raw(f'<svg width="{abs(x1-x0)+20}" height="{abs(y1-y0)+20}" style="position:absolute;left:{lx}px;top:{ty}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linecap:round"><path d="M {x0-lx} {y0-ty} C {mx-lx} {y0-ty}, {mx-lx} {y1-ty}, {x1-lx} {y1-ty}"/></svg>')
BW, BH, LW, LH, DX = 260, 74, 236, 44, 470
geo = []
for name, ic, col, tone, side, row, leaves in BR:
    bx, by = cx + side * DX, cy + row * 300
    curve(cx + side * 180, cy, bx - side * BW / 2, by, col, 8)
    n = len(leaves)
    for i, (lf, lic) in enumerate(leaves):
        ly = by + (i - (n - 1) / 2) * 58
        lx0 = bx + side * BW / 2
        lx1 = lx0 + side * 92
        curve(lx0, by, lx1, ly, col, 4)
    geo.append((name, ic, col, tone, side, bx, by, leaves))
# centre
bg, pill = TONES['amber']
b.raw(f'<div style="position:absolute;left:{cx-180}px;top:{cy-120}px;width:360px;height:240px;box-sizing:border-box;border:3px solid #0F172A;border-radius:24px;background:{bg}">{detailicon("Launch", 104, 128, 14)}'
      f'<div style="position:absolute;left:0;right:0;top:140px;display:flex;justify-content:center"><div style="padding:6px 20px;border:3px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 4px 0 #0F172A;font-size:20px;font-weight:800;line-height:24px">Launch the delivery app</div></div>'
      f'<div style="position:absolute;left:0;right:0;top:196px;text-align:center;font-size:13px;color:#475569">Goal: first orders in May</div></div>')
for name, ic, col, tone, side, bx, by, leaves in geo:
    bgc, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{bx-BW/2}px;top:{by-BH/2}px;width:{BW}px;height:{BH}px;box-sizing:border-box;border:3px solid #0F172A;border-radius:22px;background:{col};box-shadow:0 4px 0 #0F172A">'
          f'<div style="position:absolute;left:8px;top:{(BH-6-56)/2}px;width:56px;height:56px;border-radius:999px;background:#fff;border:2px solid #0F172A;box-sizing:border-box">{detailicon(ic, 44, 4, 4)}</div>'
          f'<div style="position:absolute;left:76px;right:12px;top:0;height:{BH-6}px;display:flex;align-items:center;font-size:18px;font-weight:800;color:#fff;line-height:22px">{name}</div></div>')
    n = len(leaves)
    for i, (lf, lic) in enumerate(leaves):
        ly = by + (i - (n - 1) / 2) * 58
        lx1 = bx + side * (BW / 2 + 92)
        left = lx1 if side > 0 else lx1 - LW
        b.raw(f'<div style="position:absolute;left:{left}px;top:{ly-LH/2}px;width:{LW}px;height:{LH}px;box-sizing:border-box;border:2px solid {col};border-left:8px solid {col};border-radius:12px;background:#fff;display:flex;align-items:center;gap:10px;padding:0 12px;font-size:14px;font-weight:600">'
              + icon_svg(lic, 0, 0, 18, col).replace('position:absolute;left:0px;top:0px', 'flex:none') + f'{lf}</div>')
print(save4(b))
