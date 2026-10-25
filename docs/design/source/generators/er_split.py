from erlib import *
b = Board('ER_Split', 'Splitting a large schema by domain', 1600, 1120,
  'When one page is too small, split by domain. An overview shows the domains and what links them; each page shows one domain in full, and a table that belongs to another domain appears once as a grey dashed copy with a tag.')
def panel(x, y, w, h, title):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x + 22, y + 16, title, size=16, color='#0F172A', weight=800)
# overview
panel(64, 130, 1472, 370, 'Overview: domains and links')
doms = {'rest': ('Restaurant', 'green', 90, 200, ['Restaurant', 'Dish']), 'ord': ('Orders', 'violet', 620, 200, ['Customer', 'Order', 'OrderItem']),
        'del': ('Delivery', 'teal', 1150, 200, ['Delivery', 'Courier']), 'pay': ('Payment', 'amber', 620, 380, ['Payment', 'Refund'])}
for k, (n, tone, x, y, ts) in doms.items():
    bg, hd = TONES[tone]
    b.rect(x, y, 360, 112 if k != 'pay' else 100, bg, '#64748B', 16)
    b.pill(x + 16, y - 11, n, '#0F172A')
    for i, t in enumerate(ts):
        b.raw(f'<div style="position:absolute;left:{x+20+i*112}px;top:{y+36}px;width:104px;height:34px;box-sizing:border-box;border:2px solid #0F172A;border-radius:8px;background:#fff;font-size:12.5px;font-weight:700;display:flex;align-items:center;justify-content:center">{t}</div>')
line(b, [(450, 256), (620, 256)]); b.label(535, 256, 'restaurant_id', 'plain')
line(b, [(980, 256), (1150, 256)]); b.label(1065, 256, 'order_id', 'plain')
line(b, [(800, 312), (800, 380)]); b.label(800, 346, 'order_id', 'plain')
b.text(1150, 360, 'A line between domains is a foreign key.', size=12, color='#475569')
b.text(1150, 380, 'Name it after the column, not the table.', size=12, color='#475569')
# page Orders
panel(64, 530, 720, 560, 'Page 1: Orders')
cu = entity(b, 80, 596, 'Customer', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('email', 'text', 'uq')], 'blue', 'user', w=190)
od = entity(b, 330, 596, 'Order', [('id', 'uuid', 'pk'), ('customer_id', 'uuid', 'fk'), ('restaurant_id', 'uuid', 'fk'), ('status', 'text', '')], 'violet', 'cart', w=200)
gr = entity(b, 590, 596, 'Restaurant', [('id', 'uuid', 'pk')], 'green', 'store', w=170, ghost=True, tag='see Restaurant page')
oi = entity(b, 330, 840, 'OrderItem', [('order_id', 'uuid', 'pk,fk'), ('dish_id', 'uuid', 'pk,fk'), ('quantity', 'int', '')], 'violet', 'doc', w=200)
gd = entity(b, 590, 840, 'Dish', [('id', 'uuid', 'pk')], 'green', 'pot', w=170, ghost=True, tag='see Restaurant page')
rel(b, hv((cu.r, cu.row('id')), (od.l, od.row('customer_id')), 300), 'one', 'zero_many', 'places', (300, cu.row('id') - 16))
rel(b, hv((gr.l, gr.row('id')), (od.r, od.row('restaurant_id')), 560), 'one', 'zero_many')
rel(b, [(od.cx, od.bot), (od.cx, oi.y)], 'one', 'many', 'contains', (od.cx + 36, od.bot + 50))
rel(b, hv((gd.l, gd.row('id')), (oi.r, oi.row('dish_id')), 560), 'one', 'zero_many')
b.text(88, 1040, 'Grey dashed tables belong to another page. They show only their key.', size=12, color='#475569')
# page Delivery
panel(816, 530, 720, 560, 'Page 2: Delivery')
go = entity(b, 832, 596, 'Order', [('id', 'uuid', 'pk')], 'violet', 'cart', w=170, ghost=True, tag='see Orders page')
de = entity(b, 1100, 596, 'Delivery', [('id', 'uuid', 'pk'), ('order_id', 'uuid', 'fk,uq'), ('courier_id', 'uuid', 'fk'), ('delivered_at', 'timestamp', 'null')], 'teal', 'box', w=232)
co = entity(b, 1100, 840, 'Courier', [('id', 'uuid', 'pk'), ('name', 'text', ''), ('vehicle', 'text', '')], 'teal', 'bike', w=210)
rel(b, hv((go.r, go.row('id')), (de.l, de.row('order_id')), 1050), 'one', 'zero_one', 'delivered by', (1050, go.row('id') - 16))
rel(b, [(de.cx, de.bot), (de.cx, co.y)] if False else [(co.cx, co.y), (co.cx, de.bot)], 'one', 'zero_many', 'carries', (co.cx + 40, de.bot + 50))
b.text(840, 1040, 'The same Order table is drawn in full only on page 1.', size=12, color='#475569')
print(save(b))
