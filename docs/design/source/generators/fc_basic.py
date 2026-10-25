from fclib import *
# ---- Basic: vertical login flow ----
b = Board('Flowchart_Basic', 'Basic flowchart: top to bottom', 1160, 900,
  'A login flow. Steps run down, the happy path stays in one straight column, exceptions branch to the right, and the retry loop returns above the flow as a dashed line.')
cx, cx2 = 330, 720
st  = b.node('terminator', cx, 200, 150, 48, 'Start')
io  = b.node('io', cx, 306, 190, 56, 'Enter email and password')
pr  = b.node('process', cx, 412, 170, 56, 'Check credentials')
d1  = b.node('decision', cx, 540, 170, 100, 'Valid?')
ss  = b.node('process', cx, 686, 170, 56, 'Create session')
en  = b.node('terminator', cx, 794, 150, 48, 'Open dashboard')
d2  = b.node('decision', cx2, 540, 190, 100, 'Fewer than 3 attempts?', fs=12)
lk  = b.node('process', cx2, 686, 170, 56, 'Lock account')
lk2 = b.node('terminator', cx2, 794, 150, 48, 'Show lock notice', tone='fail')
# replace last with fail colour: redraw as fail kind
b.parts.pop(); b.node('fail', cx2, 794, 150, 48, 'Show lock notice')
b.arrow([st.b(), io.t()]); b.arrow([io.b(), pr.t()]); b.arrow([pr.b(), d1.t()])
b.arrow([d1.b(), ss.t()], 'yes', 'Yes', (cx + 22, 612))
b.arrow([ss.b(), en.t()])
b.arrow([d1.r(), d2.l()], 'no', 'No', ((d1.r()[0]+d2.l()[0])/2, 540-0))
b.arrow([d2.b(), lk.t()], 'no', 'No', (cx2 + 22, 612))
b.arrow([lk.b(), (cx2, 770)])
b.arrow([d2.t(), (cx2, 306), (io.r()[0], 306)], 'back', 'Yes, retry', (cx2, 400))
# legend card
lx, ly = 900, 150
b.raw(f'<div style="position:absolute;left:{lx}px;top:{ly}px;width:196px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:16px 16px"><div style="font-size:13px;font-weight:700;margin-bottom:12px">Line roles</div>'
      + ''.join(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;font-size:12px;color:#334155"><span style="width:30px;border-top:2px {"dashed" if dash else "solid"} {col}"></span>{t}</div>' for col, dash, t in [(INK, 0, 'Next step'), ('#15803D', 0, 'Yes, success'), ('#B42318', 0, 'No, failure'), (SLATE, 1, 'Retry or return')]) + '</div>')
print(b.save())
