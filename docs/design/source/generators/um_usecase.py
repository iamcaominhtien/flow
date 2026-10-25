from umllib import *
def build(style):
    ill = style == 'detail'
    W, H = 1960, 1130
    b = Board('UML_UseCase' + ('_Illustrated' if ill else ''), 'Use case diagram: the delivery app' + (', illustrated' if ill else ', plain'), W, H,
      'Who uses the system and what for. Actors stand outside the frame, use cases inside it. A solid line means the actor takes part. A dashed arrow says one use case includes or extends another.')
    SX0, SX1, SY0, SY1 = 600, 1520, 190, 1000
    b.rect(SX0, SY0, SX1 - SX0, SY1 - SY0, '#fff', '#0F172A', 14, dashed=False)
    b.text(SX0 + 20, SY0 + 14, 'Delivery app', size=16, color='#0F172A', weight=800)
    def actor(cx, cy, name, ic, tone, ext=False):
        if ill:
            bg, pill = TONES[tone]
            b.raw(f'<div style="position:absolute;left:{cx-90}px;top:{cy-70}px;width:180px;height:140px;box-sizing:border-box;border:2px solid #0F172A;border-radius:16px;background:{bg}">{detailicon(ic, 72, 54, 10)}<div style="position:absolute;left:0;right:0;top:92px;display:flex;justify-content:center"><div style="padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:13px;font-weight:800;white-space:nowrap">{name}</div></div></div>')
            return Node(cx, cy, 180, 140)
        b.raw(f'<svg width="60" height="86" viewBox="0 0 60 86" style="position:absolute;left:{cx-30}px;top:{cy-55}px;fill:none;stroke:#0F172A;stroke-width:2.5;stroke-linecap:round"><circle cx="30" cy="14" r="11" fill="{TONES[tone][1]}"/><path d="M30 25V56M8 36H52M30 56L12 80M30 56L48 80"/></svg>')
        b.text(cx - 80, cy + 34, name + ('<br><span style="font-weight:500;color:#475569;font-size:11px">&laquo;external system&raquo;</span>' if ext else ''), size=13, color='#0F172A', weight=800, w=160, center=True)
        return Node(cx, cy, 60, 86)
    def uc(cx, cy, name, tone):
        bg, pill = TONES[tone]
        b.raw(f'<div style="position:absolute;left:{cx-120}px;top:{cy-32}px;width:240px;height:64px;box-sizing:border-box;border:2px solid #0F172A;border-radius:50%;background:{bg};display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;text-align:center;padding:0 24px">{name}</div>')
        return Node(cx, cy, 240, 64)
    A, B_ = 800, 1320
    ys = [300, 440, 580, 720, 860]
    br = uc(A, ys[0], 'Browse menus', 'blue'); tr = uc(B_, ys[0], 'Track the order', 'blue')
    po = uc(A, ys[1], 'Place an order', 'blue'); pr = uc(B_, ys[1], 'Apply a promo code', 'blue')
    ra = uc(A, ys[2], 'Rate the meal', 'blue'); pa = uc(B_, ys[2], 'Pay for the order', 'amber')
    ac = uc(A, ys[3], 'Accept an order', 'green'); pf = uc(B_, ys[3], 'Prepare the food', 'green')
    de = uc(A, ys[4], 'Deliver the order', 'teal'); sl = uc(B_, ys[4], 'Share live location', 'teal')
    cu = actor(250, ys[1], 'Customer', 'User', 'blue')
    rs = actor(250, ys[3], 'Restaurant', 'Restaurant', 'green')
    co = actor(250, ys[4] + 40, 'Courier', 'Courier', 'teal')
    pp = actor(1780, ys[2], 'Payment provider', 'Card', 'amber', ext=True)
    cr = cu.cx + (90 if ill else 30)
    for t in (br, po, ra, tr): uline(b, [(cr, cu.cy), (t.l()[0], t.cy)])
    uline(b, [(rs.cx + (90 if ill else 30), rs.cy), ac.l()])
    uline(b, [(co.cx + (90 if ill else 30), co.cy), (de.l()[0], de.cy)])
    uline(b, [(pp.cx - (90 if ill else 30), pp.cy), pa.r()])
    def dep(a, c, label, lp):
        link(b, [a, c], None, 'open', dashed=True, label=label, lpos=lp)
    dep(pr.l(), po.r(), '«extend»', ((pr.l()[0] + po.r()[0]) / 2, ys[1]))
    link(b, [(po.r()[0] - 10, po.cy + 20), (pa.l()[0] + 10, pa.cy - 20)], None, 'open', dashed=True, label='«include»', lpos=((po.r()[0] + pa.l()[0]) / 2, (po.cy + pa.cy) / 2))
    dep(ac.r(), pf.l(), '«include»', ((ac.r()[0] + pf.l()[0]) / 2, ys[3]))
    dep(de.r(), sl.l(), '«include»', ((de.r()[0] + sl.l()[0]) / 2, ys[4]))
    b.raw(f'<div style="position:absolute;left:64px;top:{H-90}px;width:1500px;font-size:12.5px;line-height:19px;color:#475569"><b style="color:#0F172A">include:</b> the base use case always uses the other one. <b style="color:#0F172A">extend:</b> the extension may add to the base in some cases. The arrow points at the use case being included or extended.</div>')
    return b
for st in ('plain', 'detail'):
    print(save5(build(st)))
