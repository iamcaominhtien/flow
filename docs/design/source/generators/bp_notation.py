from bpmnlib import *
W, H = 1500, 1220
b = Board('BPMN_Notation', 'Notation: the parts of a BPMN diagram', W, H,
  'A small set of shapes covers most processes: events, activities, gateways, flows and containers. Shape tells the kind, tint tells the role.')
def card(x, y, w, h, title):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x + 22, y + 16, title, size=16, color='#0F172A', weight=800)
# events
card(64, 130, 1372, 250, 'Events: something happens')
els = [('start', None, 'Start', 'Where the process begins. Thin green ring.'), ('start', 'message', 'Message start', 'Starts when a message arrives.'), ('intermediate', 'timer', 'Timer', 'Wait, or a deadline. Double amber ring.'),
       ('intermediate', 'message', 'Message', 'Waits for or sends a message.'), ('end', None, 'End', 'Where a path stops. Thick rose ring.'), ('end', 'error', 'Error end', 'The path ends in failure.')]
for i, (k, m, n, t) in enumerate(els):
    cx = 190 + i * 220
    event(b, cx, 220, k, m)
    b.text(cx - 95, 262, n, size=13, color='#0F172A', weight=800, w=190, center=True)
    b.text(cx - 95, 282, t, size=11.5, color='#475569', w=190, center=True, lh=16)
# activities
card(64, 410, 1372, 250, 'Activities: work is done')
acts = [('task', 'Task', 'A single unit of work.', False), ('user', 'User task', 'A person does it.', False), ('service', 'Service task', 'A system does it.', False), ('send', 'Send task', 'Sends a message.', False), ('receive', 'Receive task', 'Waits for a message.', False), ('task', 'Sub-process', 'A task defined elsewhere (+).', True)]
for i, (k, n, t, sp) in enumerate(acts):
    cx = 190 + i * 220
    task(b, cx, 500, n if n != 'Task' else 'Task', k, 150, 64, 'blue', sp)
    b.text(cx - 95, 548, n, size=13, color='#0F172A', weight=800, w=190, center=True)
    b.text(cx - 95, 568, t, size=11.5, color='#475569', w=190, center=True, lh=16)
# gateways
card(64, 690, 680, 250, 'Gateways: the path splits or joins')
gws = [('x', 'Exclusive', 'One exit is taken.'), ('plus', 'Parallel', 'All exits are taken.'), ('o', 'Inclusive', 'One or more exits.'), ('event', 'Event-based', 'First message wins.')]
for i, (k, n, t) in enumerate(gws):
    cx = 140 + i * 160
    gateway(b, cx, 790, k)
    b.text(cx - 70, 828, n, size=13, color='#0F172A', weight=800, w=140, center=True)
    b.text(cx - 70, 848, t, size=11.5, color='#475569', w=140, center=True, lh=16)
# flows
card(770, 690, 666, 250, 'Flows: what connects')
b.arrow([(810, 760), (940, 760)], 'next'); b.text(960, 748, 'Sequence flow', size=13, color='#0F172A', weight=800); b.text(960, 768, 'Order of work inside a pool.', size=11.5, color='#475569')
msgflow(b, [(810, 820), (940, 820)]); b.text(960, 808, 'Message flow', size=13, color='#0F172A', weight=800); b.text(960, 828, 'Between pools. Open circle, open head.', size=11.5, color='#475569')
b.arrow([(810, 880), (940, 880)], 'back'); b.text(960, 868, 'Return', size=13, color='#0F172A', weight=800); b.text(960, 888, 'Dashed slate: loop back or retry.', size=11.5, color='#475569')
b.arrow([(1230, 760), (1380, 760)], 'main'); b.text(1230, 780, 'Main path', size=13, color='#0F172A', weight=800); b.text(1230, 800, 'Blue, animated. One per diagram.', size=11.5, color='#475569', w=190, lh=16)
# containers
card(64, 970, 1372, 220, 'Containers: who does it')
bg, pill = TONES['blue']
b.raw(f'<div style="position:absolute;left:120px;top:1020px;width:360px;height:120px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div><div style="position:absolute;left:120px;top:1020px;width:36px;height:120px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px 0 0 6px;background:{pill};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:12px;font-weight:800">Pool</div></div>')
b.text(500, 1040, 'Pool', size=13, color='#0F172A', weight=800); b.text(500, 1060, 'One participant: a company, a system or a role that takes part. Messages cross between pools.', size=11.5, color='#475569', w=260, lh=16)
lanes_x = 800
b.raw(f'<div style="position:absolute;left:{lanes_x}px;top:1020px;width:360px;height:120px;box-sizing:border-box;border:2px solid #0F172A;border-radius:6px;background:rgba(255,255,255,.75)"></div><div style="position:absolute;left:{lanes_x}px;top:1020px;width:36px;height:60px;box-sizing:border-box;border:2px solid #0F172A;background:{pill};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:11px;font-weight:800">Lane</div></div><div style="position:absolute;left:{lanes_x}px;top:1080px;width:36px;height:60px;box-sizing:border-box;border:2px solid #0F172A;background:{TONES["green"][1]};display:flex;align-items:center;justify-content:center"><div style="writing-mode:vertical-rl;transform:rotate(180deg);font-size:11px;font-weight:800">Lane</div></div><div style="position:absolute;left:{lanes_x}px;top:1080px;width:360px;border-top:2px solid #0F172A"></div>')
b.text(1180, 1040, 'Lane', size=13, color='#0F172A', weight=800); b.text(1180, 1060, 'A role or team inside one pool. Work crosses lanes with sequence flows.', size=11.5, color='#475569', w=230, lh=16)
print(save7(b))
