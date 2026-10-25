import json, sys, shutil
root = '/path/to/work/'
saved = root + 'artifact-files/f9b613a9-bbae-477e-90e5-e72d00e5fdf2/project/canvas.json'
local = root + 'flowdesign/project/canvas.json'
cj = json.load(open(saved, encoding='utf-8'))
for spec in sys.argv[1:]:
    name, x, y, w, h, title = spec.split('|')
    if name not in cj['order']:
        cj['order'].append(name)
    cj['boards'][name] = {'h': int(h), 'page': 'screenflow', 'title': title, 'w': int(w), 'x': int(x), 'y': int(y)}
json.dump(cj, open(local, 'w', encoding='utf-8'), indent=2, sort_keys=True)
open(local, 'a').write('\n')
print(len(cj['boards']), 'boards')
