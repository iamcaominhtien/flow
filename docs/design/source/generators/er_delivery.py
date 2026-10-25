from erlib import *
def build(style):
    ill = style == 'detail'
    name = 'ER_Delivery' + ('_Illustrated' if ill else '')
    ay = 190
    hh = 64 if ill else 40
    obot = ay + hh + 8 + 6 * RH
    by = obot + 130
    H = by + hh + 8 + 5 * RH + 90
    b = Board(name, 'Complete schema: food delivery' + (', illustrated' if ill else ', plain'), 1600, H,
      'The tables behind one order: who orders, what is in it, who cooks it, who pays and who delivers. Blue is the path a typical read follows. Crossing lines never join.')
    S = dict(style=style)
    cu = entity(b, 80, ay, 'Customer', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('email', 'text', 'uq'), ('phone', 'text', 'null')], 'blue', 'user', 'User', **S)
    od = entity(b, 480, ay, 'Order', [('id', 'uuid', 'pk'), ('customer_id', 'uuid', 'fk'), ('restaurant_id', 'uuid', 'fk'), ('status', 'text', ''), ('total', 'decimal', ''), ('placed_at', 'timestamp', '')], 'violet', 'cart', 'Cart', **S)
    re = entity(b, 880, ay, 'Restaurant', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('rating', 'float', ''), ('city', 'text', '')], 'green', 'store', 'Restaurant', **S)
    co = entity(b, 1280, ay, 'Courier', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('vehicle', 'text', ''), ('status', 'text', '')], 'teal', 'bike', 'Courier', **S)
    pa = entity(b, 80, by, 'Payment', [('id', 'uuid', 'pk'), ('order_id', 'uuid', 'fk'), ('method', 'text', ''), ('amount', 'decimal', ''), ('status', 'text', '')], 'amber', 'card', 'Card', **S)
    oi = entity(b, 480, by, 'OrderItem', [('order_id', 'uuid', 'pk,fk'), ('dish_id', 'uuid', 'pk,fk'), ('quantity', 'int', ''), ('unit_price', 'decimal', '')], 'violet', 'doc', 'Table', **S)
    di = entity(b, 880, by, 'Dish', [('id', 'uuid', 'pk'), ('restaurant_id', 'uuid', 'fk'), ('name', 'text', ''), ('price', 'decimal', ''), ('available', 'bool', '')], 'green', 'pot', 'Pot', **S)
    de = entity(b, 1280, by, 'Delivery', [('id', 'uuid', 'pk'), ('order_id', 'uuid', 'fk,uq'), ('courier_id', 'uuid', 'fk'), ('picked_up_at', 'timestamp', 'null'), ('delivered_at', 'timestamp', 'null')], 'teal', 'box', 'Package', **S)
    rel(b, hv((cu.r, cu.row('id')), (od.l, od.row('customer_id')), 400), 'one', 'zero_many', 'places', (400, cu.row('id') - 16), main=True)
    rel(b, hv((re.l, re.row('id')), (od.r, od.row('restaurant_id')), 800), 'one', 'zero_many', 'receives', (800, re.row('id') - 16))
    rel(b, [(od.cx, od.bot), (od.cx, oi.y)], 'one', 'many', 'contains', (od.cx + 36, od.bot + 50), main=True)
    rel(b, hv((di.l, di.row('id')), (oi.r, oi.row('dish_id')), 800), 'one', 'zero_many', 'sold as', (800, oi.row('dish_id') + 16))
    rel(b, [(re.cx, re.bot), (re.cx, di.y)], 'one', 'many', 'offers', (re.cx + 30, re.bot + 55))
    rel(b, vhv((od.x + 50, od.bot), (pa.cx, pa.y), od.bot + 36), 'one', 'zero_many', 'paid by', (200, od.bot + 36))
    rel(b, vhv((od.r - 50, od.bot), (de.x + 60, de.y), od.bot + 70), 'one', 'zero_one', 'delivered by', (1180, od.bot + 70))
    rel(b, [(de.x + 180, co.bot), (de.x + 180, de.y)], 'one', 'zero_many', 'carries', (de.x + 180 + 38, co.bot + 60))
    b.raw(f'<div style="position:absolute;left:80px;top:{H-62}px;font-size:12px;line-height:18px;color:#475569">Delivery.order_id is unique, so one order has at most one delivery. OrderItem has a composite primary key: one row per dish in an order.</div>')
    return b
for st in ('plain', 'detail'):
    print(save(build(st)))
