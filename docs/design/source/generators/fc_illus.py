from fclib import *
from fcicons import icon as bigicon
from fcdetail import detail
b = Board('Flowchart_Illustrated', 'Illustrated nodes', 1280, 1700,
  'An optional richer style for work steps: a name pill, one line of explanation and a large icon on a card tinted by its lane. Use it for the steps that matter or when the chart is for people outside the team. Plain nodes stay the default.')
TONE = {'Customer': ('#DCEEFB', '#BFDBFE'), 'App and server': ('#E6E3FB', '#CFC8F7'), 'Payment': ('#FFF1DD', '#FFD9A3'), 'Restaurant': ('#DCF5E1', '#B5EBC1'), 'Courier': ('#D3F3EF', '#A8E6DE')}
def panel(y, h, title):
    b.rect(64, y, 1152, h, '#FFFFFF', '#E2E8F0', 14, False)
    b.text(88, y + 20, title, 16, '#0F172A', 800)
def num(x, y, n):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:22px;height:22px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:700 12px/22px \'JetBrains Mono\',monospace;text-align:center">{n}</div>')
def bullets(x, y, items, w=520, gap=8):
    b.raw(f'<ul style="position:absolute;left:{x}px;top:{y}px;width:{w}px;margin:0;padding-left:18px;font-size:13px;line-height:20px;color:#334155">' + ''.join(f'<li style="margin-bottom:{gap}px">{t}</li>' for t in items) + '</ul>')
# 1 anatomy
panel(150, 270, 'Anatomy of a card')
b.card(268, 300, 'Authorize card', 'Check the card, hold the money', 'Card', TONE['Payment'], style='detail')
for (x, y, n) in [(150, 266, 1), (150, 316, 2), (368, 286, 3), (152, 250, 4)]: pass
b.raw('<div style="position:absolute;left:172px;top:220px"></div>')
num(124, 262, 1); num(124, 304, 2); num(396, 304, 3); num(124, 340, 4)
cal = [('1', 'Name pill', 'Verb and noun, three words at most. Bold, ink outline and a 3 px shadow. Tinted a step darker than the card.'),
       ('2', 'One line of explanation', 'Six words or fewer, slate, 11.5 px. Says what happens, not how.'),
       ('3', 'Icon', '64 px, from the detailed set on the Icons page, chosen for the noun: Card for payment, Cart for order. Flat icons (56 px) are the fallback.'),
       ('4', 'Card', '232 × 96, 2 px ink border, radius 12, tinted by lane. Side bars inside the border make it a subprocess.')]
for i, (n, t, d) in enumerate(cal):
    y = 190 + i * 52
    num(560, y + 2, n); b.text(594, y, f'<b>{t}</b>', 13, '#0F172A'); b.text(594, y + 20, d, 12, '#475569', w=590, lh=16)
# 2 levels
panel(440, 270, 'Three levels of the same step')
b.node('process', 214, 580, 170, 56, 'Authorize card')
b.node('process', 214 + 380, 580, 190, 56, 'Authorize card', icon='card')
b.card(214 + 790, 580, 'Authorize card', 'Check the card, hold the money', 'Card', TONE['Payment'], bars=True, style='detail')
for x, t, d in [(130, '1 · Text', 'Default. Every step, and all drafts.'), (510, '2 · Small icon', 'The kind of work shows at a glance.'), (900, '3 · Illustrated card', 'The steps people must notice, or charts for non-specialists.')]:
    b.text(x, 640, f'<b>{t}</b>', 13, '#0F172A'); b.text(x, 660, d, 12, '#475569', w=300, lh=16)
