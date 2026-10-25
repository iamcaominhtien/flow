from bpmnlib import *
from wflib import callout, notes
W, H = 1760, 1450
b = Board('BPMN_Advanced', 'BPMN beyond a flowchart: handling a refund request', W, H,
  'The things BPMN can say and a flowchart cannot: a partner shown only by its name, work done in parallel, a task repeated for each item, deadlines that interrupt or only nudge, and stored data. Numbers point at each.')
X0, X1 = 64, 1700
blackbox(b, X0, 190, X1 - X0, 70, 'Customer  (black-box pool: only the messages it sends and receives are shown)', 'blue')
lanes = [('System', 300, 560, 'violet'), ('Agent', 560, 840, 'blue'), ('Manager', 840, 1160, 'amber')]
b.raw(f'<div data-lint="box" style="position:absolute;left:{X0}px;top:300px;width:{X1-X0}px;height:860px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div>')
for n, y0, y1, tone in lanes:
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{y0}px;width:36px;height:{y1-y0}px;box-sizing:border-box;border:2px solid #0F172A;background:{TONES[tone][1]};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:13px;font-weight:800">{n}</div></div>')
    if y0 != 300: b.raw(f'<div data-lint="edge" style="position:absolute;left:{X0}px;top:{y0}px;width:{X1-X0}px;border-top:2px solid #0F172A"></div>')
yA = 670
st = event(b, 200, yA, 'start', 'message', 'Refund requested')
g1 = gateway(b, 330, yA, 'plus')
cp = task(b, 520, 375, 'Check payment', 'service', 130, 64, 'violet')
cd = task(b, 520, 485, 'Check delivery log', 'service', 150, 64, 'violet')
g2 = gateway(b, 700, yA, 'plus')
g3 = gateway(b, 850, yA, 'x', 'Over $50?')
ap = task(b, 1000, 930, 'Approve refund', 'user', 150, 64, 'amber')
mi = task(b, 1100, yA, 'Refund each item', 'service', 150, 64, 'blue')
cf = task(b, 1330, yA, 'Confirm to customer', 'send', 150, 64, 'blue')
en = event(b, 1500, yA, 'end', None, 'Done')
t1 = boundary(b, 945, 962, 'timer', False); t2 = boundary(b, 1055, 962, 'timer', True)
rm = task(b, 870, 1070, 'Remind manager', 'send', 130, 64, 'amber')
e1 = event(b, 730, 1070, 'end', None, 'Reminded')
e2 = event(b, 1160, 1070, 'end', 'error', 'Escalated')
ds = datastore(b, 1160, 772, 'Payments DB')
multi(b, mi.cx, mi.b()[1])
a = b.arrow
a([st.r(), g1.l()], 'main')
a([g1.t(), (330, 375), cp.l()], 'main'); a([g1.b(), (330, 485)] if False else [(330, 696), (330, 485), cd.l()], 'next') if False else None
a([(330, yA - 26), (330, 375), cp.l()], 'main'); a([(330, yA - 26), (330, 485), cd.l()], 'main')
a([cp.r(), (700, 375), (700, yA - 26)], 'main'); a([cd.r(), (700, 485), (700, yA - 26)], 'main')
a([g2.r(), g3.l()], 'main')
a([g3.r(), mi.l()], 'main', 'no', ((g3.r()[0] + mi.l()[0]) / 2, yA - 14))
a([g3.b(), (850, 930), ap.l()], 'next', 'yes', (850 + 22, 760))
a([ap.r(), (1100, 930), (1100, mi.b()[1])], 'next', 'approved', (1100, 890))
a([mi.r(), cf.l()], 'main'); a([cf.r(), en.l()], 'main')
a([(945, 977), (945, 1070), rm.r()], 'next'); a([rm.l(), e1.r()], 'next')
a([(1055, 977), (1055, 1070), e2.l()], 'no')
assoc(b, [(1160, 702), (1160, 748)])
msgflow(b, [(200, 260), (200, yA - 20)], 'request', (232, 290))
msgflow(b, [(1330, yA - 32), (1330, 260)], 'refund confirmed', (1330, 290))
b.text(560, 1010 - 12, '', size=1)
b.text(886, 1030 if False else 1060, '', size=1)
b.text(1000, 934 + 100, '', size=1)
b.text(820, 1062, 'after 24 h', size=11, color='#92400E', weight=700) if False else None
b.label(945, 1000 - 52, 'after 24 h', 'plain') if False else None
b.text(872, 1008, 'after 24 h', size=11, color='#92400E', weight=700)
b.text(1062, 1008, 'after 72 h', size=11, color='#92400E', weight=700)
for (x, y, n) in [(X0 + 36, 225, 1), (330, yA - 34, 2), (700, yA - 34, 2), (898, yA - 28, 3), (mi.cx + 76, yA - 34, 4), (945 - 20, 944, 5), (1055 + 20, 944, 6), (1330, 400, 7), (1160 - 34, 744, 8)]:
    callout(b, x, y, n)
notes(b, 64, 1190, 1640, [(1, 'Black-box pool', 'A partner we do not model inside. Only its messages touch us.'), (2, 'Parallel split and join', 'Both checks run at the same time. The join waits for both.'),
    (3, 'Exclusive choice', 'Exactly one exit: a refund over $50 needs approval.'), (4, 'Multi-instance task', 'Three bars: done once for each item in the order, in parallel.'),
    (5, 'Timer that nudges', 'Dashed ring: after 24 hours a reminder is sent and the task keeps running.'), (6, 'Timer that interrupts', 'Solid ring: after 72 hours the task is cancelled and the case escalates.'),
    (7, 'Message flow', 'Confirmation goes back to the customer across the pool border.'), (8, 'Data store', 'A system that holds data. A dotted line shows which task reads or writes it.')], cols=4, gap=6)
print(save7(b))
