from c4lib import *
b = Board('C4_Context', 'Level 1, system context: food delivery', 1700, 1080,
  'Who uses the platform and which outside systems it depends on. The platform is one box here; its insides are not shown. Dashed boxes are systems we do not own.')
yp, ys, ye = 250, 560, 880
cu = c4(b, 330, yp, 'person', 'Customer', '', 'Orders food and tracks the delivery.', 'User', 'blue')
rs = c4(b, 850, yp, 'person', 'Restaurant staff', '', 'Accept orders and mark them ready.', 'Team', 'green')
co = c4(b, 1370, yp, 'person', 'Courier', '', 'Picks up and delivers orders.', 'Courier', 'teal')
sy = c4(b, 850, ys, 'system', 'Delivery platform', '', 'Takes orders, charges payments, dispatches couriers and keeps everyone informed.', 'Server', 'violet', w=360, h=150)
pp = c4(b, 330, ye, 'ext', 'Payment provider', '', 'Charges and refunds cards.', 'Card', 'gray')
mp = c4(b, 850, ye, 'ext', 'Map service', '', 'Routes and arrival times.', 'Globe', 'gray')
sm = c4(b, 1370, ye, 'ext', 'Push and SMS gateway', '', 'Delivers messages to phones.', 'Bell', 'gray')
my = (yp + 66 + ys - 75) / 2
b.arrow([cu.b(), (cu.cx, ys), sy.l()], 'main', 'Orders food using', (cu.cx + 5, 420))
b.arrow([rs.b(), (rs.cx, sy.t()[1])], 'next', 'Accept orders using', (rs.cx, my + 10))
b.arrow([co.b(), (co.cx, ys), sy.r()], 'next', 'Gets jobs from', (co.cx - 5, 420))
b.arrow([(sy.cx - 120, sy.b()[1]), (sy.cx - 120, 735), (pp.cx, 735), pp.t()], 'main', 'Charges cards using', (sy.cx - 260, 735))
b.arrow([sy.b(), mp.t()], 'next', 'Routes and ETAs from', (sy.cx, 735))
b.arrow([(sy.cx + 120, sy.b()[1]), (sy.cx + 120, 735), (sm.cx, 735), sm.t()], 'data', 'Sends messages using', (sy.cx + 260, 735))
print(save8(b))
