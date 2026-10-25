from dfdlib import *
b = Board('DFD_Level2', 'Level 2: inside process 4.0, Deliver order', 2200, 1250,
  'Process 4.0 of level 1 opened into three. Everything that entered or left 4.0 on level 1 still enters or leaves here, from the same neighbours. The dashed store belongs to level 1 and is shown for reference.')
yt, yb = 500, 900
cz = lambda *a: None
b.raw('<div data-lint="box" style="position:absolute;left:450px;top:300px;width:1600px;height:800px;box-sizing:border-box;background:rgba(15,118,110,0.06);border:1.5px dashed #0F766E;border-radius:16px"></div>')
b.raw('<div data-lint="label" style="position:absolute;left:468px;top:1089px;height:22px;padding:0 12px;border-radius:999px;background:#0F766E;color:#fff;font-size:12px;font-weight:700;line-height:22px;white-space:nowrap">4.0 Deliver order</div>')
d1 = store(b, 200, yt, 'D1', 'Orders', 'violet', w=250, ghost=True)
co = ext(b, 1250, 100, 'E3', 'Courier', 'Courier', 'teal', w=360)
p1 = proc(b, 700, yt, '4.1', 'Match courier', 'picks the nearest free courier', 'teal')
p2 = proc(b, 1250, yt, '4.2', 'Offer job', 'sends the job, waits for accept', 'teal')
p3 = proc(b, 1800, yt, '4.3', 'Confirm drop-off', 'checks proof, closes the order', 'teal')
d3 = store(b, 1250, 900, 'D3', 'Courier positions', 'teal', w=300)
b.arrow([d1.r(), p1.l()], 'main', 'Ready order', (365, yt))
b.arrow([p1.r(), p2.l()], 'main', 'Chosen courier', (960, yt))
b.arrow([p2.r(), p3.l()], 'main', 'Accepted job', (1525, p3.cy))
b.arrow([(1190, p2.t()[1]), (1190, co.b()[1])], 'next', 'Delivery job', (1190, 200))
b.arrow([(1310, co.b()[1]), (1310, p2.t()[1])], 'next', 'Job reply, location', (1310, 200))
b.arrow([co.r(), (1800, 100), (1800, p3.t()[1])], 'next', 'Drop-off proof', (1580, 100))
b.arrow([(1230, p2.b()[1]), (1230, d3.t()[1])], 'data', 'Latest position', (1230, 700))
b.arrow([d3.l(), (700, 900), p1.b()], 'data', 'Nearby couriers', (950, 900))
b.arrow([p3.b(), (1800, 1000), (200, 1000), (200, d1.b()[1])], 'data', 'Delivery status', (1450, 1000))
print(save10(b))
