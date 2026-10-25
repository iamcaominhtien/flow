from umllib import *
W, H = 1840, 1260
b = Board('UML_Class', 'Class diagram: the delivery domain', W, H,
  'Each box is a class: name, attributes, operations. Lines say how classes relate: plain association, whole and part, inheritance, interface, dependency. Numbers at the ends say how many.')
CW_ = 280
def cls(x, y, name, attrs, ops, tone='blue', kind=None, abstract=False):
    bg, pill = TONES[tone]
    ah, oh, th = (22 * len(attrs) + 12 if attrs else 0), 22 * len(ops) + 12, 56 if kind else 40
    h = th + ah + oh
    nm = f'<i>{name}</i>' if abstract else name
    ster = f'<div style="font:500 11px/14px Inter,sans-serif;color:#475569">&laquo;{kind}&raquo;</div>' if kind else ''
    arow = ''.join(f'<div style="font:500 12px/22px \'JetBrains Mono\',monospace;white-space:nowrap">{a}</div>' for a in attrs)
    orow = ''.join(f'<div style="font:500 12px/22px \'JetBrains Mono\',monospace;white-space:nowrap">{o}</div>' for o in ops)
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{CW_}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:10px;background:#fff;overflow:hidden">'
          f'<div style="height:{th}px;background:{pill};border-bottom:2px solid #0F172A;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:14px;font-weight:800">{ster}{nm}</div>'
          + (f'<div style="height:{ah}px;box-sizing:border-box;padding:6px 12px;border-bottom:2px solid #0F172A">{arow}</div>' if attrs else '') + f'<div style="padding:6px 12px">{orow}</div></div>')
    n = Node(x + CW_ / 2, y + h / 2, CW_, h); n.x, n.y, n.h_ = x, y, h
    return n
X = [80, 540, 1000, 1460]
cu = cls(X[0], 200, 'Customer', ['+id: UUID', '+name: String', '+email: String'], ['+placeOrder(): Order'], 'blue')
od = cls(X[1], 200, 'Order', ['-id: UUID', '-status: OrderStatus', '-total: Money'], ['+addItem(d: Dish, n: int)', '+cancel()', '+pay(p: Payment)'], 'violet')
oi = cls(X[2], 200, 'OrderItem', ['-quantity: int', '-unitPrice: Money'], ['+subtotal(): Money'], 'violet')
di = cls(X[3], 200, 'Dish', ['+name: String', '+price: Money'], ['+isAvailable(): bool'], 'green')
de = cls(X[0], 560, 'Delivery', ['+pickedUpAt: Time', '+deliveredAt: Time'], ['+complete()'], 'teal')
pa = cls(X[1], 560, 'Payment', ['#amount: Money'], ['+authorise(): bool'], 'amber', abstract=True)
nf = cls(1040, 560, 'Notifier', [], ['+notify(msg: String)'], 'gray', kind='interface')
re = cls(X[3], 560, 'Restaurant', ['+name: String', '+rating: float'], ['+accept(o: Order)'], 'green')
co = cls(X[0], 900, 'Courier', ['+name: String', '+vehicle: String'], ['+deliver(o: Order)'], 'teal')
cp = cls(400, 900, 'CardPayment', ['-cardToken: String'], ['+authorise(): bool'], 'amber')
wp = cls(700, 900, 'WalletPayment', ['-walletId: String'], ['+authorise(): bool'], 'amber')
en = cls(1040, 900, 'EmailNotifier', ['-smtpHost: String'], ['+notify(msg: String)'], 'gray')
def L(*a, **k): link(b, *a, **k)
# Customer 1 - * Order
L([(cu.x + CW_, 250), (od.x, 250)], None, None, label='places', lpos=(450, 226), ma='1', mb='0..*')
# Order composition OrderItem
L([(od.x + CW_, 250), (oi.x, 250)], 'dia_fill', None, ma='1', mb='1..*', label='contains', lpos=(910, 226))
# OrderItem -> Dish (navigable)
L([(oi.x + CW_, 250), (di.x, 250)], None, 'open', ma='*', mb='1', label='of', lpos=(1370, 226))
# Order - Delivery (association)
L([(od.x, 330), (400, 330), (400, 620), (de.x + CW_, 620)], None, None, ma='1', mb='0..1', label='delivered by', lpos=(400, 470))
# Order - Payment
L([(od.x + CW_ / 2, od.y + od.h_), (pa.x + CW_ / 2, pa.y)], None, None, ma='1', mb='0..*', label='paid by', lpos=(od.x + CW_ / 2 + 52, 480))
# Courier - Delivery
L([(co.x + CW_ / 2, co.y), (de.x + CW_ / 2, de.y + de.h_)], None, None, ma='1', mb='0..*', label='carries', lpos=(co.x + CW_ / 2 + 46, 800)) if False else L([(de.x + CW_ / 2, de.y + de.h_), (co.x + CW_ / 2, co.y)], None, None, ma='0..*', mb='1', label='carries', lpos=(de.x + CW_ / 2 + 46, 800))
# Dish aggregated by Restaurant
L([(di.x + CW_ / 2, di.y + di.h_), (re.x + CW_ / 2, re.y)], None, None, ma='0..*', mb='', label='offers', lpos=(di.x + CW_ / 2 + 38, 470)) if False else L([(re.x + CW_ / 2, re.y), (di.x + CW_ / 2, di.y + di.h_)], 'dia_hollow', None, ma='1', mb='0..*', label='offers', lpos=(re.x + CW_ / 2 + 38, 470))
# inheritance Payment <- Card, Wallet
ty = 800
uline(b, [(pa.x + CW_ / 2, pa.y + pa.h_ + 18), (pa.x + CW_ / 2, ty), (cp.x + CW_ / 2, ty), (cp.x + CW_ / 2, cp.y)])
uline(b, [(pa.x + CW_ / 2, ty), (wp.x + CW_ / 2, ty), (wp.x + CW_ / 2, wp.y)])
umark(b, pa.x + CW_ / 2, pa.y + pa.h_, (0, 1), 'tri')
# realization Notifier <- EmailNotifier (dashed)
uline(b, [(nf.x + CW_ / 2, nf.y + nf.h_ + 18), (nf.x + CW_ / 2, en.y)], dashed=True)
umark(b, nf.x + CW_ / 2, nf.y + nf.h_, (0, 1), 'tri')
# dependency Order -> Notifier
L([(od.x + CW_, 380), (960, 380), (960, nf.y + 56 + 17), (nf.x, nf.y + 56 + 17)], None, 'open', dashed=True, label='uses', lpos=(960, 520))
# legend
ly = 1190
items = [('Association', None, False), ('Whole and part (composition)', 'dia_fill', False), ('Aggregation', 'dia_hollow', False), ('Inheritance', 'tri', False), ('Realises an interface', 'tri', True), ('Dependency', 'open', True)]
x = 80
for t, mk, dash in items:
    uline(b, [(x + (20 if mk in ('dia_fill', 'dia_hollow') else 0), ly), (x + 70, ly)], dashed=dash)
    if mk in ('dia_fill', 'dia_hollow'): umark(b, x, ly, (1, 0), mk)
    elif mk: umark(b, x + 70, ly, (-1, 0), mk)
    b.text(x + 84, ly - 9, t, size=12, color='#334155')
    x += 84 + 8 * len(t) + 36
print(save5(b))
