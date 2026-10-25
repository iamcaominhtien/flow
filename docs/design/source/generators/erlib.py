# ER diagram builder (crow's foot) on top of fclib.Board
import html
from fclib import *
from fslib import TONES

BADGE = {'pk': ('PK', '#FFE2B0', '#92400E'), 'fk': ('FK', '#DCEEFB', '#1E5AA8'), 'uq': ('UQ', '#E6E3FB', '#4F46A5')}
RH = 28

class Ent:
    def __init__(s, x, y, w, h, hh, cols): s.x, s.y, s.w, s.h, s.hh, s.cols = x, y, w, h, hh, cols
    def row(s, name):
        i = [c[0] for c in s.cols].index(name)
        return s.y + s.hh + 4 + i * RH + RH / 2
    @property
    def l(s): return s.x
    @property
    def r(s): return s.x + s.w
    @property
    def cx(s): return s.x + s.w / 2
    @property
    def bot(s): return s.y + s.h

def entity(b, x, y, name, cols, tone, icon=None, dicon=None, style='plain', w=240, note=None, ghost=False, tag=None):
    hh = 40 if style == 'plain' else 64
    h = hh + 8 + len(cols) * RH
    bg, hd = TONES[tone]
    if ghost: bg, hd = '#F1F5F9', '#E2E8F0'
    rows = ''
    for i, (cn, ty, fl) in enumerate(cols):
        fl = fl.split(',') if fl else []
        bd = ''.join(f'<span style="display:inline-block;width:22px;margin-right:2px;height:16px;border-radius:4px;background:{BADGE[f][1]};color:{BADGE[f][2]};font:700 9.5px/16px Inter,sans-serif;text-align:center">{BADGE[f][0]}</span>' for f in ('pk', 'fk', 'uq') if f in fl)
        ty2 = ty + ('?' if 'null' in fl else '')
        rows += (f'<div style="position:absolute;left:0;right:0;top:{hh+4+i*RH}px;height:{RH}px;display:flex;align-items:center;padding:0 12px;box-sizing:border-box;gap:6px;border-top:{"1px solid #E2E8F0" if i else "0"}">'
                 f'<span style="width:50px;flex:none;display:flex;gap:2px">{bd}</span>'
                 f'<span style="font-size:12.5px;font-weight:{700 if "pk" in fl else 500};color:#0F172A;white-space:nowrap">{html.escape(cn)}</span>'
                 f'<span style="margin-left:auto;font:400 11px/14px \'JetBrains Mono\',monospace;color:#64748B;white-space:nowrap">{html.escape(ty2)}</span></div>')
    if style == 'plain':
        ic = icon_svg(icon, 12, 11, 18, '#334155') if icon else ''
        head = f'<div style="position:absolute;left:0;top:0;width:100%;height:{hh}px;background:{hd};border-bottom:2px solid #0F172A">{ic}<div style="position:absolute;left:{36 if icon else 14}px;top:0;height:{hh}px;display:flex;align-items:center;font-size:14px;font-weight:800">{html.escape(name)}</div></div>'
    else:
        ic = detailicon(dicon or icon, 52, w - 66, 6) if (dicon or icon) in DETAIL else ''
        head = f'<div style="position:absolute;left:0;top:0;width:100%;height:{hh}px;background:{hd};border-bottom:2px solid #0F172A"><div style="position:absolute;left:14px;top:0;height:{hh}px;display:flex;align-items:center"><span style="padding:2px 12px;border:2px solid #0F172A;border-radius:999px;background:{bg};box-shadow:0 3px 0 #0F172A;font-size:13.5px;font-weight:800;line-height:18px">{html.escape(name)}</span></div>{ic}</div>'
    tg = f'<div style="position:absolute;left:-2px;top:{h+8}px;padding:0 8px;height:18px;border-radius:999px;background:#fff;border:1.5px solid #64748B;color:#475569;font:700 10.5px/15px Inter,sans-serif;white-space:nowrap">{html.escape(tag)}</div>' if tag else ''
    bd = '2px dashed #64748B' if ghost else '2px solid #0F172A'
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;background:#fff;border:{bd};border-radius:12px;overflow:hidden">{head}{rows}</div>')
    if tg: b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px">{tg}</div>')
    return Ent(x, y, w, h, hh, cols)

def mark(b, x, y, d, kind, col=INK, sw=2):
    """cardinality mark at entity edge point (x,y); d = unit vector pointing away from the entity."""
    ang = {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}[d]
    o = 20
    foot = f'<path d="M{o+14} {o}L{o} {o-7}M{o+14} {o}L{o} {o}M{o+14} {o}L{o} {o+7}"/>'
    bar = lambda dx: f'<path d="M{o+dx} {o-6}V{o+6}"/>'
    circ = lambda dx: f'<circle cx="{o+dx}" cy="{o}" r="4.5" fill="#F8FAFC"/>'
    g = {'one': bar(10) + bar(16), 'zero_one': bar(10) + circ(20), 'many': foot + bar(19), 'zero_many': foot + circ(21)}[kind]
    b.raw(f'<svg width="40" height="40" viewBox="0 0 40 40" style="position:absolute;left:{x-o:g}px;top:{y-o:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linecap:round" aria-hidden="true"><g transform="rotate({ang} {o} {o})">{g}</g></svg>')

def line(b, pts, main=False, dashed=False):
    col, sw = ('#1D4ED8', 4) if main else (INK, 2)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = 8
    ox, oy = min(xs) - pad, min(ys) - pad
    d = 'M ' + ' L '.join(f'{p[0]-ox:g} {p[1]-oy:g}' for p in pts)
    cls = ' class="flow"' if main else ''
    da = ' stroke-dasharray="7 6"' if dashed else ''
    col = '#475569' if dashed else col
    b.raw(f'<svg width="{max(xs)-ox+pad:g}" height="{max(ys)-oy+pad:g}" style="position:absolute;left:{ox:g}px;top:{oy:g}px;overflow:visible;fill:none;stroke:{col};stroke-width:{sw};stroke-linejoin:round"><path{cls} d="{d}"{da}/></svg>')

def rel(b, pts, a_kind, b_kind, label=None, lpos=None, main=False, dashed=False, mono=False):
    """pts: polyline from entity A edge to entity B edge. a_kind at start, b_kind at end."""
    def unit(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        if abs(dx) >= abs(dy): return (1 if dx > 0 else -1, 0)
        return (0, 1 if dy > 0 else -1)
    line(b, pts, main, dashed)
    col = '#1D4ED8' if main else (SLATE if dashed else INK)
    mark(b, pts[0][0], pts[0][1], unit(pts[0], pts[1]), a_kind, col, 4 if main else 2)
    mark(b, pts[-1][0], pts[-1][1], unit(pts[-1], pts[-2]), b_kind, col, 4 if main else 2)
    if label:
        b.label(lpos[0], lpos[1], label, 'plain')

def save(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>ER: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r

def hv(p, q, mid):
    """horizontal-vertical-horizontal route with the vertical leg at x=mid"""
    if abs(p[1] - q[1]) < 0.5: return [p, q]
    return [p, (mid, p[1]), (mid, q[1]), q]
def vhv(p, q, midy):
    if abs(p[0] - q[0]) < 0.5: return [p, q]
    return [p, (p[0], midy), (q[0], midy), q]
