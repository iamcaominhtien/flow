import html
from fclib import *
from fslib import TONES
TONES['rose'] = ('#FDE4E4', '#F9C2C0')
def save5(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>UML: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
def state(b, cx, cy, name, tone='blue', w=160, h=64, sub=None, dashed=False):
    bg, pill = TONES[tone]
    bd = '2px dashed #64748B' if dashed else '2px solid #0F172A'
    b.raw(f'<div style="position:absolute;left:{cx-w/2:g}px;top:{cy-h/2:g}px;width:{w}px;height:{h}px;box-sizing:border-box;border:{bd};border-radius:20px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center"><div style="font-size:14px;font-weight:800;line-height:18px">{html.escape(name)}</div>'
          + (f'<div style="font:500 11px/15px \'JetBrains Mono\',monospace;color:#475569">{html.escape(sub)}</div>' if sub else '') + '</div>')
    return Node(cx, cy, w, h)
def initial(b, cx, cy, r=13):
    b.raw(f'<div style="position:absolute;left:{cx-r}px;top:{cy-r}px;width:{2*r}px;height:{2*r}px;border-radius:999px;background:#0F172A"></div>')
    return Node(cx, cy, 2 * r, 2 * r)
def final(b, cx, cy, r=16):
    b.raw(f'<div style="position:absolute;left:{cx-r}px;top:{cy-r}px;width:{2*r}px;height:{2*r}px;box-sizing:border-box;border-radius:999px;border:2.5px solid #0F172A;background:#fff"><div style="position:absolute;left:4.5px;top:4.5px;right:4.5px;bottom:4.5px;border-radius:999px;background:#0F172A"></div></div>')
    return Node(cx, cy, 2 * r, 2 * r)

def uline(b, pts, dashed=False, col=INK, sw=2):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 8
    ox, oy = min(xs) - pad, min(ys) - pad
    d = 'M ' + ' L '.join(f'{p[0]-ox:g} {p[1]-oy:g}' for p in pts)
    da = ' stroke-dasharray="7 6"' if dashed else ''
    b.raw(f'<svg width="{max(xs)-ox+pad:g}" height="{max(ys)-oy+pad:g}" style="position:absolute;left:{ox:g}px;top:{oy:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round"><path d="{d}"{da}/></svg>')
def umark(b, x, y, d, kind, col=INK):
    """end mark at (x,y), d = unit vector pointing away from the target (along the line); kinds: open, tri, dia_hollow, dia_fill"""
    import math
    ang = math.degrees(math.atan2(d[1], d[0]))
    o = 24
    g = {'open': f'<path d="M{o+12} {o-6} L{o} {o} L{o+12} {o+6}" fill="none"/>',
         'tri': f'<path d="M{o} {o} L{o+16} {o-8} L{o+16} {o+8} Z" fill="#fff"/>',
         'dia_hollow': f'<path d="M{o} {o} L{o+11} {o-7} L{o+22} {o} L{o+11} {o+7} Z" fill="#fff"/>',
         'dia_fill': f'<path d="M{o} {o} L{o+11} {o-7} L{o+22} {o} L{o+11} {o+7} Z" fill="{col}"/>'}[kind]
    b.raw(f'<svg width="{2*o}" height="{2*o}" viewBox="0 0 {2*o} {2*o}" style="position:absolute;left:{x-o:g}px;top:{y-o:g}px;overflow:visible;stroke:{col};stroke-width:2;stroke-linejoin:round;stroke-linecap:round"><g transform="rotate({ang:g} {o} {o})">{g}</g></svg>')
def link(b, pts, a_mark=None, b_mark=None, dashed=False, label=None, lpos=None, ma=None, mb=None):
    import math
    def unit(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1
        return (dx / L, dy / L)
    uline(b, pts, dashed)
    if a_mark: umark(b, pts[0][0], pts[0][1], unit(pts[0], pts[1]), a_mark)
    if b_mark: umark(b, pts[-1][0], pts[-1][1], unit(pts[-1], pts[-2]), b_mark)
    if label: b.label(lpos[0], lpos[1], label, 'plain')
    for (txt, p, q) in ((ma, pts[0], pts[1]), (mb, pts[-1], pts[-2])):
        if txt:
            u = unit(p, q)
            b.text(p[0] + u[0] * 30 - 6 + (14 if abs(u[1]) > .5 else 0), p[1] + u[1] * 30 + (-20 if abs(u[1]) > .5 else 6), txt, size=12, color='#0F172A', weight=700)
