# Explainer / infographic builder
import html
from fclib import *
from fslib import TONES
def banner(b, title, sub, w):
    b.raw(f'<div style="position:absolute;left:64px;top:44px;width:{w-128}px"><div style="font-size:40px;line-height:46px;font-weight:800;letter-spacing:-0.5px">{html.escape(title)}</div><div style="font-size:16px;line-height:24px;color:#475569;margin-top:10px;max-width:900px">{html.escape(sub)}</div></div>')
def num(b, x, y, n):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:30px;height:30px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:800 14px/30px \'JetBrains Mono\',monospace;text-align:center;z-index:3">{n}</div>')
def xcard(b, cx, cy, title, desc, dicon, tone, n=None, w=260, h=200):
    bg, pill = TONES[tone]
    x, y = cx - w / 2, cy - h / 2
    ic = detailicon(dicon, 88, (w - 88) / 2, 14) if dicon in DETAIL else ''
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:16px;background:{bg}">{ic}'
          f'<div style="position:absolute;left:0;right:0;top:112px;display:flex;justify-content:center"><div style="padding:3px 14px;border:2px solid #0F172A;border-radius:999px;background:{pill};box-shadow:0 3px 0 #0F172A;font-size:14px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(title)}</div></div>'
          f'<div style="position:absolute;left:14px;right:14px;top:150px;text-align:center;font-size:12.5px;line-height:17px;color:#334155">{html.escape(desc)}</div></div>')
    if n is not None: num(b, x - 10, y - 10, n)
    return Node(cx, cy, w, h)
def band(b, x0, y0, x1, y1, label, tone):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{x0}px;top:{y0}px;width:{x1-x0}px;height:{y1-y0}px;box-sizing:border-box;background:{bg};opacity:.55;border-radius:20px"></div>')
    b.raw(f'<div style="position:absolute;left:{x0+18}px;top:{y0+16}px;padding:3px 14px;border:2px solid #0F172A;border-radius:999px;background:{pill};font-size:13px;font-weight:800;line-height:18px;white-space:nowrap">{html.escape(label)}</div>')
def save3(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Explainer: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
