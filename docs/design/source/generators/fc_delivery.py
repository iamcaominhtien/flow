from fclib import *
W, H = 2880, 1460
b = Board('Flowchart_Delivery', 'Complete flowchart: food delivery, five actors', W, H,
  'One order from tap to doorstep. It combines swimlanes, screen cards, icons, a payment subprocess, a parallel split and join, two retry loops, three failure paths, an off-page connector, the animated main path (blue) and a slower data stream (violet).')
X0, X1, top, LH = 64, 2816, 170, 210
lanes = [('Customer', '#EFF6FF', '#BFDBFE', '#1D4ED8'), ('App and server', '#F3F1FD', '#D4CEF7', '#5B4BD6'), ('Payment', '#FFF7EA', '#F5DDB4', '#B45309'), ('Restaurant', '#F0FBF2', '#BBE7C4', '#15803D'), ('Courier', '#EEFBF9', '#BDE8E3', '#0F766E')]
for i, (nm, bg, bd, fg) in enumerate(lanes):
    yy = top + i * LH
    b.rect(X0, yy, X1 - X0, LH, bg, bd, 0, False)
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{yy}px;width:44px;height:{LH}px;box-sizing:border-box;background:{fg};display:flex;align-items:center;justify-content:center"><span style="writing-mode:vertical-rl;transform:rotate(180deg);color:#fff;font-size:13px;font-weight:700;letter-spacing:.02em;white-space:nowrap">{nm}</span></div>')
C, A, P, R, K = [top + i * LH + LH // 2 for i in range(5)]
x4 = 816; x5 = x4 + 240; x3 = 616
fork = 1200; x7 = 1385; x8 = 1570; join = 1735; x10 = 1920; x11 = 2130; x12 = 2340; x13 = 2530; x14 = 2720
# --- customer lane
st = b.node('terminator', 175, C, 120, 48, 'Open app', icon='phone')
s1 = b.screen(380, C, 'S01', 'Browse'); s2 = b.screen(598, C, 'S02', 'Menu'); s3 = b.screen(x4, C, 'S03', 'Checkout')
s4 = b.screen(x11, C, 'S04', 'Tracking'); s5 = b.screen(x12, C, 'S05', 'Rate order')
rt = b.node('decision', x13, C, 150, 100, 'Rating below 3?', fs=12)
en = b.node('terminator', x14, C, 140, 48, 'Enjoy meal', icon='star')
# --- app lane
co = b.node('process', x4, A, 150, 56, 'Create order', icon='cart')
se = b.node('process', x5, A, 150, 56, 'Show payment error', icon='warn', fs=12)
pu = b.node('io', x7, A, 190, 56, 'Push: order accepted', icon='bell', fs=12)
tm = b.node('process', x11, A, 170, 56, 'Update live tracking', icon='pin', fs=12)
cl = b.node('process', x12, A, 140, 56, 'Close order', icon='doc')
cn = b.node('connector', x13, A, 38, 38, 'A')
# --- payment lane
au = b.node('subprocess', x4, P, 160, 56, 'Authorize card', icon='card', fs=12)
ap = b.node('decision', x5, P, 130, 100, 'Approved?')
rf = b.node('subprocess', x3, P, 160, 56, 'Refund customer', icon='refund', fs=12)
mr = b.node('terminator', 380, P, 150, 48, 'Money returned')
cp = b.node('process', x12, P, 150, 56, 'Capture payment', icon='card', fs=12)
# --- restaurant lane
ac = b.node('decision', x5, R, 150, 100, 'Accepts order?', fs=12)
ca = b.node('process', x3, R, 140, 56, 'Cancel order', icon='warn')
pf = b.node('preparation', x7, R, 160, 56, 'Prepare food', icon='pot')
rd = b.node('process', x8, R, 140, 56, 'Mark ready', icon='check')
# --- courier lane
fc = b.node('process', x7, K, 140, 56, 'Find courier', icon='bike')
fd = b.node('decision', x8, K, 110, 90, 'Found?')
pk = b.node('process', x10, K, 140, 56, 'Pick up order', icon='box', fs=12)
dl = b.node('process', x11, K, 140, 56, 'Deliver to door', icon='pin', fs=12)
cd = b.node('process', x12, K, 150, 56, 'Confirm delivery', icon='check', fs=12)
b.bar(fork, R - 45, K + 45); b.bar(join, R - 45, K + 45)
M = 'main'
# main path
b.arrow([st.r(), s1.l()], M)
b.arrow([s1.r(), s2.l()], M); b.chip((s1.r()[0] + s2.l()[0]) / 2, C - 20, 'tap shop')
b.arrow([s2.r(), s3.l()], M); b.chip((s2.r()[0] + s3.l()[0]) / 2, C - 20, 'checkout')
b.arrow([s3.b(), co.t()], M); b.arrow([co.b(), au.t()], M); b.arrow([au.r(), ap.l()], M)
b.arrow([ap.b(), ac.t()], M); b.label(x5 + 22, P + 66, 'Yes', 'yes')
b.arrow([ac.r(), (fork - 4, R)], M); b.label((ac.r()[0] + fork) / 2, R - 18, 'Yes', 'yes')
b.arrow([(fork + 4, R), pf.l()], M)
b.arrow([(fork + 4, K), fc.l()], M)
b.arrow([pf.r(), rd.l()], M); b.arrow([rd.r(), (join - 4, R)], M)
b.arrow([fc.r(), fd.l()], M)
b.arrow([fd.r(), (join - 4, K)], M); b.label((fd.r()[0] + join) / 2, K - 18, 'Yes', 'yes')
b.arrow([(join + 4, K), pk.l()], M)
b.arrow([pk.r(), dl.l()], M); b.arrow([dl.r(), cd.l()], M)
b.arrow([cd.t(), cp.b()], M); b.arrow([cp.t(), cl.b()], M); b.arrow([cl.t(), s5.b()], M)
b.arrow([s5.r(), rt.l()], M)
b.arrow([rt.r(), en.l()], M); b.label((rt.r()[0] + en.l()[0]) / 2, C - 18, 'No', 'no')
# branches
b.arrow([ap.t(), se.b()], 'no', 'No', (x5 + 22, P - 66))
b.arrow([se.t(), (x5, C), s3.r()], 'back', 'Edit card', (x5 - 56, C - 16))
b.arrow([ac.l(), ca.r()], 'no', 'No', ((ac.l()[0] + ca.r()[0]) / 2, R - 16))
b.arrow([ca.t(), rf.b()], 'no')
b.arrow([rf.l(), mr.r()])
b.arrow([rt.b(), cn.t()], 'yes', 'Yes', (x13 + 22, C + 78))
b.text(x13 + 34, A - 16, 'Continues in<br><b>Support case</b> flow', 12, '#475569', lh=17)
# courier retry loop
b.arrow([fd.b(), (x8, K + 80), (x7, K + 80), fc.b()], 'back')
b.chip((x7 + x8) / 2, K + 80, 'wait 30 s', False, 'clock')
b.label(x8 + 22, K + 60, 'No', 'no')
# data stream (violet, slower)
b.arrow([(fork, R - 45), (fork, A), pu.l()], 'data')
b.arrow([pu.r(), tm.l()], 'data')
b.arrow([dl.t(), tm.b()], 'data'); b.arrow([tm.t(), s4.b()], 'data')
b.chip(x11 + 62, P + 6, 'live location', False, 'pin')
# legend
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
legend_line(1010, 'no', 'Failure')
legend_line(1130, 'back', 'Retry or return')
legend_line(1310, 'next', 'Next step')
notes = ['Customer lane uses screen cards (S01 to S05) from the Screen flow notation, so one chart links logic and screens. The S-IDs match the Screen flow diagram of the same app.',
         'Icons name the kind of work: phone, cart, card, pot, bike, pin. They are optional and never replace the text.',
         'Failure paths: payment declined (back to Checkout), restaurant declines (cancel and refund), low rating (off-page flow A).']
for i, t in enumerate(notes): b.text(64, ly + 68 + i * 24, t, 12, '#475569')
print(b.save())
