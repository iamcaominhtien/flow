from exlib import *
W, H = 1400, 1340
b = Board('Explainer_Compare', 'Comparison: SQL or NoSQL', W, H, hdr=False)
banner(b, 'SQL or NoSQL?', 'Two ways to store data. Neither is better; they fit different jobs. Read across each row to compare.', W)
LX, RX, CX = 340, 1060, 700
l = xcard(b, LX, 330, 'SQL database', 'Data in tables with fixed columns, linked by keys.', 'Table', 'blue', w=320, h=200)
r = xcard(b, RX, 330, 'NoSQL database', 'Data as flexible documents, each shaped as it needs.', 'JSON', 'green', w=320, h=200)
b.raw(f'<div style="position:absolute;left:{CX-60}px;top:310px;width:120px;height:40px;border-radius:999px;background:#0F172A;color:#fff;font:800 16px/40px Inter,sans-serif;text-align:center">vs</div>')
rows = [('Shape of the data', 'Every row has the same columns.', 'Each document can have its own fields.'),
        ('Changing the shape', 'A planned change to the table, applied to all rows.', 'Just start writing the new field.'),
        ('Links between things', 'Strong: keys and joins keep them consistent.', 'Weak: you repeat data or link it yourself.'),
        ('Growing very large', 'Harder: usually one big machine, then careful splitting.', 'Easier: designed to spread over many machines.'),
        ('Best for', 'Orders, accounts, money: data that must stay exact.', 'Feeds, logs, catalogues: lots of data that changes shape.')]
y0, pit = 520, 124
for i, (lab, a, c) in enumerate(rows):
    cy = y0 + i * pit
    b.raw(f'<div style="position:absolute;left:{CX-110}px;top:{cy-17}px;width:220px;height:34px;border:2px solid #0F172A;border-radius:999px;background:#FFF1DD;box-shadow:0 3px 0 #0F172A;font:800 13.5px/30px Inter,sans-serif;text-align:center;white-space:nowrap;z-index:2">{lab}</div>')
    for x, txt, tone in ((LX, a, 'blue'), (RX, c, 'green')):
        bg, pill = TONES[tone]
        b.raw(f'<div style="position:absolute;left:{x-170}px;top:{cy-44}px;width:340px;height:88px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg};padding:0 20px;display:flex;align-items:center;font-size:14px;line-height:20px;color:#0F172A">{txt}</div>')
    b.raw(f'<div style="position:absolute;left:{CX-0.75}px;top:{cy-62}px;height:124px;border-left:1.5px dashed #94A3B8"></div>')
vy = y0 + 5 * pit - 20
b.rect(64, vy, W - 128, 120, '#fff', '#E2E8F0', 16, dashed=False)
b.text(96, vy + 16, 'Rule of thumb', size=16, color='#0F172A', weight=800)
b.text(96, vy + 46, 'Start with SQL when the data has clear relationships and must stay correct. Add NoSQL beside it when one kind of data is huge or its shape keeps changing. Many systems use both.', size=14, color='#334155', w=1200, lh=22)
print(save3(b))
