import json, re, math
root = '/path/to/work/'
proj = root + 'flowdesign/project/'
src = open(root + 'artifact-files/f9b613a9-bbae-477e-90e5-e72d00e5fdf2/project/Components.dc.html', encoding='utf-8').read()

first = src.index('<section class="sec">')
prefix = src[:first]
last_end = src.rindex('</section>') + len('</section>')
suffix = src[last_end:]
sections = {}
pos = first
while True:
    i = src.find('<section class="sec">', pos)
    if i < 0 or i >= last_end:
        break
    j = src.index('</section>', i) + len('</section>')
    title = re.search(r'<h2>([^<]*)</h2>', src[i:j]).group(1)
    sections[title] = src[i:j]
    pos = j
assert len(sections) == 19, len(sections)

groups = [
 ('Components_Process.dc.html', 'Process and behavior',
  'Nodes and notation for flowcharts, business processes and behavior models: flowchart shapes, BPMN, state machines, use cases and data flow.',
  [('Flowchart nodes', 2), ('BPMN and activity', 3), ('State machine, use case and data flow', 3)]),
 ('Components_Structure.dc.html', 'Structure and architecture',
  'Notation for data, class, sequence and system diagrams: ER entities and cardinality, UML relationships, sequence parts, C4 elements and cloud boundaries.',
  [('Data modeling', 2), ('UML relationships', 2), ('Sequence diagrams', 2), ('Architecture and C4', 2), ('Cloud boundaries', 2)]),
 ('Components_ScreenFlow.dc.html', 'Screen flow parts',
  'Everything a screen-flow diagram is built from: device frames, wireframe blocks, overlays and states, and the transitions between screens.',
  [('Screen flow: device frames', 2), ('Screen flow: wireframe blocks', 3), ('Screen flow: overlays and states', 2), ('Screen flow: transitions', 2)]),
 ('Components_Annotations.dc.html', 'Annotations and layout',
  'Labels, frames, special edges and page chrome that sit on top of any diagram type.',
  [('Labels and annotations', 2), ('Containers and frames', 2), ('Special edges', 2), ('Headers and chrome', 1)]),
 ('Components_Planning.dc.html', 'Planning and explainer',
  'Timelines, boards and org charts, plus infographic elements and code or technical snippets for explainers.',
  [('Planning and organization', 2), ('Infographic elements', 3), ('Code and technical', 2)]),
]
used = [t for g in groups for t, _ in g[3]]
assert sorted(used) == sorted(sections), set(sections) ^ set(used)

heights = {}
for fname, title, lede, items in groups:
    p = prefix
    p = p.replace('<title>Flow Components</title>', '<title>Flow Components: %s</title>' % title)
    p = p.replace('Components · shared across diagram types', 'Components · %s' % title)
    p = p.replace('>Component library</h1>', '>%s</h1>' % title)
    p = re.sub(r'(max-width: 800px">)[^<]*(</p>)', lambda m: m.group(1) + lede + m.group(2), p, count=1)
    h = 260 + sum(60 + rows * 290 + 48 for _, rows in items)
    h = int(math.ceil(h / 50.0) * 50)
    heights[fname] = h
    body = '\n\n'.join(sections[t] for t, _ in items)
    s = suffix
    s = re.sub(r'("\$preview":\{"width":\d+,"height":)\d+', lambda m: m.group(1) + str(h), s)
    open(proj + fname, 'w', encoding='utf-8').write(p + body + s)
print(heights)

cj = json.load(open(root + 'artifact-files/f9b613a9-bbae-477e-90e5-e72d00e5fdf2/project/canvas.json', encoding='utf-8'))
del cj['boards']['Components.dc.html']
cj['order'].remove('Components.dc.html')
row2 = max(list(heights.values())[:3]) + 140
pos = {
 'Components_Process.dc.html': (0, 0), 'Components_Structure.dc.html': (1360, 0), 'Components_ScreenFlow.dc.html': (2720, 0),
 'Components_Annotations.dc.html': (0, row2), 'Components_Planning.dc.html': (1360, row2)}
titles = {g[0]: g[1] for g in groups}
for fname, (x, y) in pos.items():
    cj['boards'][fname] = {'expand': 'fill', 'h': heights[fname], 'page': 'components', 'title': titles[fname], 'w': 1280, 'x': x, 'y': y}
    cj['order'].append(fname)
json.dump(cj, open(proj + 'canvas.json', 'w', encoding='utf-8'), indent=2, sort_keys=True)
open(proj + 'canvas.json', 'a').write('\n')
