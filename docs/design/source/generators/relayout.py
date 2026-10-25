import json
root = '/path/to/work/'
cj = json.load(open(root + 'artifact-files/f9b613a9-bbae-477e-90e5-e72d00e5fdf2/project/canvas.json', encoding='utf-8'))
B = cj['boards']
key = lambda n: 'ScreenFlow_' + n + '.dc.html'
sections = [
 ('Reference and notation', 'cols', [['Rules'], ['Anatomy', 'Triggers'], ['Cond_Inline', 'Cond_Coded']]),
 ('Fidelity levels', 'grid', [['L0_Names', 'L1_Skeleton'], ['L2_KeyElements', 'Mixed']]),
 ('Examples and variants', 'cols', [['Shop_SP', 'States'], ['Shop_PC', 'Devices']]),
 ('Navigation and structure patterns', 'cols', [['Tabs'], ['Overlays', 'Entry']]),
 ('Complete flows', 'cols', [['Real_ShopApp'], ['Highlight']]),
]
GAP = 120
notes = {}
y0 = 0
for si, (title, mode, groups) in enumerate(sections):
    top = y0 + 300
    bottom = top
    x = 0
    maxx = 0
    if mode == 'cols':
        for col in groups:
            colw = max(B[key(n)]['w'] for n in col)
            y = top
            for n in col:
                b = B[key(n)]
                b['x'], b['y'] = x, y
                y += b['h'] + GAP
            bottom = max(bottom, y - GAP)
            x += colw + GAP
        maxx = x - GAP
    else:
        colw = [max(B[key(r[c])]['w'] for r in groups if c < len(r)) for c in range(max(len(r) for r in groups))]
        y = top
        for r in groups:
            x = 0
            rh = 0
            for c, n in enumerate(r):
                b = B[key(n)]
                b['x'], b['y'] = x, y
                x += colw[c] + GAP
                rh = max(rh, b['h'])
            y += rh + GAP
        bottom = y - GAP
        maxx = sum(colw) + GAP * (len(colw) - 1)
    notes['sf-section-%d' % (si + 1)] = {'x': 0, 'y': y0, 'text': title, 'kind': 'title1', 'maxW': maxx, 'page': 'screenflow'}
    print(si + 1, title, 'rows y', top, '->', bottom, 'width', maxx)
    y0 = bottom + 240
cj['notes'].update(notes)
json.dump(cj, open(root + 'flowdesign/project/canvas.json', 'w', encoding='utf-8'), indent=2, sort_keys=True)
open(root + 'flowdesign/project/canvas.json', 'a').write('\n')
