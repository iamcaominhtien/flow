import html
from fclib import *
from fslib import TONES
STAT = {'done': ('#15803D', '#B5EBC1'), 'doing': ('#1D4ED8', '#BFDBFE'), 'plan': ('#64748B', '#E2E8F0'), 'blocked': ('#B42318', '#FDE4E4')}
def save4(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Planning: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
def avatar(b, x, y, init, tone, d=26):
    bg, pill = TONES[tone]
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{d}px;height:{d}px;border-radius:999px;background:{pill};border:2px solid #0F172A;box-sizing:border-box;font:800 {int(d*0.38)}px/{d-4}px Inter,sans-serif;text-align:center;color:#0F172A">{init}</div>')
def line(b, pts, col=INK, sw=2, dash=None, cls=''):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 8
    ox, oy = min(xs) - pad, min(ys) - pad
    d = 'M ' + ' L '.join(f'{p[0]-ox:g} {p[1]-oy:g}' for p in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ''
    b.raw(f'<svg width="{max(xs)-ox+pad:g}" height="{max(ys)-oy+pad:g}" style="position:absolute;left:{ox:g}px;top:{oy:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round"><path{cls} d="{d}"{da}/></svg>')
