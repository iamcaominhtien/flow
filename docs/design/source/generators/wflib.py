# Wireframe builder: neutral gray-blue blocks, blue for the primary action
import html
from fclib import *
G1, G2, G3, G4 = '#F1F5F9', '#E2E8F0', '#CBD5E1', '#94A3B8'
BLUE = '#1D4ED8'
def save6(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Wireframe: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
def R(b, x, y, w, h, bg='#fff', bd=G3, r=8, bw=1.5, extra=''):
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{w:g}px;height:{h:g}px;box-sizing:border-box;background:{bg};border:{bw}px solid {bd};border-radius:{r}px;{extra}"></div>')
def T(b, x, y, t, size=12, wt=500, col='#334155', w=None, center=False, lh=None):
    lh = lh or int(size * 1.35)
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;{"width:%gpx;" % w if w else "white-space:nowrap;"}font-size:{size}px;line-height:{lh}px;font-weight:{wt};color:{col};{"text-align:center;" if center else ""}">{t}</div>')
def bar(b, x, y, w, h=7, col=G3): R(b, x, y, w, h, col, col, h / 2, 0)
def lines(b, x, y, w, n=3, gap=13, last=0.6):
    for i in range(n): bar(b, x, y + i * gap, w * (last if i == n - 1 else 1))
def btn(b, x, y, w, t, kind='primary', h=44):
    bg, fg, bd = {'primary': (BLUE, '#fff', BLUE), 'secondary': ('#fff', BLUE, BLUE), 'danger': ('#fff', '#B42318', '#B42318'), 'disabled': (G2, G4, G2)}[kind]
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{w:g}px;height:{h}px;box-sizing:border-box;border:2px solid {bd};border-radius:{h/2.8:g}px;background:{bg};color:{fg};font:700 {13 if h>=40 else 12}px/{h-4}px Inter,sans-serif;text-align:center">{t}</div>')
def field(b, x, y, w, label, value='', focus=False, helper=None):
    T(b, x, y, label, 11, 700, '#475569')
    R(b, x, y + 18, w, 38, '#fff', BLUE if focus else G4, 8, 2 if focus else 1.5, 'box-shadow:0 0 0 3px rgba(29,78,216,.15);' if focus else '')
    if value: T(b, x + 12, y + 28, value, 13, 500, '#0F172A')
    else: bar(b, x + 12, y + 33, w * 0.4)
    if helper: T(b, x, y + 60, helper, 10.5, 500, G4)
def img(b, x, y, w, h, r=8):
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{w:g}px;height:{h:g}px;box-sizing:border-box;background:{G2};border:1.5px solid {G3};border-radius:{r}px;overflow:hidden"><svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 100" style="position:absolute;inset:0" stroke="{G4}" stroke-width="1.2" vector-effect="non-scaling-stroke"><path d="M0 0L100 100M100 0L0 100" vector-effect="non-scaling-stroke"/></svg></div>')
def chip(b, x, y, t, tone='gray', w=None):
    bg, fg = {'gray': (G2, '#334155'), 'green': ('#DCF5E1', '#15803D'), 'amber': ('#FFE2B0', '#92400E'), 'blue': ('#DCEEFB', '#1E5AA8'), 'rose': ('#FDE4E4', '#B42318')}[tone]
    w = w or 14 + 7 * len(t)
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{w}px;height:22px;border-radius:999px;background:{bg};color:{fg};font:700 11px/22px Inter,sans-serif;text-align:center;white-space:nowrap">{t}</div>')
    return w
def icon_dot(b, x, y, d=36, glyph=None, col=G4):
    b.raw(f'<div style="position:absolute;left:{x:g}px;top:{y:g}px;width:{d}px;height:{d}px;border-radius:999px;background:{G2};border:1.5px solid {G3}"></div>')
    if glyph: b.raw(icon_svg(glyph, x + d / 2 - 9, y + d / 2 - 9, 18, col))
def listitem(b, x, y, w, title, sub=None, trail=None, h=64, img_=True):
    R(b, x, y, w, h, '#fff', G3, 10)
    if img_: icon_dot(b, x + 12, y + (h - 38) / 2, 38)
    tx = x + (62 if img_ else 14)
    T(b, tx, y + (h / 2 - 16 if sub else h / 2 - 9), title, 13, 700, '#0F172A')
    if sub: T(b, tx, y + h / 2 + 2, sub, 11, 500, '#64748B')
    if trail: T(b, x + w - 14 - 7 * len(trail), y + h / 2 - 8, trail, 13, 700, '#0F172A')
def appbar(b, x, y, w, title, back=True):
    if back: b.raw(f'<svg width="22" height="22" viewBox="0 0 24 24" style="position:absolute;left:{x+14}px;top:{y+13}px;fill:none;stroke:#0F172A;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round"><path d="M15 5L8 12L15 19"/></svg>')
    T(b, x + (48 if back else 16), y + 14, title, 16, 800, '#0F172A')
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y+48}px;width:{w}px;border-top:1.5px solid {G2}"></div>')
def navtabs(b, x, y, w, items, active=0, icons=None):
    R(b, x, y, w, 60, '#fff', G3, 0, 1.5)
    n = len(items)
    for i, t in enumerate(items):
        cx = x + w * (i + .5) / n
        col = BLUE if i == active else G4
        if icons: b.raw(icon_svg(icons[i], cx - 10, y + 8, 20, col))
        T(b, cx - 40, y + 34, t, 10.5, 700, col, w=80, center=True)
def phone(b, x, y, w=300, h=620, label=None):
    b.raw(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;box-sizing:border-box;border:3px solid #0F172A;border-radius:38px;background:#F8FAFC;overflow:hidden"></div>')
    T(b, x + 30, y + 14, '10:24', 12, 700, '#0F172A')
    b.raw(f'<div style="position:absolute;left:{x+w/2-48}px;top:{y+h-18}px;width:96px;height:5px;border-radius:3px;background:#0F172A"></div>')
    if label: b.raw(f'<div style="position:absolute;left:{x}px;top:{y-38}px;width:{w}px;text-align:center;font-size:14px;font-weight:800">{label}</div>')
def callout(b, x, y, n):
    b.raw(f'<div style="position:absolute;left:{x-13}px;top:{y-13}px;width:26px;height:26px;border-radius:999px;background:#0F172A;color:#7DD3CB;font:800 12px/26px \'JetBrains Mono\',monospace;text-align:center;box-shadow:0 0 0 3px rgba(248,250,252,.9);z-index:5">{n}</div>')
def hotspot(b, x, y):
    b.raw(f'<div style="position:absolute;left:{x-6}px;top:{y-6}px;width:12px;height:12px;border-radius:999px;background:#D92D20;border:2px solid #fff;box-shadow:0 0 0 7px rgba(217,45,32,.25);z-index:4"></div>')
def notes(b, x, y, w, items, cols=1, gap=14, size=13):
    cw = (w - (cols - 1) * 24) / cols
    per = -(-len(items) // cols)
    for k, (n, title, text) in enumerate(items):
        c, r = divmod(k, per)
        xx, yy = x + c * (cw + 24), y + r * (66 + gap)
        callout(b, xx + 13, yy + 13, n)
        T(b, xx + 36, yy, title, size, 800, '#0F172A', w=cw - 40)
        T(b, xx + 36, yy + 20, text, size - 1.5, 500, '#475569', w=cw - 40, lh=17)
