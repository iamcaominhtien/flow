from fslib import *
CW, CH, GX, GY = 640, 400, 32, 28
b = Board('Sequence_Fragments', 'Fragments: alt, opt, loop, par, break, critical, ref', 1400, 64 + 120 + 4 * (CH + GY),
  'A frame groups messages and says when they happen. Its tag names the kind, the guard in brackets says under which condition. Frames sit behind the lifelines and may nest.')
def cell(i, title, desc):
    col, row = i % 2, i // 2
    x0, y0 = 64 + col * (CW + GX), 150 + row * (CH + GY)
    b.raw(f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{CW}px;height:{CH}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x0 + 22, y0 + 16, title, size=16, color='#0F172A', weight=800)
    b.text(x0 + 22, y0 + 40, desc, size=12, color='#475569')
    return x0, y0
def seq(x0, y0, names, tones=('gray', 'blue', 'violet'), icons=('user', 'box', 'doc')):
    xs = [x0 + 120, x0 + 320, x0 + 520][:len(names)]
    P = [dict(key=str(i), label=n, x=xs[i], icon=icons[i], tone=tones[i]) for i, n in enumerate(names)]
    return Seq(b, P, y0 + 64, y0 + CH - 14), xs

# 1 alt
x0, y0 = cell(0, 'alt: one of several', 'Exactly one branch runs. A dashed line separates the branches; the last is [else].')
s, xs = seq(x0, y0, ['Shop', 'Payment'])
fy = y0 + 150
s.frame('alt', x0 + 50, x0 + 400, fy, fy + 200, '[card accepted]', div=[(fy + 112, '[else]')])
s.msg('0', '1', y0 + 138, 'Charge card', num=1)
s.msg('1', '0', fy + 52, 'Receipt', kind='ret', num='2a')
s.msg('1', '0', fy + 152, 'Declined', kind='ret', role='fail', num='2b')
s.draw()
# 2 opt
x0, y0 = cell(1, 'opt: may or may not happen', 'One branch with a guard. When the guard is false, nothing in the frame runs.')
s, xs = seq(x0, y0, ['Shop', 'Coupons', 'Payment'])
fy = y0 + 150
s.frame('opt', x0 + 50, x0 + 590, fy, fy + 150, '[has coupon code]')
s.msg('0', '1', fy + 54, 'Check code')
s.msg('0', '2', fy + 104, 'Apply discount')
s.msg('0', '2', y0 + 328, 'Charge total', num=1)
s.draw()
# 3 loop
x0, y0 = cell(2, 'loop: repeat', 'Repeats while the guard is true. Write the stop condition, or the count: [3 times].')
s, xs = seq(x0, y0, ['Worker', 'API'])
fy = y0 + 150
s.frame('loop', x0 + 50, x0 + 400, fy, fy + 150, '[until status = done]')
s.msg('0', '1', fy + 54, 'Get status')
s.msg('1', '0', fy + 104, 'pending', kind='ret')
s.msg('0', '1', y0 + 328, 'Download result', num=1)
s.draw()
# 4 par
x0, y0 = cell(3, 'par: at the same time', 'Branches run in parallel, separated by a dashed line. Order inside a branch still counts.')
s, xs = seq(x0, y0, ['Order', 'Kitchen', 'Courier'], ('blue', 'green', 'teal'), ('doc', 'pot', 'bike'))
fy = y0 + 150
s.frame('par', x0 + 50, x0 + 590, fy, fy + 190, '', div=[(fy + 100, '')])
s.msg('0', '1', fy + 54, 'Start cooking', role='main')
s.msg('0', '2', fy + 146, 'Find a courier', role='main')
s.draw()
# 5 break
x0, y0 = cell(4, 'break: leave the flow', 'If the guard holds, the frame runs and the rest of the diagram is skipped.')
s, xs = seq(x0, y0, ['Shop', 'Stock', 'Payment'])
fy = y0 + 170
s.msg('0', '1', y0 + 138, 'Reserve item', num=1)
s.frame('break', x0 + 50, x0 + 400, fy, fy + 100, '[out of stock]')
s.msg('1', '0', fy + 56, 'Sold out', kind='ret', role='fail', num='2a')
s.msg('0', '2', y0 + 326, 'Charge card', num=3)
s.draw()
# 6 critical
x0, y0 = cell(5, 'critical: no interruption', 'The messages inside must finish as one unit: a lock, a transaction, a payment capture.')
s, xs = seq(x0, y0, ['Shop', 'Stock'])
fy = y0 + 150
s.frame('critical', x0 + 50, x0 + 400, fy, fy + 150, '[lock stock row]')
s.msg('0', '1', fy + 54, 'Decrease stock')
s.msg('1', '0', fy + 104, 'new count', kind='ret')
s.msg('0', '1', y0 + 328, 'Release lock', kind='async', num=1)
s.draw()
# 7 ref
x0, y0 = cell(6, 'ref: use another diagram', 'Points to a sequence diagram by name. Keeps long flows readable; the plugin can link it.')
s, xs = seq(x0, y0, ['App', 'API', 'Payment'], ('blue', 'violet', 'amber'), ('phone', 'box', 'card'))
fy = y0 + 150
s.msg('0', '1', y0 + 128, 'Open cart', num=1)
s.frame('ref', x0 + 70, x0 + 580, fy, fy + 90, '')
b.text(x0 + 70, fy + 36, 'Sign in', size=13, color='#0F172A', weight=700, w=510, center=True)
s.msg('1', '2', y0 + 292, 'Charge card', num=2)
s.draw()
# 8 nested
x0, y0 = cell(7, 'Nested frames', 'A frame lives inside another one, inset by 10 px on each side. Two levels is enough.')
s, xs = seq(x0, y0, ['Worker', 'Gateway', 'Provider'], ('blue', 'violet', 'amber'), ('doc', 'box', 'card'))
fy = y0 + 130
s.frame('loop', x0 + 40, x0 + 600, fy, fy + 240, '[up to 3 attempts]')
s.frame('alt', x0 + 50, x0 + 590, fy + 36, fy + 230, '[provider answers]', div=[(fy + 150, '[timeout]')])
s.msg('0', '1', fy + 82, 'Send request')
s.msg('1', '2', fy + 118, 'Call provider')
s.msg('1', '0', fy + 192, 'wait 2 s', kind='ret', role='fail')
s.draw()
print(save(b))
