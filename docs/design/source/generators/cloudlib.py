# Cloud / network / deployment builder on top of archlib
from archlib import *
ZT = {'region': ('rgba(29,78,216,0.05)', '#1D4ED8', 'solid'), 'vpc': ('rgba(91,75,214,0.06)', '#5B4BD6', 'dashed'),
      'az': ('rgba(100,116,139,0.06)', '#64748B', 'dashed'), 'public': ('rgba(21,128,61,0.08)', '#15803D', 'dashed'),
      'private': ('rgba(245,158,58,0.10)', '#B45309', 'dashed'), 'data': ('rgba(15,118,110,0.08)', '#0F766E', 'dashed'),
      'onprem': ('rgba(100,116,139,0.08)', '#334155', 'solid'), 'edge': ('rgba(91,75,214,0.05)', '#7C3AED', 'dashed'),
      'dmz': ('rgba(180,35,24,0.06)', '#B42318', 'dashed')}
def cz(b, x0, y0, x1, y1, label, kind, pill_x=None):
    """Frame: region, vpc, az, subnet (public/private/data), on-prem, edge, dmz. Label pill on the top edge."""
    bg, bd, st = ZT[kind]
    b.raw(f'<div data-lint="box" style="position:absolute;left:{x0}px;top:{y0}px;width:{x1-x0}px;height:{y1-y0}px;box-sizing:border-box;background:{bg};border:1.5px {st} {bd};border-radius:14px"></div>')
    b.raw(f'<div data-lint="label" style="position:absolute;left:{pill_x if pill_x is not None else x0 + 18}px;top:{y0-11}px;height:22px;padding:0 12px;box-sizing:border-box;border-radius:999px;background:{bd};color:#fff;font-size:12px;font-weight:700;line-height:22px;white-space:nowrap">{html.escape(label)}</div>')
def save9(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Cloud: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
