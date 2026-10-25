from exlib import *
W, H = 1400, 1200
b = Board('Explainer_Tree', 'Tree: what is inside a web project', W, H, hdr=False)
banner(b, 'What is inside a web project', 'A project is a folder with a few well-known places in it. Knowing what each one is for makes any new project easy to read.', W)
root = xcard(b, 250, 640, 'my-app/', 'The project folder. Everything below lives here.', 'Folder', 'amber', w=300, h=210)
rows = [('src/', 'The code you write. Most of your time is spent here.', 'Code / API', 'blue'), ('public/', 'Files sent to the browser as they are: images, icons, fonts.', 'Globe', 'violet'),
        ('tests/', 'Small programs that check the code still works.', 'Success', 'green'), ('docs/', 'Notes for people: how to start, how it is built.', 'Info', 'teal'),
        ('package.json', 'The shopping list: which libraries the project needs.', 'Package', 'amber'), ('README.md', 'The front door: what this is and how to run it.', 'File', 'gray'),
        ('.env', 'Secrets such as passwords. Never shared, never uploaded.', 'Lock', 'rose')]
TONES['rose'] = ('#FDE4E4', '#F9C2C0')
RX, RW, RH, P0, PIT = 640, 700, 92, 330, 112
for i, (n, d, ic, tone) in enumerate(rows):
    cy = P0 + i * PIT
    bg, pill = TONES[tone]
    chips = '<div style="position:absolute;right:16px;top:30px;display:flex;align-items:center;gap:8px"><span style="font-size:11.5px;font-weight:700;color:#475569">inside:</span>' + ''.join(f'<span style="height:24px;padding:0 10px;border:2px solid #0F172A;border-radius:999px;background:#fff;font:600 12px/20px JetBrains Mono,monospace">{s}</span>' for s in ('components/', 'pages/', 'api/')) + '</div>'
    b.raw(f'<div style="position:absolute;left:{RX}px;top:{cy-RH/2}px;width:{RW}px;height:{RH}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:14px;background:{bg}">{detailicon(ic, 60, 16, 14)}'
          f'<div style="position:absolute;left:96px;top:14px;font:700 16px/22px \'JetBrains Mono\',monospace">{n}</div><div style="position:absolute;left:96px;top:42px;right:{350 if i == 0 else 16}px;font-size:13px;line-height:18px;color:#334155">{d}</div>{chips if i == 0 else ''}</div>')
    b.arrow([(root.r()[0], 640), (460, 640), (460, cy), (RX, cy)] if cy != 640 else [(root.r()[0], 640), (RX, 640)], 'next')
b.text(RX + 120, P0 + 58, '', size=1)
b.text(64, H - 70, 'Folder names end with a slash. Names with a dot are files. Order here is only for reading; real folders are listed alphabetically.', size=13, color='#475569', w=1200)
print(save3(b))
