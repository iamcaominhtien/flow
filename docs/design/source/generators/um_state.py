from umllib import *
W, H = 3120, 1120
b = Board('UML_State', 'State machine: the life of an order', W, H,
  'Boxes are states, arrows are transitions written as event, [guard] and / action. The filled dot is the start, the ringed dot an end. The blue path is the happy path. A frame groups states that belong together.')
y1, y2 = 400, 760
X = lambda i: 360 + 340 * i
zone_x0, zone_x1 = X(4) - 110, X(6) + 110
b.rect(zone_x0, y1 - 110, zone_x1 - zone_x0, 220, 'rgba(15,118,110,0.07)', '#64748B', 18)
b.pill(zone_x0 + 18, y1 - 121, 'Delivering', '#0F172A')
st0 = initial(b, 150, y1)
pl = state(b, X(0), y1, 'Placed', 'blue')
pa = state(b, X(1), y1, 'Paid', 'amber')
pr = state(b, X(2), y1, 'Preparing', 'green', sub='do / cook')
rd = state(b, X(3), y1, 'Ready', 'green')
pk = state(b, X(4), y1, 'Picked up', 'teal')
ow = state(b, X(5), y1, 'On the way', 'teal', sub='do / share location')
ar = state(b, X(6), y1, 'Arrived', 'teal')
dv = state(b, X(7), y1, 'Delivered', 'green')
fe = final(b, X(7) + 260, y1)
ca = state(b, (X(0) + X(1)) / 2, y2, 'Cancelled', 'rose', w=400)
rf = state(b, X(7), y2, 'Refunded', 'rose')
fe2 = final(b, X(7) + 260, y2)
g = lambda a, c: ((a.r()[0] + c.l()[0]) / 2, a.cy)
b.arrow([st0.r(), pl.l()], 'main', 'checkout / create order', ((st0.r()[0] + pl.l()[0]) / 2 - 8, y1 - 26)) if False else b.arrow([st0.r(), pl.l()], 'main')
b.arrow([pl.r(), pa.l()], 'main', 'payment succeeded', g(pl, pa))
b.arrow([pa.r(), pr.l()], 'main', 'restaurant accepts', g(pa, pr))
b.arrow([pr.r(), rd.l()], 'main', 'food done', g(pr, rd))
b.arrow([rd.r(), pk.l()], 'main', 'courier arrives', g(rd, pk))
b.arrow([pk.r(), ow.l()], 'main', 'leaves restaurant', g(pk, ow))
b.arrow([ow.r(), ar.l()], 'main', '[near address] / notify', g(ow, ar))
b.arrow([ar.r(), dv.l()], 'main', 'customer confirms', g(ar, dv))
b.arrow([dv.r(), fe.l()], 'main')
# cancel
b.arrow([(pl.cx, pl.b()[1]), (pl.cx, ca.t()[1])], 'no', 'cancel', (pl.cx + 40, (pl.b()[1] + ca.t()[1]) / 2))
b.arrow([(pa.cx, pa.b()[1]), (pa.cx, ca.t()[1])], 'no', 'cancel / refund', (pa.cx + 62, (pa.b()[1] + ca.t()[1]) / 2))
b.arrow([ca.r(), (X(7) - 400, y2), (X(7) - 400, y2)], 'no') if False else None
b.arrow([ca.r(), (ca.r()[0] + 120, y2)], 'no') if False else None
b.arrow([rf.r(), fe2.l()], 'no')
b.arrow([(dv.cx, dv.b()[1]), (dv.cx, rf.t()[1])], 'no', 'refund [within 7 days]', (dv.cx + 82, (dv.b()[1] + rf.t()[1]) / 2))
# cancelled -> end : route along the bottom
yb = y2 + 80
b.arrow([(ca.cx, ca.b()[1]), (ca.cx, yb), (fe2.cx, yb), (fe2.cx, fe2.cy + 16)], 'no', 'cleanup', (1400, yb))
# self transition on Preparing
sx = pr.cx
b.raw(f'<svg width="150" height="60" viewBox="0 0 150 60" style="position:absolute;left:{sx-75}px;top:{pr.t()[1]-58}px;overflow:visible;fill:none;stroke:#0F172A;stroke-width:2"><path d="M45 58 V20 Q45 4 75 4 Q105 4 105 20 V50"/><path d="M99 44 L105 56 L111 44 Z" fill="#0F172A" stroke="none"/></svg>')
b.label(sx, pr.t()[1] - 70, 'item out of stock / substitute', 'plain')
# guard note
b.raw(f'<div style="position:absolute;left:1280px;top:{y2-30}px;width:600px;font-size:12.5px;line-height:19px;color:#475569"><b style="color:#0F172A">How to read a label.</b> <span style="font-family:\'JetBrains Mono\',monospace">event [guard] / action</span>: the event triggers it, the guard must be true, the action runs on the way. Any part may be left out.</div>')
print(save5(b))
