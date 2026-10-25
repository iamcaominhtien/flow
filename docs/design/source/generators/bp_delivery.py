from bpmnlib import *
W, H = 1960, 1260
b = Board('BPMN_Delivery', 'BPMN: ordering and delivering a meal', W, H,
  'Three participants, each in its own pool. Solid arrows are the order of work inside a pool. Dashed arrows are messages between pools. Circles are events, diamonds are decisions. Blue is the customer\'s happy path.')
PX0, PX1 = 64, 1900
pool(b, PX0, 190, PX1 - PX0, 270, 'Customer', 'blue')
pool(b, PX0, 500, PX1 - PX0, 250, 'Restaurant', 'green')
pool(b, PX0, 790, PX1 - PX0, 220, 'Courier', 'teal')
y1, y2 = 275, 385
# customer
cs = event(b, 210, y1, 'start', None, 'Hungry')
cp = task(b, 360, y1, 'Place order', 'user', 130, 64, 'blue')
eg = gateway(b, 540, y1, 'event')
cc = event(b, 830, y1, 'intermediate', 'message', 'Confirmed', lpos='above')
ct = task(b, 1080, y1, 'Track order', 'user', 140, 64, 'blue')
cf = event(b, 1500, y1, 'intermediate', 'message', 'Food arrives', lpos='above')
ce = task(b, 1640, y1, 'Eat and rate', 'manual', 130, 64, 'blue')
cn = event(b, 1790, y1, 'end', None, 'Done')
cr = event(b, 700, y2, 'intermediate', 'message', 'Rejected', lpos='above')
cx_ = event(b, 780, y2, 'end', 'error', 'Not served')
# restaurant
y3, y4 = 560, 650
rs = event(b, 360, y4, 'start', 'message', 'Order received')
rg = gateway(b, 520, y4, 'x', 'In stock?', lpos='below')
rr = task(b, 700, y3, 'Reject order', 'send', 130, 64, 'green')
re2 = event(b, 840, y3, 'end', None)
rc = task(b, 860, y4 + 0, 'Confirm order', 'send', 130, 64, 'green') if False else task(b, 880, y4, 'Confirm order', 'send', 130, 64, 'green')
rk = task(b, 1050, y4, 'Cook', 'task', 110, 64, 'green')
rp = task(b, 1190, y4, 'Pack', 'task', 100, 64, 'green')
rh = task(b, 1340, y4, 'Hand to courier', 'send', 140, 64, 'green')
rn = event(b, 1470 if False else 1480, y4, 'end')
# courier
y5 = 900
ks = event(b, 1340, y5, 'start', 'message', 'Pickup request')
kp = task(b, 1470, y5, 'Pick up', 'manual', 110, 64, 'teal')
kr = task(b, 1600, y5, 'Ride', 'manual', 110, 64, 'teal')
kh = task(b, 1740, y5, 'Hand over', 'send', 120, 64, 'teal')
ke = event(b, 1860, y5, 'end')
a = b.arrow
# customer sequence
a([cs.r(), cp.l()], 'main'); a([cp.r(), eg.l()], 'main')
a([eg.r(), cc.l()], 'main'); a([cc.r(), ct.l()], 'main'); a([ct.r(), cf.l()], 'main'); a([cf.r(), ce.l()], 'main'); a([ce.r(), cn.l()], 'main')
a([(540, y1 + 26), (540, y2), cr.l()], 'next')
a([cr.r(), cx_.l()], 'next')
# restaurant sequence
a([rs.r(), rg.l()], 'next', None); a([rg.r(), rc.l()], 'next', 'yes', ((rg.r()[0] + rc.l()[0]) / 2, y4 - 14))
a([(520, y4 - 26), (520, y3), rr.l()], 'next', 'no', (520 + 20, y3 + 26))
a([rr.r(), re2.l()], 'next'); a([rc.r(), rk.l()], 'next'); a([rk.r(), rp.l()], 'next'); a([rp.r(), rh.l()], 'next'); a([rh.r(), rn.l()], 'next')
# courier sequence
a([ks.r(), kp.l()], 'next'); a([kp.r(), kr.l()], 'next'); a([kr.r(), kh.l()], 'next'); a([kh.r(), ke.l()], 'next')
# message flows
msgflow(b, [(360, y1 + 32), (360, y4 - 20)], 'order', (392, 480))
msgflow(b, [(700, y3 - 32), (700, y2 + 20)], 'rejection', (734, 470))
msgflow(b, [(880, y4 - 32), (880, y1 + 20)], None) if False else None
msgflow(b, [(880, y4 - 32), (880, 482), (830, 482), (830, y1 + 20)], 'confirmation', (830, 436))
msgflow(b, [(1340, y4 + 32), (1340, y5 - 20)], 'pickup', (1380, 770))
msgflow(b, [(1740, y5 - 32), (1740, 470), (1500, 470), (1500, y1 + 20)], 'delivery', (1620, 470))
# note
b.raw('<div style="position:absolute;left:64px;top:1060px;width:1500px;font-size:12.5px;line-height:19px;color:#475569"><b style="color:#0F172A">Event-based gateway</b> (the diamond with a ring and a pentagon after Place order): the customer waits for whichever message arrives first, a confirmation or a rejection.</div>')
print(save7(b))
