from bpmnlib import *
W, H = 2560, 1760
b = Board('BPMN_Order', 'BPMN, complex: from order to delivered parcel', W, H,
  'Four participants and a customer: the shop (three lanes), the payment provider, the courier company and the customer as a black box. It combines splits and joins, a task per item, a loop, a payment deadline, a delivery deadline, a retry loop and six message flows. Blue is the shop\'s happy path.')
X0, X1 = 64, 2480
blackbox(b, X0, 190, X1 - X0, 70, 'Customer  (black box)', 'blue')
SP0, SP1 = 300, 1110
b.raw(f'<div data-lint="box" style="position:absolute;left:{X0}px;top:{SP0}px;width:{X1-X0}px;height:{SP1-SP0}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div>')
for n, y0, y1, tone in [('Orders', 300, 540, 'blue'), ('Warehouse', 540, 780, 'violet'), ('Finance', 780, 1110, 'amber')]:
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{y0}px;width:36px;height:{y1-y0}px;box-sizing:border-box;border:2px solid #0F172A;background:{TONES[tone][1]};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:13px;font-weight:800">{n}</div></div>')
    if y0 != 300: b.raw(f'<div data-lint="edge" style="position:absolute;left:{X0}px;top:{y0}px;width:{X1-X0}px;border-top:2px solid #0F172A"></div>')
pool(b, X0, 1150, X1 - X0, 200, 'Payment provider', 'amber')
pool(b, X0, 1390, X1 - X0, 260, 'Courier company', 'teal')
yo, yr, yw, yf = 450, 350, 660, 860
# ---- shop: orders lane
s1 = event(b, 220, yo, 'start', 'message', 'Order placed')
t1 = task(b, 370, yo, 'Validate order', 'service', 140, 64, 'blue')
g1 = gateway(b, 530, yo, 'x', 'Valid?', lpos='below')
trej = task(b, 680, yr, 'Reject order', 'send', 130, 64, 'blue'); erej = event(b, 810, yr, 'end')
g2 = gateway(b, 680, yo, 'plus')
g3 = gateway(b, 1580, yo, 'plus')
thand = task(b, 1720, yo, 'Hand to courier', 'send', 140, 64, 'blue')
twait2 = task(b, 1950, yo, 'Wait for delivery', 'receive', 150, 64, 'blue')
tcap = task(b, 2160, yo, 'Capture payment', 'send', 140, 64, 'blue')
eend = event(b, 2320, yo, 'end', None, 'Done')
tinv = task(b, 2060, yw, 'Open investigation', 'user', 150, 64, 'blue'); einv = event(b, 2210, yw, 'end', 'error', 'Lost parcel')
tm2 = boundary(b, 1910, yo + 32, 'timer', True)
# ---- warehouse
tres = task(b, 860, yw, 'Reserve stock', 'service', 140, 64, 'violet'); multi(b, 860, yw + 32)
tpk = task(b, 1060, yw, 'Pick and pack', 'manual', 140, 64, 'violet'); loopmark(b, 1060, yw + 32)
# ---- finance
treq = task(b, 860, yf, 'Request payment', 'send', 140, 64, 'amber')
twt = task(b, 1280, yf, 'Wait for payment result', 'receive', 200, 64, 'amber')
tm1 = boundary(b, 1230, yf + 32, 'timer', True)
g4 = gateway(b, 1470, yf, 'x', 'Paid?', lpos='above')
tcan = task(b, 1100, 990, 'Cancel order', 'send', 130, 64, 'amber'); ecan = event(b, 960, 990, 'end', None, 'Cancelled')
# ---- provider
ps = event(b, 840, 1250, 'start', 'message', 'Payment requested')
pa = task(b, 1000, 1250, 'Authorise card', 'service', 140, 64, 'amber')
pr = task(b, 1360, 1250, 'Return result', 'send', 140, 64, 'amber')
pe = event(b, 1520, 1250, 'end')
# ---- courier
ks = event(b, 1720, 1500, 'start', 'message', 'Pickup booked')
kc = task(b, 1860, 1500, 'Collect parcel', 'manual', 130, 64, 'teal')
kd = task(b, 2010, 1500, 'Deliver', 'manual', 110, 64, 'teal')
kg = gateway(b, 2150, 1500, 'x', 'Delivered?', lpos='above')
kf = task(b, 2300, 1500, 'Confirm delivery', 'send', 140, 64, 'teal'); ke = event(b, 2430, 1500, 'end')
kw = event(b, 2010, 1590, 'intermediate', 'timer', 'Wait a day', lpos='below')
a = b.arrow
# main happy path
a([s1.r(), t1.l()], 'main'); a([t1.r(), g1.l()], 'main'); a([g1.r(), g2.l()], 'main', 'yes', (605, yo - 14))
a([g3.r(), thand.l()], 'main'); a([thand.r(), twait2.l()], 'main'); a([twait2.r(), tcap.l()], 'main'); a([tcap.r(), eend.l()], 'main')
# branches
a([(530, yo - 26), (530, yr), trej.l()], 'no', 'no', (552, yr + 22)); a([trej.r(), erej.l()], 'next')
a([(680, yo + 26), (680, yw), tres.l()], 'main'); a([(680, yo + 26), (680, yf), treq.l()], 'main')
a([tres.r(), tpk.l()], 'main'); a([tpk.r(), (1580, yw), (1580, yo + 26)], 'main')
a([treq.r(), twt.l()], 'main'); a([twt.r(), g4.l()], 'main')
a([g4.r(), (1580, yf), (1580, yo + 26)], 'main', 'yes', (1530, yf - 14))
a([(1470, yf + 26), (1470, 1075), (1100, 1075), (1100, 1022)], 'no', 'no', (1470 + 20, 1000))
a([(1230, yf + 47), (1230, 990), tcan.r()], 'no'); a([tcan.l(), ecan.r()], 'next')
a([(1910, yo + 47), (1910, yw), tinv.l()], 'no'); a([tinv.r(), einv.l()], 'next')
# provider and courier flows
a([ps.r(), pa.l()], 'next'); a([pa.r(), pr.l()], 'next'); a([pr.r(), pe.l()], 'next')
a([ks.r(), kc.l()], 'next'); a([kc.r(), kd.l()], 'next'); a([kd.r(), kg.l()], 'next')
a([kg.r(), kf.l()], 'next', 'yes', (2201, 1482)); a([kf.r(), ke.l()], 'next')
a([(2150, 1526), (2150, 1590), kw.r()], 'next', 'no', (2172, 1560)); a([kw.l(), (2010 - 20 - 0, 1590)] if False else [(1990, 1590), (1990, 1590)], 'next') if False else None
a([(2010, 1570), (2010, 1532)], 'back')
# message flows
msgflow(b, [(220, 260), (220, yo - 20)], 'order', (252, 280))
msgflow(b, [(680, yr - 32), (680, 260)], 'rejection', (718, 280))
msgflow(b, [(840, yf + 32), (840, 1230)], 'payment request', (840, 1130))
msgflow(b, [(1360, 1218), (1360, yf + 32)], 'payment result', (1360, 1130))
msgflow(b, [(1720, yo + 32), (1720, 1480)], 'pickup', (1720, 1130))
msgflow(b, [(2300, 1468), (2300, 1370), (1950, 1370), (1950, yo + 32)], 'delivery confirmed', (2125, 1370))
print(save7(b))
