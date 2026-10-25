# Architecture diagram builder on top of fclib.Board
import html
from fclib import *
from fslib import TONES
PW, PH = 196, 68      # plain component
CW, CH = 232, 96      # illustrated card
def comp(b, cx, cy, name, sub, icon, tone, style='plain', w=None, h=None):
    if style == 'detail':
        return b.card(cx, cy, name, sub, icon, TONES[tone], w=CW, h=CH, style='detail')
    bg, pill = TONES[tone]
    PW_, PH_ = w or PW, h or PH
    isz = 38 if PH_ >= 64 else 30
    b.raw(f'<div style="position:absolute;left:{cx-PW_/2:g}px;top:{cy-PH_/2:g}px;width:{PW_}px;height:{PH_}px;box-sizing:border-box;border:2px solid #0F172A;border-radius:12px;background:{bg}">'
          + bigicon(icon, isz, 10, (PH_ - isz) / 2 - 2)
          + f'<div style="position:absolute;left:{isz+18}px;right:6px;top:0;height:{PH_-4}px;display:flex;flex-direction:column;justify-content:center"><div style="font-size:13px;font-weight:800;line-height:16px;white-space:nowrap">{html.escape(name)}</div><div style="font-size:11px;line-height:15px;color:#475569;white-space:nowrap">{html.escape(sub)}</div></div></div>')
    return Node(cx, cy, PW_, PH_)
def zone(b, x0, y0, x1, y1, label, tone='gray'):
    bg = {'gray': 'rgba(100,116,139,0.07)', 'blue': 'rgba(29,78,216,0.06)', 'green': 'rgba(21,128,61,0.07)', 'amber': 'rgba(245,158,58,0.09)', 'violet': 'rgba(91,75,214,0.07)', 'teal': 'rgba(15,118,110,0.07)'}[tone]
    b.rect(x0, y0, x1 - x0, y1 - y0, bg, '#64748B', 16)
    b.pill(x0 + 18, y0 - 11, label, '#0F172A')
def save2(b, hh=None):
    r = b.save(hh)
    p = ROOT + b.name + '.dc.html'
    h = open(p, encoding='utf-8').read().replace('<title>Flowchart: ', '<title>Architecture: ')
    open(p, 'w', encoding='utf-8').write(h)
    return r
