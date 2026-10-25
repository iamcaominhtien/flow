from fclib import *
b = Board('Flowchart_Complex', 'Complete flowchart: online payment', 1780, 880,
  'All parts together: numbered steps, a subprocess, two decisions, a retry loop, an error branch, a document and the one animated main path (blue) from start to confirmation.')
y = 260
def N(kind, cx, w, h, t, chip=None): return b.node(kind, cx, y, w, h, t, chip=chip)
x = 64; gap = 70
def place(kind, w, h, t, chip=None):
    global x
    n = N(kind, x + w/2, w, h, t, chip); x += w + gap; return n
a1 = place('terminator', 130, 48, 'Cart ready')
a2 = place('preparation', 140, 56, 'Load cart', '1')
a3 = place('subprocess', 160, 56, 'Validate address', '2')
a4 = place('decision', 150, 100, 'In stock?', '3')
a5 = place('process', 150, 56, 'Authorize card', '4')
a6 = place('decision', 150, 100, 'Approved?', '5')
a7 = place('document', 130, 60, 'Receipt', '6')
a8 = place('terminator', 150, 48, 'Order confirmed')
for p, q in [(a1, a2), (a2, a3), (a3, a4)]: b.arrow([p.r(), q.l()], 'main')
b.arrow([a4.r(), a5.l()], 'main'); b.label((a4.r()[0]+a5.l()[0])/2, y-18, 'Yes', 'yes')
b.arrow([a5.r(), a6.l()], 'main')
b.arrow([a6.r(), a7.l()], 'main'); b.label((a6.r()[0]+a7.l()[0])/2, y-18, 'Yes', 'yes')
b.arrow([a7.r(), a8.l()], 'main')
# branch 1: out of stock
y2 = 470
o1 = b.node('process', a4.cx, y2, 150, 56, 'Show out-of-stock', chip='3a')
b.arrow([a4.b(), o1.t()], 'no', 'No', (a4.cx + 22, 360))
b.arrow([o1.l(), (a2.cx, y2), (a2.cx, a2.b()[1])], 'back', 'Edit cart', (a2.cx + (a4.cx - a2.cx)/2 - 20, y2 - 18))
# branch 2: payment declined
d3 = b.node('decision', a6.cx, y2 + 20, 150, 100, 'Retry < 3?', chip='5a')
b.arrow([a6.b(), d3.t()], 'no', 'No', (a6.cx + 22, 360))
b.arrow([d3.l(), (a5.cx, d3.cy), (a5.cx, a5.b()[1])], 'back', 'Yes', ((a5.cx + d3.l()[0])/2, d3.cy - 18))
c1 = b.node('process', a6.cx, y2 + 170, 150, 56, 'Cancel order')
b.arrow([d3.b(), c1.t()], 'no', 'No', (a6.cx + 22, y2 + 20 + 50 + 30))
e1 = b.node('fail', a7.cx + 110 - 10, y2 + 170, 150, 48, 'Payment failed')
b.arrow([c1.r(), e1.l()])
# notes
b.text(64, 660, '<b>Reading the chart</b>', 13, '#0F172A', w=400)
notes = ['Blue animated line: the main path, the route a successful order takes. One per chart.',
         'Green and rose lines leave decisions as Yes and No. Dashed slate lines go back.',
         'Number chips (1, 2, 3...) name steps so text elsewhere can refer to them; 3a and 5a are branches of steps 3 and 5.',
         'The subprocess (bars at the sides) is its own chart; the document has a wavy bottom.']
for i, t in enumerate(notes): b.text(64, 690 + i*26, t, 12, '#475569')
print(b.save())
