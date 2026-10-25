from fclib import *
import sys
DET = True
STYLE = 'detail'
W, H = 3724, 1540
b = Board('Flowchart_Delivery_Illustrated', 'Complete flowchart: food delivery, illustrated', W, H,
  'The same order as the plain version, drawn with illustrated cards: a name pill, one line of explanation and a large icon from the Icons page. Cards take the colour of their lane, so the owner of a step is clear before reading it.')
X0, X1, top, LH = 64, 3660, 170, 240
TONE = {'C': ('#DCEEFB', '#BFDBFE'), 'A': ('#E6E3FB', '#CFC8F7'), 'P': ('#FFF1DD', '#FFD9A3'), 'R': ('#DCF5E1', '#B5EBC1'), 'K': ('#D3F3EF', '#A8E6DE')}
lanes = [('Customer', '#EFF6FF', '#BFDBFE', '#1D4ED8'), ('App and server', '#F3F1FD', '#D4CEF7', '#5B4BD6'), ('Payment', '#FFF7EA', '#F5DDB4', '#B45309'), ('Restaurant', '#F0FBF2', '#BBE7C4', '#15803D'), ('Courier', '#EEFBF9', '#BDE8E3', '#0F766E')]
for i, (nm, bg, bd, fg) in enumerate(lanes):
    yy = top + i * LH
    b.rect(X0, yy, X1 - X0, LH, bg, bd, 0, False)
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{yy}px;width:44px;height:{LH}px;box-sizing:border-box;background:{fg};display:flex;align-items:center;justify-content:center"><span style="writing-mode:vertical-rl;transform:rotate(180deg);color:#fff;font-size:13px;font-weight:700;letter-spacing:.02em;white-space:nowrap">{nm}</span></div>')
C, A, P, R, K = [top + i * LH + LH // 2 for i in range(5)]
x4, x5, x3, fork, x7, x8, xr, join, x10, x11, x12, x13, x14 = 885, 1206, 613, 1391, 1606, 1872, 1933, 2144, 2359, 2686, 3013, 3263, 3508
def cd(lane, cx, cy, t, d, ic, bars=False): return b.card(cx, cy, t, d, ic, TONE[lane], bars=bars, style=STYLE)
st = b.node('terminator', 180, C, 140, 52, 'Open app', icon='phone')
s1 = b.screen_card(405, C, 'S01', 'Browse', style=STYLE); s2 = b.screen_card(645, C, 'S02', 'Menu', style=STYLE); s3 = b.screen_card(x4, C, 'S03', 'Checkout', style=STYLE)
s4 = b.screen_card(x11, C, 'S04', 'Tracking', style=STYLE); s5 = b.screen_card(x12, C, 'S05', 'Rate order', style=STYLE)
rt = b.node('decision', x13, C, 170, 100, 'Rating below 3?', fs=12)
en = b.node('terminator', x14, C, 150, 52, 'Enjoy meal', icon='star')
co = cd('A', x4, A, 'Create order', 'Save the items and the total', 'Cart')
se = cd('A', x5, A, 'Payment error', 'Ask for another card', 'Warning')
pu = cd('A', x7, A, 'Push message', 'Tell the customer: accepted', 'Bell')
tm = cd('A', x11, A, 'Live tracking', 'Move the courier on the map', 'Region')
cl = cd('A', x12, A, 'Close order', 'Mark the order complete', 'Approved doc')
cn = b.node('connector', x13, A, 38, 38, 'A')
au = cd('P', x4, P, 'Authorize card', 'Check the card, hold the money', 'Card', True)
ap = b.node('decision', x5, P, 150, 100, 'Approved?')
rf = cd('P', x3, P, 'Refund', 'Return the held money', 'Refund', True)
mr = b.node('terminator', 307, P, 160, 52, 'Money returned')
cp = cd('P', x12, P, 'Capture payment', 'Take the held money', 'Money')
ac = b.node('decision', x5, R, 170, 100, 'Accepts order?', fs=12)
ca = cd('R', x3, R, 'Cancel order', 'Tell the customer', 'Error')
pf = cd('R', x7, R, 'Prepare food', 'Cook it and pack it', 'Pot')
rd = cd('R', xr, R, 'Mark ready', 'Wait for the courier', 'Package')
fc = cd('K', x7, K, 'Find courier', 'Ask the nearest free rider', 'Courier')
fd = b.node('decision', x8, K, 130, 90, 'Found?')
pk = cd('K', x10, K, 'Pick up', 'Collect it at the restaurant', 'Restaurant')
dl = cd('K', x11, K, 'Deliver', 'Ride to the door', 'Courier')
cd_ = cd('K', x12, K, 'Confirm', 'Photo at the door', 'Success')
b.bar(fork, R - 55, K + 55); b.bar(join, R - 55, K + 55)
M = 'main'
b.arrow([st.r(), s1.l()], M)
b.arrow([s1.r(), s2.l()], M); b.chip((s1.r()[0] + s2.l()[0]) / 2, C - 24, 'tap shop')
b.arrow([s2.r(), s3.l()], M); b.chip((s2.r()[0] + s3.l()[0]) / 2, C - 24, 'checkout')
b.arrow([s3.b(), co.t()], M); b.arrow([co.b(), au.t()], M); b.arrow([au.r(), ap.l()], M)
b.arrow([ap.b(), ac.t()], M); b.label(x5 + 22, P + 70, 'Yes', 'yes')
b.arrow([ac.r(), (fork - 4, R)], M); b.label((ac.r()[0] + fork) / 2, R - 18, 'Yes', 'yes')
b.arrow([(fork + 4, R), pf.l()], M); b.arrow([(fork + 4, K), fc.l()], M)
b.arrow([pf.r(), rd.l()], M); b.arrow([rd.r(), (join - 4, R)], M)
b.arrow([fc.r(), fd.l()], M)
b.arrow([fd.r(), (join - 4, K)], M); b.label((fd.r()[0] + join) / 2, K - 18, 'Yes', 'yes')
b.arrow([(join + 4, K), pk.l()], M)
b.arrow([pk.r(), dl.l()], M); b.arrow([dl.r(), cd_.l()], M)
b.arrow([cd_.t(), cp.b()], M); b.arrow([cp.t(), cl.b()], M); b.arrow([cl.t(), s5.b()], M)
b.arrow([s5.r(), rt.l()], M)
b.arrow([rt.r(), en.l()], M); b.label((rt.r()[0] + en.l()[0]) / 2, C - 18, 'No', 'no')
b.arrow([ap.t(), se.b()], 'no', 'No', (x5 + 22, P - 72))
b.arrow([se.t(), (x5, C), s3.r()], 'back', 'Edit card', (x5 - 56, C - 16))
b.arrow([ac.l(), ca.r()], 'no', 'No', ((ac.l()[0] + ca.r()[0]) / 2, R - 16))
b.arrow([ca.t(), rf.b()], 'no')
b.arrow([rf.l(), mr.r()])
b.arrow([rt.b(), cn.t()], 'yes', 'Yes', (x13 + 22, C + 78))
b.text(x13 + 34, A - 16, 'Continues in<br><b>Support case</b> flow', 12, '#475569', lh=17)
b.arrow([fd.b(), (x8, K + 95), (x7, K + 95), fc.b()], 'back')
b.chip((x7 + x8) / 2, K + 95, 'wait 30 s', False, 'clock')
b.label(x8 + 22, K + 68, 'No', 'no')
b.arrow([(fork, R - 55), (fork, A), pu.l()], 'data')
b.arrow([pu.r(), tm.l()], 'data')
b.arrow([dl.t(), tm.b()], 'data'); b.arrow([tm.t(), s4.b()], 'data')
b.chip(x11 + 74, P + 6, 'live location', False, 'pin')
ly = top + 5 * LH + 36
b.text(64, ly, '<b>Reading the chart</b>', 13, '#0F172A')
def legend_line(x, role, text):
    col, dash, sw = ROLE[role]
    if role == 'main': st_ = f'<svg width="40" height="8" viewBox="0 0 40 8" style="fill:none;stroke:{col};stroke-width:4;stroke-dasharray:8 5"><path d="M0 4L40 4"/></svg>'
    elif role == 'data': st_ = f'<svg width="40" height="8" viewBox="0 0 40 8" style="fill:none;stroke:{col};stroke-width:2;stroke-dasharray:6 6"><path d="M0 4L40 4"/></svg>'
    else: st_ = f'<span style="width:40px;border-top:2px {"dashed" if dash else "solid"} {col};display:block"></span>'
    b.raw(f'<div style="position:absolute;left:{x}px;top:{ly+30}px;display:flex;align-items:center;gap:10px;font-size:12px;color:#334155;white-space:nowrap">{st_}{text}</div>')
legend_line(64, 'main', 'Main path, animated fast. Splits at the fork and joins again.')
legend_line(520, 'data', 'Data stream, animated slowly: messages and location, not steps.')
legend_line(1010, 'no', 'Failure'); legend_line(1130, 'back', 'Retry or return'); legend_line(1310, 'next', 'Next step')
notes = ['Cards are used for work steps. Decisions stay diamonds, start and end stay pills, connectors stay circles, so the shape grammar still reads at a glance. Side bars on a card mean a subprocess.',
         ('Card colour follows the lane: blue customer, violet app, amber payment, green restaurant, teal courier. Icons come from the detailed set on the Icons page.' if DET else 'Card colour follows the lane: blue customer, violet app, amber payment, green restaurant, teal courier. Icons come from the Icons page; seven were added for this chart (Card, Restaurant, Pot, Courier, Refund, Star, Receipt).')]
for i, t in enumerate(notes): b.text(64, ly + 68 + i * 24, t, 12, '#475569')
print(b.save())
