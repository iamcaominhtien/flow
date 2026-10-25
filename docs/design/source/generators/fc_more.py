from fclib import *
out = []
# ---- Horizontal ----
b = Board('Flowchart_Horizontal', 'Horizontal flowchart: left to right', 1560, 620,
  'Use left to right for pipelines and processes that read like a timeline. The same rules apply: the happy path stays on one centre line, exceptions drop below, and an off-page connector marks where a branch continues elsewhere.')
y = 260
s1 = b.node('terminator', 139, y, 150, 48, 'Order placed')
s2 = b.node('process', 359, y, 150, 56, 'Check stock')
s3 = b.node('decision', 599, y, 170, 100, 'In stock?')
s4 = b.node('process', 849, y, 150, 56, 'Pack items')
s5 = b.node('process', 1069, y, 150, 56, 'Ship order')
s6 = b.node('terminator', 1299, y, 160, 48, 'Order delivered')
n1 = b.node('process', 599, 440, 160, 56, 'Notify customer')
c1 = b.node('connector', 849, 440, 38, 38, 'A', fs=13)
for a, c in [(s1, s2), (s2, s3)]: b.arrow([a.r(), c.l()])
b.arrow([s3.r(), s4.l()], 'yes', 'Yes', ((s3.r()[0]+s4.l()[0])/2, y-18))
b.arrow([s4.r(), s5.l()]); b.arrow([s5.r(), s6.l()])
b.arrow([s3.b(), n1.t()], 'no', 'No', (599+22, 342))
b.arrow([n1.r(), c1.l()])
b.text(885-0, 430, 'Continues in <b>Back-order handling</b>, connector A', 12, '#475569')
b.text(64, 540, 'Off-page connector: a rose circle with a letter. The same letter appears at the start of the next chart.', 12, '#475569')
out.append(b.save())

# ---- Swimlane ----
b = Board('Flowchart_Swimlane', 'Swimlane flowchart: who does what', 1160, 800,
  'Lanes show who is responsible. Every step sits in exactly one lane, arrows that change lane run straight across, and the flow reads left to right inside the lanes.')
X0, X1 = 64, 1096; top = 150; LH = 190
lanes = [('Customer', '#EFF6FF', '#BFDBFE', '#1D4ED8'), ('Support', '#F3F1FD', '#D4CEF7', '#5B4BD6'), ('Finance', '#F0FBF2', '#BBE7C4', '#15803D')]
for i, (nm, bg, bd, fg) in enumerate(lanes):
    yy = top + i * LH
    b.raw(f'<div data-lint="box" style="position:absolute;left:{X0}px;top:{yy}px;width:{X1-X0}px;height:{LH}px;box-sizing:border-box;background:{bg};border:1.5px solid {bd}"></div>')
    b.raw(f'<div style="position:absolute;left:{X0}px;top:{yy}px;width:44px;height:{LH}px;box-sizing:border-box;background:{fg};display:flex;align-items:center;justify-content:center"><span style="writing-mode:vertical-rl;transform:rotate(180deg);color:#fff;font-size:13px;font-weight:700;letter-spacing:.02em">{nm}</span></div>')
cyC, cyS, cyF = top + LH//2, top + LH + LH//2, top + 2*LH + LH//2
c1 = b.node('terminator', 260, cyC, 160, 48, 'Request refund')
s1 = b.node('process', 260, cyS, 160, 56, 'Review request')
s2 = b.node('decision', 520, cyS, 170, 100, 'Eligible?')
s3 = b.node('process', 790, cyS, 160, 56, 'Send rejection')
c2 = b.node('terminator', 790, cyC, 170, 48, 'Rejection received')
f1 = b.node('process', 520, cyF, 160, 56, 'Issue refund')
f2 = b.node('fail', 520, cyF, 10, 10) if False else None
f2 = b.node('terminator', 790, cyF, 160, 48, 'Refund sent')
b.arrow([c1.b(), s1.t()]); b.arrow([s1.r(), s2.l()])
b.arrow([s2.b(), f1.t()], 'yes', 'Yes', (542, cyS + 76))
b.arrow([s2.r(), s3.l()], 'no', 'No', (655, cyS - 16))
b.arrow([s3.t(), c2.b()]); b.arrow([f1.r(), f2.l()])
b.text(64, top + 3*LH + 24, 'Lane order follows the first hand-off: the actor who starts the process goes on top. A lane never holds a decision for someone else.', 12, '#475569')
out.append(b.save())
for o in out: print(o)
