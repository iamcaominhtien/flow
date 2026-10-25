from erlib import *
b = Board('ER_Notation', 'Notation: marks, keys, lines', 1280, 960,
  'How to read one table and one line. Cardinality marks sit at the end of the line, against the table they describe.')
def card(x, y, w, h, title):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#fff;border:1px solid #E2E8F0;border-radius:14px"></div>')
    b.text(x + 22, y + 18, title, size=16, color='#0F172A', weight=800)
def box(x, y, w, h, t):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:8px;background:#F1F5F9;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700">{t}</div>')
# A: cardinality
card(64, 130, 560, 440, 'Cardinality marks')
rows = [('one', 'Exactly one', 'one', 'Two bars: mandatory, single.'), ('zero_one', 'Zero or one', 'zero_one', 'A circle and a bar: optional, single.'),
        ('many', 'One or many', 'many', 'A crow\'s foot and a bar: mandatory, several.'), ('zero_many', 'Zero or many', 'zero_many', 'A circle and a crow\'s foot: optional, several.')]
for i, (k, n, v, t) in enumerate(rows):
    y = 214 + i * 82
    box(88, y - 20, 70, 40, 'A'); box(300, y - 20, 70, 40, 'B')
    line(b, [(158, y), (300, y)]); mark(b, 300, y, (-1, 0), k)
    b.text(396, y - 24, n, size=13, color='#0F172A', weight=800)
    b.text(396, y - 5, t, size=11.5, color='#475569', w=210, lh=16)
    b.text(396, y + 28, f'card: {v}', size=11, color='#64748B', mono=True) if False else b.text(88, y + 26, f'value: {v}', size=11, color='#64748B', mono=True)
b.text(88, 520, 'Read a mark as: each A relates to this many B. Every line carries two marks.', size=12, color='#334155')
# B: inside a table
card(656, 130, 560, 440, 'Inside a table')
e = entity(b, 680, 190, 'Order', [('id', 'uuid', 'pk'), ('customer_id', 'uuid', 'fk'), ('email', 'text', 'uq'), ('coupon', 'text', 'null'), ('total', 'decimal', '')], 'violet', 'cart', w=240)
items = [('Badges', 'PK primary key, FK foreign key, UQ unique. A column can carry two, such as PK FK in a junction table.'),
         ('Bold name', 'The primary key is bold. Keys come first, then the columns that explain the relationships.'),
         ('Type', 'Mono, grey, right aligned. Generic names: uuid, text, int, decimal, bool, timestamp.'),
         ('Question mark', 'A ? after the type: the column may be empty.')]
for i, (n, t) in enumerate(items):
    y = 190 + i * 88
    b.text(950, y, n, size=13, color='#0F172A', weight=800)
    b.text(950, y + 20, t, size=11.5, color='#475569', w=240, lh=16)
# C: lines
card(64, 600, 560, 310, 'Lines')
ls = [({'main': False, 'dashed': False}, 'Solid ink', 'A real foreign key, enforced by the database.'),
      ({'main': False, 'dashed': True}, 'Dashed slate', 'A logical link: no constraint, often to another service.'),
      ({'main': True, 'dashed': False}, 'Blue, thick, animated', 'The one path to follow. One per diagram, as in every other type.')]
for i, (kw, n, t) in enumerate(ls):
    y = 676 + i * 66
    line(b, [(88, y), (208, y)], **kw)
    b.text(236, y - 18, n, size=13, color='#0F172A', weight=800)
    b.text(236, y + 2, t, size=11.5, color='#475569', w=360, lh=16)
b.text(88, 860, 'A verb on a pill names the link: places, contains. Active voice, read from the one side.', size=12, color='#334155')
# D: styles
card(656, 600, 560, 310, 'Two header styles')
entity(b, 680, 660, 'Customer', [('id', 'uuid', 'pk'), ('email', 'text', 'uq')], 'blue', 'user', 'User', style='plain', w=240)
entity(b, 944, 660, 'Customer', [('id', 'uuid', 'pk'), ('email', 'text', 'uq')], 'blue', 'user', 'User', style='detail', w=240)
b.text(680, 802, 'Plain: flat icon, 40 px header.', size=12, color='#334155')
b.text(944, 802, 'Illustrated: 52 px icon, 64 px header.', size=12, color='#334155')
b.text(680, 860, 'Rows, keys, lines and marks are identical in both.', size=12, color='#334155')
print(save(b))
