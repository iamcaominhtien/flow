import re, sys
base = '/path/to/flowdesign/project/'
s = open(base + 'ScreenFlow_Cond_Inline.dc.html', encoding='utf-8').read()
lines = s.split('\n')
drop_starts = [
 'left: 192px; top: 258px', 'left: 453px; top: 260px', 'left: 453px; top: 296px', 'left: 376px; top: 390px',
 'left: 492px; top: 548px', 'left: 452px; top: 590px', 'left: 716px; top: 258px', 'left: 994px; top: 260px',
 'left: 974px; top: 296px', 'left: 896px; top: 366px', 'left: 896px; top: 392px']
out = []
for ln in lines:
    if ln.startswith('<div style="position: absolute; ') and any(ln.startswith('<div style="position: absolute; ' + d) for d in drop_starts):
        continue
    out.append(ln)
s = '\n'.join(out)
i = s.index('<div style="position: absolute; left: 700px; top: 520px')
j = s.rindex('\n</div>\n</x-dc>')
s = s[:i].rstrip('\n') + s[j:]
tag = lambda l, t, c: f'<div style="position: absolute; left: {l}px; top: {t}px; width: 30px; height: 22px; box-sizing: border-box; border-radius: 6px; background: #FFFFFF; border: 1.5px solid #0F172A; font-family: \'JetBrains Mono\', monospace; font-size: 11px; font-weight: 700; line-height: 19px; text-align: center">{c}</div>'
tags = '\n'.join([tag(224,256,'C1'), tag(493,256,'C2'), tag(376,379,'C3'), tag(519,546,'C4'), tag(744,256,'C5'), tag(1014,256,'C6'), tag(896,379,'C7')])
rows = [
 ('C1','S00 &rarr; Logged in?','auto, 2 s','splash timer elapsed','', 'check session'),
 ('C2','Logged in? &rarr; S02','system','token exists and is not expired','#15803D','load profile'),
 ('C3','Logged in? &rarr; S01','system','no token, or token expired','#B42318','clear token'),
 ('C4','S01 &rarr; S02','tap Login','email and password valid','#15803D','save token'),
 ('C5','S02 &rarr; Camera allowed?','tap Scan','none','','request camera permission'),
 ('C6','Camera allowed? &rarr; S03','OS prompt','permission granted','#15803D','open camera'),
 ('C7','Camera allowed? &rarr; S04','OS prompt','permission denied','#B42318','show settings link'),
]
cell = 'padding: 10px 12px; border-bottom: 1px solid #E2E8F0; font-size: 13px; line-height: 18px'
hdr = 'padding: 10px 12px; background: #F1F5F9; font-size: 12px; font-weight: 700'
t = ['<div style="position: absolute; left: 64px; top: 740px; width: 1172px; box-sizing: border-box; background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 12px; overflow: hidden; display: grid; grid-template-columns: 64px 220px 130px 1fr 1fr">']
for h in ['Code','Transition','Trigger','Condition (guard)','Effect']:
    t.append(f'<span style="{hdr}">{h}</span>')
for code, tr, trg, cond, col, eff in rows:
    ccol = f'color: {col}; ' if col else 'color: #475569; '
    t.append(f'<span style="{cell}; font-family: \'JetBrains Mono\', monospace; font-weight: 700">{code}</span>')
    t.append(f'<span style="{cell}">{tr}</span>')
    t.append(f'<span style="{cell}">{trg}</span>')
    t.append(f'<span style="{cell}; font-family: \'JetBrains Mono\', monospace; font-size: 12px; {ccol}">{cond}</span>')
    t.append(f'<span style="{cell}; color: #334155">{eff}</span>')
t.append('</div>')
t.append('<div style="position: absolute; left: 64px; top: 1020px; width: 900px; font-size: 13px; line-height: 20px; color: #475569">Arrows carry only a code. Everything else lives in the table, so labels never crowd the diagram. Use this form when conditions are long, shared by several arrows, or reviewed by someone who does not read the diagram.</div>')
block = tag and '\n'.join(t)
s = s.replace('\n</div>\n</x-dc>', '\n' + tags + '\n' + block + '\n</div>\n</x-dc>', 1)
s = s.replace('height: 780px; background: #F8FAFC', 'height: 1100px; background: #F8FAFC')
s = s.replace('"height":780', '"height":1100')
s = s.replace('Conditions written on the arrows', 'Conditions as codes and a table')
s = s.replace('<title>Screen flow: conditions on the arrows</title>', '<title>Screen flow: conditions as codes</title>')
open(base + 'ScreenFlow_Cond_Coded.dc.html', 'w', encoding='utf-8').write(s)
print(len(s))
