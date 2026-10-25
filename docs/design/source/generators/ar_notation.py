from archlib import *
b = Board('Architecture_Notation', 'Notation: components, lines, zones', 1280, 1020,
  'How to read one box, one line and one frame. The same pieces are used in every architecture diagram.')
def card(x, y, w, h, title):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x + 22, y + 18, title, size=16, color='#0F172A', weight=800)
# A components
card(64, 130, 1152, 330, 'Components')
comp(b, 200, 250, 'Order service', 'checkout, status', 'Server', 'violet')
comp(b, 200, 380, 'Order service', 'checkout, status', 'Server', 'violet', 'detail')
b.text(340, 232, 'Plain', size=13, color='#0F172A', weight=800); b.text(340, 252, '196 × 68. Flat icon, name, one line of detail.', size=12, color='#475569')
b.text(340, 352, 'Illustrated', size=13, color='#0F172A', weight=800); b.text(340, 372, '232 × 96. Name pill, one line of detail, 64 px icon.', size=12, color='#475569')
items = [('Name', 'What it is, in the team\'s words: Order service, Orders database. Two or three words.'),
         ('Detail line', 'The technology or the job, one short line: PostgreSQL, push and SMS. Never a sentence.'),
         ('Icon', 'From the same sets as the other diagram types. Pick by the noun: Database, Queue, Gateway.'),
         ('Tint', 'Groups parts by domain or owner, not by layer. Courier is teal everywhere.')]
for i, (n, t) in enumerate(items):
    x = 760 if i % 2 else 760
    y = 190 + i * 62
    b.text(760, y, n, size=13, color='#0F172A', weight=800)
    b.text(860, y, t, size=12, color='#475569', w=330, lh=17)
# B lines
card(64, 490, 560, 480, 'Lines')
ys = [570, 650, 730, 810]
roles = [('next', 'Call or request', 'A synchronous call. Ink, thin. Label the protocol or the action: HTTPS, SQL, charge.'),
         ('main', 'Main path', 'Blue, thick, animated fast. The one route the diagram is about. One per diagram.'),
         ('data', 'Event or message', 'Violet, thin, animated slowly. Asynchronous: queues, topics, streams.'),
         ('back', 'Optional or copy', 'Dashed slate. Replication, a fallback, or a return you want to show.')]
for (r, n, t), y in zip(roles, ys):
    b.arrow([(88, y), (230, y)], r)
    b.text(256, y - 18, n, size=13, color='#0F172A', weight=800)
    b.text(256, y + 2, t, size=12, color='#475569', w=340, lh=17)
b.text(88, 880, 'A label sits on the line, a verb or a protocol, 90 px of room at least.', size=12, color='#334155')
b.text(88, 905, 'Arrows show who starts the call, not which way the data flows.', size=12, color='#334155')
# C zones
card(656, 490, 560, 480, 'Zones')
zone(b, 690, 570, 1190, 680, 'Cloud region', 'blue'); zone(b, 720, 600, 1000, 665, 'Private network', 'amber')
zone(b, 690, 730, 940, 800, 'Layer', 'green'); zone(b, 960, 730, 1190, 800, 'Third party', 'gray')
tx = [('Cloud region', 'Where it runs. Outermost frame, blue.'), ('Private network', 'Inside the region, closed to the internet. Amber.'), ('Layer', 'Clients, edge, services, data. Green or violet.'), ('Third party', 'Not yours. Grey.')]
for i, (n, t) in enumerate(tx):
    y = 830 + i * 0
b.text(690, 830, 'Frames nest, with 30 px between an outer and an inner edge.', size=12, color='#334155')
b.text(690, 852, 'Label is a dark pill on the top left edge. One frame, one word or two.', size=12, color='#334155')
b.text(690, 874, 'A part belongs to the smallest frame that holds it.', size=12, color='#334155')
b.text(690, 940, 'A line from a frame edge means "any part inside" (one line, one label).', size=12, color='#334155')
b.text(690, 896, 'Layer tints: clients blue, edge violet, services green, data amber,', size=12, color='#334155')
b.text(690, 918, 'third party grey. Region and network frames take blue and amber.', size=12, color='#334155')
print(save2(b))