b.text(88, 482, 'Levels mix in one chart, as fidelity levels do in Screen flow. Upgrading a step changes its size, so leave room (see spacing).', 12, '#475569', w=1000)
# 3 lane colours and shapes
panel(730, 360, 'Lane colours, and which shapes become cards')
for i, (n, (bg, pb)) in enumerate(TONE.items()):
    y = 790 + i * 52
    b.raw(f'<div style="position:absolute;left:88px;top:{y}px;width:46px;height:34px;box-sizing:border-box;border:2px solid #0F172A;border-radius:8px;background:{bg}"></div>')
    b.raw(f'<div style="position:absolute;left:140px;top:{y+9}px;width:46px;height:16px;box-sizing:border-box;border:2px solid #0F172A;border-radius:999px;background:{pb}"></div>')
    b.text(204, y + 6, f'<b>{n}</b>', 13, '#0F172A'); b.text(340, y + 8, f'<span style="font-family:JetBrains Mono,monospace">{bg} · {pb}</span>', 12, '#475569')
b.text(88, 1056, 'Outside lanes, use the tone of the owner. No lanes: one tone per group of related steps.', 12, '#475569', w=560)
rows = [('process', 'Process, input / output, document, preparation', 'become a card; the icon says which'), ('subprocess', 'Subprocess', 'card with side bars'), ('decision', 'Decision', 'stays a diamond, text only'), ('terminator', 'Start and end', 'stay pills, small icon allowed'), ('connector', 'Connector', 'stays a circle')]
for i, (k, t, d) in enumerate(rows):
    y = 790 + i * 52
    if k == 'process': b.raw(f'<div style="position:absolute;left:700px;top:{y}px;width:52px;height:34px;box-sizing:border-box;border:2px solid #0F172A;border-radius:7px;background:#DCEEFB"><div style="position:absolute;left:5px;top:6px;width:20px;height:8px;border:1.5px solid #0F172A;border-radius:99px;background:#BFDBFE"></div></div>')
    elif k == 'subprocess': b.raw(f'<div style="position:absolute;left:700px;top:{y}px;width:52px;height:34px;box-sizing:border-box;border:2px solid #0F172A;border-radius:7px;background:#FFF1DD"><div style="position:absolute;left:4px;top:1px;bottom:1px;width:1.5px;background:#0F172A"></div><div style="position:absolute;right:4px;top:1px;bottom:1px;width:1.5px;background:#0F172A"></div></div>')
    else:
        b.raw(f'<div style="position:absolute;left:700px;top:{y}px;width:52px;height:34px">{shape_svg(k, 52, 34) if k!="connector" else shape_svg(k, 34, 34)}</div>')
    b.text(770, y, f'<b>{t}</b>', 13, '#0F172A', w=420); b.text(770, y + 18, d, 12, '#475569', w=420)
# 4 icons
panel(1110, 330, 'Choosing icons')
bullets(88, 1156, ['Match the noun, not the verb: Card for authorize card, Restaurant for pick up.', 'One icon per card. Never two, never an icon that only decorates.', 'The same thing gets the same icon everywhere in the chart.', 'Take icons from the detailed set on the Icons page. If none fits, draw one in the same style: 64 grid, 2.5 px ink outline, three tones.', 'Icons are optional. A card without an icon is allowed, but keep its text width.'], 520, 6)
names = ['Card', 'Restaurant', 'Pot', 'Courier', 'Refund', 'Database', 'Server', 'Mobile', 'Cart', 'Region', 'Bell', 'Package']
b.text(660, 1156, '<b>Detailed set</b>, 12 of 45 shown', 12, '#475569')
for i, n in enumerate(names):
    x = 660 + (i % 6) * 90; y = 1190 + (i // 6) * 110
    b.raw(detail(n, 60, x + 6, y)); b.text(x, y + 66, n, 11, '#334155', center=True, w=72)
# 5 spacing
panel(1460, 210, 'Spacing')
bullets(88, 1506, ['Card 232 × 96 with a 64 px icon. Plain node 160 × 56. Screen card 150 × 92 with a Mobile icon.', 'Gap between cards in a row: 90 px or more, 130 px when a trigger chip sits on the arrow.', 'Lane height: 240 px with cards, 210 px with plain nodes. A lane holding both uses 240.', 'Vertical gap between rows of cards: 56 px or more.', 'Fork and join bars span the lanes they split and sit 90 px from the cards they feed.'], 1000, 6)
print(b.save())
