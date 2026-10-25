from archlib import *
def build(style):
    ill = style == 'detail'
    name = 'Architecture_Delivery' + ('_Illustrated' if ill else '')
    ph = 80 if ill else 64
    ys = [250, 510, 770, 1030]
    H = ys[-1] + ph + 90
    b = Board(name, 'Complete system: food delivery' + (', illustrated' if ill else ', plain'), 1840, H,
      'Four layers from the phone to the data. Blue is the path of one order: placed in the app, through the gateway to the order service, charged, and paid through the provider. Violet is the event stream that wakes everything else.')
    S = style
    zone(b, 200, ys[0] - ph, 1300, ys[0] + ph, 'Clients', 'blue')
    zone(b, 520, ys[1] - ph, 1400, ys[1] + ph, 'Edge', 'violet')
    zone(b, 170, ys[2] - ph, 1400, ys[2] + ph, 'Services', 'green')
    zone(b, 170, ys[3] - ph, 1760, ys[3] + ph, 'Data', 'amber')
    zone(b, 1500, ys[2] - ph, 1760, ys[2] + ph, 'Third party', 'gray')
    cu = comp(b, 400, ys[0], 'Customer app', 'iOS, Android', 'Mobile', 'blue', S)
    rt = comp(b, 760, ys[0], 'Restaurant tablet', 'kitchen screen', 'Laptop', 'green', S)
    co = comp(b, 1120, ys[0], 'Courier app', 'iOS, Android', 'Mobile', 'teal', S)
    gw = comp(b, 760, ys[1], 'API gateway', 'routing, rate limits', 'Gateway', 'violet', S)
    au = comp(b, 1190, ys[1], 'Auth', 'tokens, sessions', 'Identity (IAM)', 'gray', S)
    di = comp(b, 330, ys[2], 'Dispatch', 'matches couriers', 'Courier', 'teal', S)
    od = comp(b, 760, ys[2], 'Order service', 'checkout, status', 'Server', 'violet', S)
    pa = comp(b, 1190, ys[2], 'Payment service', 'charges, refunds', 'Card', 'amber', S)
    pp = comp(b, 1630, ys[2], 'Payment provider', 'card network', 'Card', 'gray', S)
    ca = comp(b, 330, ys[3], 'Courier cache', 'live locations', 'Cache', 'teal', S)
    db = comp(b, 760, ys[3], 'Orders database', 'PostgreSQL', 'Database', 'violet', S)
    bu = comp(b, 1190, ys[3], 'Event bus', 'order events', 'Event stream', 'amber', S)
    no = comp(b, 1630, ys[3], 'Notifications', 'push and SMS', 'Bell', 'green', S)
    my = ys[0] + ph + (ys[1] - ph - ys[0] - ph) / 2   # y between clients and edge
    # clients -> gateway
    b.arrow([cu.b(), (cu.cx, my), (gw.cx - 70, my), (gw.cx - 70, gw.t()[1])], 'main', 'HTTPS', (cu.cx + 130, my))
    b.arrow([rt.b(), gw.t()], 'next', 'HTTPS', (gw.cx + 38, my))
    b.arrow([co.b(), (co.cx, my), (gw.cx + 70, my), (gw.cx + 70, gw.t()[1])], 'next', 'HTTPS + GPS', (co.cx - 120, my))
    b.arrow([gw.r(), au.l()], 'next', 'verify token', ((gw.r()[0] + au.l()[0]) / 2, ys[1]))
    # gateway -> services
    m2 = ys[1] + ph + (ys[2] - ph - ys[1] - ph) / 2
    b.arrow([(gw.cx - 70, gw.b()[1]), (gw.cx - 70, m2), (di.cx, m2), di.t()], 'next', 'courier status', (di.cx + 150, m2))
    b.arrow([gw.b(), od.t()], 'main', 'create order', (gw.cx, m2 + 34))
    b.arrow([(gw.cx + 70, gw.b()[1]), (gw.cx + 70, m2 - 0), (pa.cx, m2), pa.t()], 'next', 'refunds', (pa.cx - 110, m2))
    # services
    b.arrow([od.r(), pa.l()], 'main', 'charge', ((od.r()[0] + pa.l()[0]) / 2, ys[2]))
    b.arrow([od.l(), di.r()], 'next', 'assign courier', ((od.l()[0] + di.r()[0]) / 2, ys[2]))
    b.arrow([pa.r(), pp.l()], 'main', 'HTTPS API', ((pa.r()[0] + pp.l()[0]) / 2, ys[2]))
    # data
    b.arrow([od.b(-0 if False else 0), db.t()], 'next', 'write', (od.cx + 30, (od.b()[1] + db.t()[1]) / 2))
    b.arrow([di.b(), ca.t()], 'next', 'positions', (di.cx + 40, (di.b()[1] + ca.t()[1]) / 2))
    m3 = od.b()[1] + (db.t()[1] - od.b()[1]) / 2
    b.arrow([(od.cx + 80, od.b()[1]), (od.cx + 80, m3 + 12), (bu.cx, m3 + 12), bu.t()], 'data', 'order.placed', (bu.cx - 150, m3 + 12))
    b.arrow([bu.r(), no.l()], 'data', 'order.placed', ((bu.r()[0] + no.l()[0]) / 2, ys[3]))
    return b
for st in ('plain', 'detail'):
    print(save2(build(st)))
