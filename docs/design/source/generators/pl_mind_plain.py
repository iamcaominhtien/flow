from pllib import *
W, H = 1700, 1060
b = Board('Planning_Mind_Plain', 'Mind map: plain', W, H,
  'One topic in the middle, one branch per area of work, one short phrase per leaf. Colour follows the branch. A mind map has no order and no animation.')
cx, cy = 850, 560
b.raw(f'<div style="position:absolute;left:{cx-160}px;top:{cy-46}px;width:320px;height:92px;box-sizing:border-box;border:2px solid #0F172A;border-radius:999px;background:#0F172A;color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:22px;font-weight:800;line-height:26px;padding:0 24px">Launch the delivery app</div>')
BR = [('Product', 'doc', '#1D4ED8', 'blue', 1, -1, ['Menu and photos', 'Checkout flow', 'Order tracking']),
      ('Engineering', 'phone', '#5B4BD6', 'violet', 1, 0, ['Backend API', 'Mobile apps', 'Payments', 'Monitoring']),
      ('Marketing', 'bell', '#D97706', 'amber', 1, 1, ['Launch offer', 'Restaurant sign-ups', 'Social media']),
      ('Operations', 'bike', '#0F766E', 'teal', -1, -1, ['Courier onboarding', 'Support desk', 'Restaurant onboarding']),
      ('Money and law', 'card', '#15803D', 'green', -1, 1, ['Payment licence', 'Terms and privacy', 'Budget'])]
def curve(x0, y0, x1, y1, col, sw):
    mx = (x0 + x1) / 2
    lx, ty = min(x0, x1) - 10, min(y0, y1) - 10
    b.raw(f'<svg width="{abs(x1-x0)+20}" height="{abs(y1-y0)+20}" style="position:absolute;left:{lx}px;top:{ty}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linecap:round"><path d="M {x0-lx} {y0-ty} C {mx-lx} {y0-ty}, {mx-lx} {y1-ty}, {x1-lx} {y1-ty}"/></svg>')
for name, ic, col, tone, side, row, leaves in BR:
    bx = cx + side * 380
    by = cy + row * 250
    bw = 210
    curve(cx + side * 160, cy, bx - side * bw / 2, by, col, 5)
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{bx-bw/2}px;top:{by-26}px;width:{bw}px;height:52px;box-sizing:border-box;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;display:flex;align-items:center;justify-content:center;gap:8px;font-size:15px;font-weight:800">{icon_svg(ic, 0, 0, 20, "#0F172A").replace("position:absolute;left:0px;top:0px", "flex:none")}{name}</div>')
    n = len(leaves)
    for i, lf in enumerate(leaves):
        ly = by + (i - (n - 1) / 2) * 52
        lx0 = bx + side * bw / 2
        lx1 = lx0 + side * 70
        curve(lx0, by, lx1, ly, col, 3)
        w = 230
        left = lx1 if side > 0 else lx1 - w
        b.raw(f'<div style="position:absolute;left:{left}px;top:{ly-17}px;width:{w}px;height:34px;box-sizing:border-box;border-bottom:3px solid {col};font-size:14px;font-weight:600;line-height:30px;{"text-align:right;" if side < 0 else ""}padding:0 8px">{lf}</div>')
print(save4(b))
