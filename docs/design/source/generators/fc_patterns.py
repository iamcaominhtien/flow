from fclib import *
CW, CH, G, M = 384, 330, 24, 64
b = Board('Flowchart_Patterns', 'Flowchart patterns', M*2 + 3*CW + 2*G, 150 + 3*CH + 2*G + 64,
  'The small structures every flowchart is built from. A plugin picks one of these for each part of a process, then fills in the text.')
def card(i, title, desc):
    c, r = i % 3, i // 3
    x, y = M + c * (CW + G), 150 + r * (CH + G)
    b.rect(x, y, CW, CH, '#FFFFFF', '#E2E8F0', 14, False)
    b.text(x + 20, y + 16, title, 14, '#0F172A', 700)
    b.text(x + 20, y + 42, desc, 12, '#475569', 400, w=CW - 40, lh=18)
    return x, y + 100
def N(o, kind, cx, cy, t='', w=92, h=40, fs=12): return b.node(kind, o[0] + cx, o[1] + cy, w, h, t, fs=fs)
def pt(o, x, y): return (o[0] + x, o[1] + y)
# 0 sequence
o = card(0, 'Sequence', 'Steps in order, one arrow between neighbours. The simplest block.')
a = N(o, 'process', 62, 90, 'Step A'); c = N(o, 'process', 192, 90, 'Step B'); d = N(o, 'process', 322, 90, 'Step C')
b.arrow([a.r(), c.l()]); b.arrow([c.r(), d.l()])
# 1 branch and merge
o = card(1, 'Branch and merge', 'A decision splits the flow, and both branches meet again at the next step.')
D = N(o, 'decision', 62, 100, 'Test?', 92, 64)
A = N(o, 'process', 196, 40, 'Do A', 84); B = N(o, 'process', 196, 160, 'Do B', 84); Mg = N(o, 'process', 326, 100, 'Next', 64)
b.arrow([D.t(), pt(o, 62, 40), A.l()], 'yes', 'Yes', pt(o, 100, 40 - 15))
b.arrow([D.b(), pt(o, 62, 160), B.l()], 'no', 'No', pt(o, 100, 160 + 15))
b.arrow([A.r(), pt(o, 326, 40), Mg.t()]); b.arrow([B.r(), pt(o, 326, 160), Mg.b()])
# 2 loop
o = card(2, 'Loop (repeat until)', 'The return line is dashed slate and runs below the flow, back into the step.')
T = N(o, 'process', 62, 70, 'Try step', 88); D = N(o, 'decision', 192, 70, 'Done?', 92, 64)
E = N(o, 'terminator', 324, 70, 'Exit', 72, 32)
b.arrow([T.r(), D.l()]); b.arrow([D.r(), E.l()], 'yes', 'Yes', pt(o, 262, 70 - 16))
b.arrow([D.b(), pt(o, 192, 150), pt(o, 62, 150), T.b()], 'back', 'No, try again', pt(o, 127, 150))
# 3 multi-way
o = card(3, 'Multi-way decision', 'Three or more exits: label each with its value and keep an else exit last.')
D = N(o, 'decision', 68, 90, 'Plan?', 96, 64)
X0 = N(o, 'process', 290, 20, 'Free', 92, 34); X1 = N(o, 'process', 290, 90, 'Pro', 92, 34); X2 = N(o, 'process', 290, 160, 'Other', 92, 34)
b.arrow([D.t(), pt(o, 68, 20), X0.l()], 'next', 'Free', pt(o, 150, 20 - 14))
b.arrow([D.r(), X1.l()], 'next', 'Pro', pt(o, 170, 90 - 14))
b.arrow([D.b(), pt(o, 68, 160), X2.l()], 'next', 'else', pt(o, 150, 160 + 14))
# 4 parallel
o = card(4, 'Parallel split and join', 'A thick bar splits the flow into steps that run together, and a second bar joins them.')
S = N(o, 'process', 192, 12, 'Start work', 100, 30)
b.raw(f'<div style="position:absolute;left:{o[0]+92}px;top:{o[1]+44}px;width:200px;height:6px;border-radius:3px;background:#0F172A"></div>')
PA = N(o, 'process', 130, 100, 'Task A', 92, 34); PB = N(o, 'process', 254, 100, 'Task B', 92, 34)
b.raw(f'<div style="position:absolute;left:{o[0]+92}px;top:{o[1]+150}px;width:200px;height:6px;border-radius:3px;background:#0F172A"></div>')
Z = N(o, 'process', 192, 190, 'Continue', 100, 30)
b.arrow([S.b(), pt(o, 192, 44)])
b.arrow([pt(o, 130, 50), PA.t()]); b.arrow([pt(o, 254, 50), PB.t()])
b.arrow([PA.b(), pt(o, 130, 150)]); b.arrow([PB.b(), pt(o, 254, 150)])
b.arrow([pt(o, 192, 156), Z.t()])
# 5 error handling
o = card(5, 'Error handling', 'Failure exits go down in rose and end in their own rose terminator.')
Cl = N(o, 'process', 52, 60, 'Call API', 84); D = N(o, 'decision', 168, 60, 'OK?', 84, 60)
Nx = N(o, 'process', 304, 60, 'Continue', 84)
Lg = N(o, 'process', 168, 150, 'Log error', 84, 36); Ab = N(o, 'fail', 304, 150, 'Abort', 84, 32)
b.arrow([Cl.r(), D.l()]); b.arrow([D.r(), Nx.l()], 'yes', 'Yes', pt(o, 236, 60 - 16))
b.arrow([D.b(), Lg.t()], 'no', 'No', pt(o, 190, 110)); b.arrow([Lg.r(), Ab.l()])
# 6 subprocess
o = card(6, 'Subprocess', 'A step with side bars stands for a chart of its own. Draw that chart separately, with the same name.')
P1 = N(o, 'process', 52, 30, 'Receive', 84, 36); Sb = N(o, 'subprocess', 192, 30, 'Validate order', 120, 40, 11); P3 = N(o, 'process', 334, 30, 'Store', 64, 36)
b.arrow([P1.r(), Sb.l()]); b.arrow([Sb.r(), P3.l()])
b.rect(o[0] + 20, o[1] + 80, 344, 110, '#F8FAFC', '#94A3B8', 12)
b.pill(o[0] + 32, o[1] + 72, 'Validate order', '#0F172A', w=112)
t1 = N(o, 'terminator', 78, 140, 'Start', 76, 30, 11); t2 = N(o, 'process', 192, 140, 'Check lines', 88, 34, 11); t3 = N(o, 'terminator', 308, 140, 'Return', 76, 30, 11)
b.arrow([t1.r(), t2.l()]); b.arrow([t2.r(), t3.l()])
# 7 off-page connector
o = card(7, 'Off-page connector', 'A lettered circle ends one chart and the same letter starts the next.')
b.rect(o[0] + 8, o[1] + 8, 170, 170, '#F8FAFC', '#CBD5E1', 10, False)
b.rect(o[0] + 198, o[1] + 8, 170, 170, '#F8FAFC', '#CBD5E1', 10, False)
b.text(o[0] + 16, o[1] + 14, 'Page 1', 11, '#64748B', 600); b.text(o[0] + 206, o[1] + 14, 'Page 2', 11, '#64748B', 600)
q1 = N(o, 'process', 93, 60, 'Last step', 100, 36); k1 = N(o, 'connector', 93, 140, 'A', 34, 34, 13)
k2 = N(o, 'connector', 283, 60, 'A', 34, 34, 13); q2 = N(o, 'process', 283, 140, 'First step', 100, 36)
b.arrow([q1.b(), k1.t()]); b.arrow([k2.b(), q2.t()])
# 8 data and documents
o = card(8, 'Data in and out', 'Parallelograms are data entering or leaving. A document is an output people read.')
i1 = N(o, 'io', 66, 90, 'Read file', 108, 40); pr = N(o, 'process', 192, 90, 'Process', 80, 40); dc = N(o, 'document', 318, 90, 'Report', 84, 46)
b.arrow([i1.r(), pr.l()]); b.arrow([pr.r(), dc.l()])
print(b.save())
