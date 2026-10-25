from bpmnlib import *
W, H = 1500, 930
b = Board('BPMN_Basic', 'Basic BPMN: approving an expense', W, H,
  'One pool with three lanes, one per role. The flow starts top left, crosses lanes where a hand-over happens, and splits at a decision. A dashed arrow returns work for a fix.')
PX0, PX1, PY = 64, 1436, 190
lanes = [('Employee', 'blue'), ('Manager', 'violet'), ('Finance', 'green')]
LH = 210
b.raw(f'<div data-lint="box" style="position:absolute;left:{PX0}px;top:{PY}px;width:{PX1-PX0}px;height:{LH*3}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div>')
for i, (n, tone) in enumerate(lanes):
    y = PY + i * LH
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{PX0}px;top:{y}px;width:36px;height:{LH}px;box-sizing:border-box;border:2px solid #0F172A;background:{pill};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:13px;font-weight:800">{n}</div></div>')
    if i: b.raw(f'<div data-lint="edge" style="position:absolute;left:{PX0}px;top:{y}px;width:{PX1-PX0}px;border-top:2px solid #0F172A"></div>')
y1, y2, y3 = PY + 105, PY + LH + 105, PY + 2 * LH + 105
s = event(b, 190, y1, 'start', None, 'Expense incurred')
sub = task(b, 360, y1, 'Submit expense', 'user', 140, 64, 'blue')
rv = task(b, 360, y2, 'Review expense', 'user', 140, 64, 'violet')
gw = gateway(b, 560, y2, 'x', 'Approved?', lpos='below')
fx = task(b, 740, y1, 'Fix and resubmit', 'user', 150, 64, 'blue')
pay = task(b, 780, y3, 'Pay employee', 'service', 140, 64, 'green')
pe = event(b, 960, y3, 'end', None, 'Paid')
a = b.arrow
a([s.r(), sub.l()], 'main'); a([sub.b(), rv.t()], 'main'); a([rv.r(), gw.l()], 'main')
a([gw.r(), (780, y2), (780, pay.t()[1])], 'main', 'yes', (800, y2 + 34))
a([pay.r(), pe.l()], 'main')
a([gw.t(), (560, y1), fx.l()], 'no', 'no', (560 + 22, y1 + 34))
a([fx.t(), (fx.cx, y1 - 70), (sub.cx, y1 - 70), sub.t()], 'back', 'fix and resubmit', ((sub.cx + fx.cx) / 2, y1 - 70))
b.raw(f'<div style="position:absolute;left:64px;top:{PY+LH*3+30}px;width:1300px;font-size:12.5px;line-height:19px;color:#475569"><b style="color:#0F172A">Reading it.</b> Each lane is a role, not a person. A task is a unit of work, written as verb and noun. The diamond with a cross is an exclusive choice: exactly one exit is taken.</div>')
print(save7(b))
