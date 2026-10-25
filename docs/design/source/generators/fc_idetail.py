import json
from fclib import *
from fcdetail import detail, D
flat = json.load(open('icons.json'))['groups']
ALIAS = {'Containers': 'Container', 'Serverless function': 'Function', 'Object storage': 'Bucket', 'SQL database': 'Database', 'In-memory cache': 'Cache',
         'API gateway': 'Gateway', 'Message queue': 'Queue', 'Pub / Sub topic': 'Pub / Sub', 'Email service': 'Email', 'Firewall / WAF': 'Firewall', 'CI / CD': 'Pipeline'}
def src(n): return ALIAS.get(n, n)
groups = [(g['name'], [i['name'] for i in g['icons']]) for g in flat]
groups.append(('Extras for delivery and commerce', ['Restaurant', 'Pot', 'Courier', 'Card', 'Refund']))
missing = [n for g, l in groups for n in l if src(n) not in D]
assert not missing, missing
CW, CH = 144, 132
def rows(l): return (len(l) + 7) // 8
total = sum(len(l) for _, l in groups)
uniq = len({src(n) for _, l in groups for n in l})
H = 340 + sum(56 + rows(l) * CH + 20 for _, l in groups) + 250
b = Board('Icons_Detailed', 'Detailed icons', 1280, H,
  f'A second icon style for illustrated mode. The same subjects as the flat set, with a shaded side, a highlight, small accents and a ground shadow, in the same palette. Every icon of the flat set has a detailed version ({uniq} drawings; cloud service icons that match a generic icon reuse it).')
b.rect(64, 150, 1152, 170, '#FFFFFF', '#E2E8F0', 14, False)
b.text(88, 168, 'Style rules', 16, '#0F172A', 800)
b.raw('<ul style="position:absolute;left:88px;top:198px;width:640px;margin:0;padding-left:18px;font-size:13px;line-height:20px;color:#334155"><li style="margin-bottom:4px">64 grid, 2.5 px ink outline, round joins, same ink and palette as the flat icons.</li><li style="margin-bottom:4px">Three tones per object: base, a darker shade on the side away from the light, a white highlight stroke.</li><li style="margin-bottom:4px">One or two small accents in palette colours: a badge, steam, a sparkle.</li><li style="margin-bottom:4px">A soft ground shadow under every object.</li><li>Readable at 56 px: no detail thinner than 2 px.</li></ul>')
b.text(780, 168, 'Size ladder', 16, '#0F172A', 800)
x = 780
for sz in (32, 48, 64, 96):
    b.raw(detail('Package', sz, x, 290 - sz - 14)); b.text(x, 292, f'{sz}', 11, '#64748B', mono=True); x += sz + 26
y = 340
for name, ics in groups:
    h = 56 + rows(ics) * CH
    b.rect(64, y, 1152, h, '#FFFFFF', '#E2E8F0', 14, False)
    b.text(88, y + 18, name, 16, '#0F172A', 800); b.text(88 + 16 + len(name) * 9, y + 22, f'{len(ics)} icons', 12, '#64748B')
    for i, n in enumerate(ics):
        cx, cy = 64 + (i % 8) * CW, y + 52 + (i // 8) * CH
        s = src(n)
        b.raw(detail(s, 80, cx + 32, cy + 6))
        b.text(cx, cy + 96, n, 12, '#334155', w=CW, center=True)
        if s != n: b.text(cx, cy + 112, f'same as {s}', 10.5, '#94A3B8', w=CW, center=True)
    y += h + 20
b.rect(64, y, 1152, 210, '#FFFFFF', '#E2E8F0', 14, False)
b.text(88, y + 18, 'The same card with each icon style', 16, '#0F172A', 800)
TONE = {'P': ('#FFF1DD', '#FFD9A3'), 'K': ('#D3F3EF', '#A8E6DE')}
for j, (style, label) in enumerate([('flat', 'Flat icon'), ('detail', 'Detailed icon')]):
    x0 = 88 + j * 560
    b.text(x0, y + 58, f'<b>{label}</b>', 13, '#0F172A')
    b.card(x0 + 116, y + 128, 'Capture payment', 'Take the held money', 'Money', TONE['P'], style=style)
    b.card(x0 + 116 + 250, y + 128, 'Pick up', 'Collect it at the restaurant', 'Restaurant', TONE['K'], style=style)
print(b.save(y + 250), total, uniq)
