# C4 model builder on top of archlib / fclib.Board
import html
from archlib import *
KIND = {'person': 'Person', 'system': 'Software system', 'ext': 'External system', 'container': 'Container', 'component': 'Component'}
def c4(b, cx, cy, kind, name, tech, desc, icon, tone, w=280, h=132):
    """One C4 element: icon, bold name, [type: technology], a description of its job."""
    bg, pill = TONES[tone]
    dash = ';border-style:dashed' if kind == 'ext' else ''
    t = KIND[kind] + (f': {tech}' if tech else '')
    isz = 40
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:{14 if kind!="person" else 28}px;background:{bg}{dash}">'
          + bigicon(icon, isz, 14, 14)
          + f'<div style="position:absolute;left:{isz+28}px;right:12px;top:12px"><div style="font-size:14px;font-weight:800;line-height:18px">{html.escape(name)}</div><div style="font-size:11px;line-height:15px;color:#475569;font-family:\'JetBrains Mono\',monospace">[{html.escape(t)}]</div></div>'
          + f'<div style="position:absolute;left:14px;right:14px;top:68px;font-size:12px;line-height:16px;color:#334155">{html.escape(desc)}</div></div>')
    return Node(cx, cy, w, h)
def boundary(b, x0, y0, x1, y1, label, tone='gray', pill_x=None):
    """Dashed frame that marks the edge of the thing being zoomed into."""
    bg = {'gray': 'rgba(100,116,139,0.07)', 'violet': 'rgba(91,75,214,0.07)', 'blue': 'rgba(29,78,216,0.06)'}[tone]
    b.rect(x0, y0, x1 - x0, y1 - y0, bg, '#64748B', 16)
    b.pill(pill_x if pill_x is not None else x0 + 18, y1 - 11, label, '#0F172A')   # label on the bottom edge so lines from people above never cross it
def save8(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>C4: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
